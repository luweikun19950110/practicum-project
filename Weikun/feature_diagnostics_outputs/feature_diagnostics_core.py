from pathlib import Path
import json,hashlib,time,os
import numpy as np,pandas as pd
GROUPS={
 'core_history':['cases_today','cases_lag_1','cases_lag_7','cases_lag_14'],
 'rolling_level':['cases_mean_7d','cases_mean_14d'],'volatility':['case_std_7d','case_std_14d'],
 'dynamics':['case_acceleration','case_jerk'],
 'local_rates':['case_rate_today_per_100k','case_rate_7d_per_100k','case_rate_14d_per_100k'],
 'sparse_history':['days_since_last_observed_case_censored','no_previous_observed_case'],
 'pressure':['nj_covid_pressure_7d','nj_covid_pressure_14d'],
 'month':[f'target_month_{k}' for k in range(2,13)],'weekday':[f'target_weekday_{k}' for k in range(2,8)]}
FEATURES=sum(GROUPS.values(),[])
FAMILIES={'local_case_history':sum([v for k,v in GROUPS.items() if k not in ['pressure','month','weekday']],[]),
 'commuting_pressure':GROUPS['pressure'],'calendar':GROUPS['month']+GROUPS['weekday']}
MODELS=['Dynamic Panel FE','XGBoost','Random Forest']

def run(source,cohort,baseline_paths,output):
 from scipy import sparse
 from sklearn.ensemble import RandomForestRegressor
 from xgboost import XGBRegressor
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 ids=pd.read_csv(cohort,dtype={'zip':str})['zip'].to_numpy(dtype='U5')
 dates=pd.date_range('2020-03-01','2020-12-31');origins=np.flatnonzero((dates>='2020-04-30')&(dates<='2020-12-28'))
 numeric=sum([v for k,v in GROUPS.items() if k not in ['month','weekday','sparse_history']],[])
 f=pd.read_csv(source,usecols=['zip','date','pressure_definition']+numeric,dtype={'zip':str},parse_dates=['date'])
 f=f.loc[f.zip.isin(ids)&f.date.isin(dates)]
 assert f.pressure_definition.eq('valid_population_nj_origins_renormalized_v2').all()
 assert not f.duplicated(['zip','date']).any() and len(ids)==585
 arrays={c:f.pivot(index='zip',columns='date',values=c).reindex(index=ids,columns=dates).to_numpy(float) for c in numeric}
 counts=arrays['cases_today'];actual=np.stack([counts[:,origins+h] for h in (1,2,3)],axis=2)
 baselines={}
 for name,path in baseline_paths.items():
  with np.load(path,allow_pickle=False) as z:
   assert np.array_equal(z['zip'],ids) and np.array_equal(z['forecast_origins'],dates[origins].to_numpy())
   assert np.array_equal(z['actual_cases'],actual)
   baselines[name]=np.maximum(z['raw_predictions'].copy(),0)
 variants={g:[i for i,x in enumerate(FEATURES) if x not in xs] for g,xs in FAMILIES.items()}
 predictions={(m,g):np.full_like(actual,np.nan) for m in MODELS for g in variants}
 completed=set()
 for g in variants:
  for m in MODELS:
   path=output/f'predictions_{m.split()[0]}_DROP_{g}.npz'
   if path.exists():
    with np.load(path,allow_pickle=False) as z:
     assert np.array_equal(z['actual_cases'],actual)
     predictions[m,g]=z['predictions'].copy();completed.add((m,g))
 first=dates.get_loc('2020-04-29');fits=np.unique(first+7*((origins-first)//7));logs=[]
 for fit in fits:
  lo=fit-59;batch=np.flatnonzero((origins>=fit)&(origins<fit+7));last=np.full(len(ids),-1)
  gap=np.full_like(counts,np.nan);never=np.full_like(counts,np.nan)
  for t in range(lo,int(origins[batch[-1]])+1):
   last=np.where(counts[:,t]>0,t,last);never[:,t]=last<0;gap[:,t]=np.where(last>=0,t-last,t-lo+1)
  arrays['days_since_last_observed_case_censored']=gap;arrays['no_previous_observed_case']=never
  for hh,h in enumerate((1,2,3)):
   train=np.arange(lo+14,fit-h+1);target=dates+pd.Timedelta(days=h)
   for k in range(2,13):arrays[f'target_month_{k}']=np.broadcast_to((target.month==k).astype(float),counts.shape)
   for k in range(2,8):arrays[f'target_weekday_{k}']=np.broadcast_to((target.dayofweek==k-1).astype(float),counts.shape)
   xt=np.stack([arrays[x][:,train] for x in FEATURES],axis=2);xp=np.stack([arrays[x][:,origins[batch]] for x in FEATURES],axis=2);yt=counts[:,train+h]
   assert np.isfinite(xt).all() and np.isfinite(xp).all()
   assert train[-1]+h<=fit and np.all(origins[batch]+h>fit) and lo>=0
   for g,cols in variants.items():
    xx,pp=xt[:,:,cols],xp[:,:,cols];features=[FEATURES[i] for i in cols]
    for m in MODELS:
     if (m,g) in completed:continue
     start=time.time()
     if m=='Dynamic Panel FE':
      xm=xx.mean(axis=1);ym=yt.mean(axis=1);xc=xx-xm[:,None];yc=yt-ym[:,None]
      norms=np.sqrt((xc*xc).mean(axis=(0,1)));scale=np.where(norms>1e-10,norms,1);z=(xc/scale).reshape(-1,len(cols));keep=[];q=[]
      for j in range(len(cols)):
       if norms[j]<1e-10:continue
       v=z[:,j].copy()
       for _ in range(2):
        for u in q:v-=u*(u@v)
       length=np.linalg.norm(v)
       if length<=1e-7*np.sqrt(len(v)):continue
       keep.append(j);q.append(v/length)
      b=np.linalg.lstsq(z[:,keep],yc.ravel(),rcond=None)[0]/scale[keep]
      yhat=np.einsum('ntp,p->nt',pp[:,:,keep],b)+(ym-xm[:,keep]@b)[:,None]
     elif m=='XGBoost':
      def design(v):
       d=pd.DataFrame(v.reshape(-1,len(cols)),columns=features);d['region_id']=pd.Categorical(np.repeat(ids,v.shape[1]),categories=ids);return d
      model=XGBRegressor(objective='reg:squarederror',tree_method='hist',n_estimators=200,max_depth=3,learning_rate=.05,min_child_weight=20,subsample=.8,colsample_bytree=1.,reg_lambda=5.,reg_alpha=0.,max_bin=128,enable_categorical=True,max_cat_to_onehot=4,max_cat_threshold=64,random_state=20261027,n_jobs=4)
      model.fit(design(xx),yt.ravel());yhat=model.predict(design(pp)).reshape(len(ids),len(batch))
     else:
      def design(v,fmt):
       rows=len(ids)*v.shape[1];identity=sparse.csr_matrix((np.ones(rows,dtype=np.float32),(np.arange(rows),np.repeat(np.arange(len(ids)),v.shape[1]))),shape=(rows,len(ids)))
       return sparse.hstack([sparse.csr_matrix(v.reshape(rows,len(cols)).astype(np.float32)),identity],format=fmt)
      model=RandomForestRegressor(n_estimators=200,max_depth=8,min_samples_leaf=20,max_features=1.,bootstrap=True,max_samples=.8,criterion='squared_error',random_state=20261027,n_jobs=4)
      model.fit(design(xx,'csc'),yt.ravel());yhat=model.predict(design(pp,'csr')).reshape(len(ids),len(batch))
     predictions[m,g][:,batch,hh]=np.maximum(yhat,0)
     logs.append(dict(model=m,drop_group=g,fit_date=str(dates[fit].date()),window_start=str(dates[lo].date()),latest_training_target=str(dates[train[-1]+h].date()),first_forecast_target=str(dates[origins[batch[0]]+h].date()),horizon=h,features=len(cols),seconds=time.time()-start))
  print('Completed diagnostic refit',dates[fit].date(),flush=True)
 for (m,g),pred in predictions.items():
  assert np.isfinite(pred).all()
  if (m,g) not in completed:np.savez_compressed(output/f'predictions_{m.split()[0]}_DROP_{g}.npz',predictions=pred,actual_cases=actual,zip=ids,daily_forecast_dates=dates[origins].to_numpy(),horizons=[1,2,3])
 if logs:pd.DataFrame(logs).to_csv(output/'training_audit.csv',index=False)
 summarize(actual,baselines,predictions,dates[origins],output)
 protocol=dict(scope='Exploratory 2020 validation diagnostics, not untouched testing or causal inference',daily_forecast_dates=['2020-04-30','2020-12-28'],zip_count=585,forecast_dates=243,window_days=60,retrain_every=7,features=FEATURES,families=FAMILIES,identity='Retained in every variant; FE/native category/one-hot by model',primary='Trajectory MAE over the same ZIP-date-horizon observations',delta='DROP MAE minus FULL MAE: positive means keeping the group helps',tests='9 two-sided intercept-only HAC tests of paired daily mean absolute-loss differences; Holm across all 9 primary tests; lags 7 primary and 28 sensitivity',intervals='Paired circular moving-date-block bootstrap, 14-day blocks, 4000 draws, pointwise percentile 95% CI. Entire ZIP cross-section and all horizons travel together.',dependence='Cross-ZIP dependence retained by daily aggregation. Temporal nonstationarity and few waves limit inference.',retrospective='Recorded onset dates; historical reporting availability unverified',pressure='Main full-feature models unchanged. DROP is a diagnostic only.',source_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest())
 (output/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
 return pd.read_csv(output/'group_ablation_summary.csv')

def summarize(actual,full,preds,dates,output):
 import statsmodels.api as sm
 from statsmodels.stats.multitest import multipletests
 rng=np.random.default_rng(20261102);n=len(dates);B=4000;block=14
 starts=rng.integers(0,n,size=(B,int(np.ceil(n/block))));idx=((starts[:,:,None]+np.arange(block))%n).reshape(B,-1)[:,:n]
 rows=[];daily=[];hrows=[];months=[]
 for (m,g),p in preds.items():
  ef=full[m]-actual;ed=p-actual;d=np.abs(ed).mean(axis=(0,2))-np.abs(ef).mean(axis=(0,2));delta=d.mean();boot=d[idx].mean(axis=1)
  tests=[]
  for lag in [7,28]:
   fit=sm.OLS(d,np.ones((n,1))).fit(cov_type='HAC',cov_kwds={'maxlags':lag,'use_correction':True});tests.append(float(fit.pvalues[0]))
  fm=np.abs(ef).mean();dm=np.abs(ed).mean()
  rows.append(dict(model=m,drop_group=g,FULL_MAE=fm,DROP_MAE=dm,delta_MAE_DROP_minus_FULL=delta,relative_increase_pct=100*delta/fm,ci95_low=np.quantile(boot,.025),ci95_high=np.quantile(boot,.975),p_HAC7_raw=tests[0],p_HAC28_raw=tests[1],FULL_RMSE=np.sqrt((ef**2).mean()),DROP_RMSE=np.sqrt((ed**2).mean()),regions=actual.shape[0],forecast_dates=n,paths=actual.shape[0]*n))
  for t,v in zip(dates,d):daily.append(dict(model=m,drop_group=g,daily_forecast_date=t,delta_MAE_DROP_minus_FULL=v))
  for h in range(3):hrows.append(dict(model=m,drop_group=g,horizon=h+1,FULL_MAE=np.abs(ef[:,:,h]).mean(),DROP_MAE=np.abs(ed[:,:,h]).mean(),delta_MAE_DROP_minus_FULL=(np.abs(ed[:,:,h])-np.abs(ef[:,:,h])).mean()))
  for mon in np.unique(dates.to_period('M')):
   mask=dates.to_period('M')==mon;months.append(dict(model=m,drop_group=g,month=str(mon),delta_MAE_DROP_minus_FULL=d[mask].mean(),dates=int(mask.sum())))
 r=pd.DataFrame(rows);r['p_Holm']=multipletests(r.p_HAC7_raw,method='holm')[1];r['p_HAC28_Holm_sensitivity']=multipletests(r.p_HAC28_raw,method='holm')[1]
 r.to_csv(output/'group_ablation_summary.csv',index=False);pd.DataFrame(daily).to_csv(output/'paired_daily_loss_differences.csv',index=False);pd.DataFrame(hrows).to_csv(output/'group_ablation_by_horizon.csv',index=False);pd.DataFrame(months).to_csv(output/'group_ablation_by_month.csv',index=False)

