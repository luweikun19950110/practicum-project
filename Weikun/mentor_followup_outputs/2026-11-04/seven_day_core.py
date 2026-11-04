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

def run_seven(source,cohort,output):
 from scipy import sparse
 from sklearn.ensemble import RandomForestRegressor
 from xgboost import XGBRegressor
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 ids=pd.read_csv(cohort,dtype={'zip':str})['zip'].to_numpy(dtype='U5')
 dates=pd.date_range('2020-03-01','2020-12-31');origins=np.flatnonzero((dates>='2020-04-30')&(dates<='2020-12-24'))
 numeric=sum([v for k,v in GROUPS.items() if k not in ['month','weekday','sparse_history']],[])
 f=pd.read_csv(source,usecols=['zip','date','pressure_definition']+numeric,dtype={'zip':str},parse_dates=['date'])
 f=f.loc[f.zip.isin(ids)&f.date.isin(dates)]
 assert f.pressure_definition.eq('valid_population_nj_origins_renormalized_v2').all()
 assert not f.duplicated(['zip','date']).any() and len(ids)==585
 arrays={c:f.pivot(index='zip',columns='date',values=c).reindex(index=ids,columns=dates).to_numpy(float) for c in numeric}
 counts=arrays['cases_today'];actual=np.stack([counts[:,origins+h] for h in range(1,8)],axis=2)
 variants={'FULL':list(range(len(FEATURES)))}
 predictions={(m,g):np.full_like(actual,np.nan) for m in MODELS for g in variants}
 completed=set()
 for g in variants:
  for m in MODELS:
   path=output/f'predictions_{m.split()[0]}_7day.npz'
   if path.exists():
    with np.load(path,allow_pickle=False) as z:
     assert np.array_equal(z['actual_cases'],actual)
     predictions[m,g]=z['predictions'].copy();completed.add((m,g))
 for mm,gg in predictions:
  checkpoint=output/f'checkpoint_{mm.split()[0]}.npz'
  if checkpoint.exists() and (mm,gg) not in completed:
   with np.load(checkpoint) as z:predictions[mm,gg]=z['predictions'].copy()
 # Reuse identical previously fitted Days 1-3; only Days 4-7 require new fits.
 from threadpoolctl import threadpool_limits
 threadpool_limits(limits=1,user_api='blas')
 roots=Path(source).parents[2]
 baseline_files=['rolling_trajectory_outputs/rolling60_weekly_development_20261027/predictions.npz','xgboost_trajectory_outputs/xgb60_weekly_development_20261027/predictions.npz','random_forest_trajectory_outputs/rf60_weekly_development_20261027/predictions.npz']
 for mm,relative in zip(MODELS,baseline_files):
  with np.load(roots/relative) as zz:
   ix=pd.Index(zz['forecast_origins']).get_indexer(dates[origins]);assert (ix>=0).all()
   assert np.array_equal(zz['zip'],ids) and np.array_equal(zz['actual_cases'][:,ix,:],actual[:,:,:3])
   predictions[mm,'FULL'][:,:,:3]=np.maximum(zz['raw_predictions'][:,ix,:],0)
 first=dates.get_loc('2020-04-29');fits=np.unique(first+7*((origins-first)//7));logs=pd.read_csv(output/'training_audit.csv').to_dict('records') if (output/'training_audit.csv').exists() else []
 for fit in fits:
  lo=fit-59;batch=np.flatnonzero((origins>=fit)&(origins<fit+7));last=np.full(len(ids),-1)
  gap=np.full_like(counts,np.nan);never=np.full_like(counts,np.nan)
  for t in range(lo,int(origins[batch[-1]])+1):
   last=np.where(counts[:,t]>0,t,last);never[:,t]=last<0;gap[:,t]=np.where(last>=0,t-last,t-lo+1)
  arrays['days_since_last_observed_case_censored']=gap;arrays['no_previous_observed_case']=never
  for hh,h in enumerate(range(1,8)):
   train=np.arange(lo+14,fit-h+1);target=dates+pd.Timedelta(days=h)
   for k in range(2,13):arrays[f'target_month_{k}']=np.broadcast_to((target.month==k).astype(float),counts.shape)
   for k in range(2,8):arrays[f'target_weekday_{k}']=np.broadcast_to((target.dayofweek==k-1).astype(float),counts.shape)
   xt=np.stack([arrays[x][:,train] for x in FEATURES],axis=2);xp=np.stack([arrays[x][:,origins[batch]] for x in FEATURES],axis=2);yt=counts[:,train+h]
   assert np.isfinite(xt).all() and np.isfinite(xp).all()
   assert train[-1]+h<=fit and np.all(origins[batch]+h>fit) and lo>=0
   for g,cols in variants.items():
    xx,pp=xt[:,:,cols],xp[:,:,cols];features=[FEATURES[i] for i in cols]
    for m in MODELS:
     if (m,g) in completed or np.isfinite(predictions[m,g][:,batch,hh]).all():continue
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
  for (mm,gg),ppred in predictions.items():
   np.savez_compressed(output/f'checkpoint_{mm.split()[0]}.npz',predictions=ppred)
  pd.DataFrame(logs).to_csv(output/'training_audit.csv',index=False)
  print('Completed diagnostic refit',dates[fit].date(),flush=True)
 for (m,g),pred in predictions.items():
  assert np.isfinite(pred).all()
  if (m,g) not in completed:np.savez_compressed(output/f'predictions_{m.split()[0]}_7day.npz',predictions=pred,actual_cases=actual,zip=ids,daily_forecast_dates=dates[origins].to_numpy(),horizons=list(range(1,8)))
 if logs:pd.DataFrame(logs).to_csv(output/'training_audit.csv',index=False)
 (output/'protocol.json').write_text(json.dumps(dict(window=60,retrain_every=7,horizons=list(range(1,8)),features=FEATURES,scope='2020 exploratory validation only; retrospective onset availability assumed',daily_forecast_dates=['2020-04-30','2020-12-24'],label_boundary='latest training target <= fit date; target > forecast date'),indent=2))
 return predictions

