from pathlib import Path
import json,numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from statsmodels.stats.multitest import multipletests
import statsmodels.api as sm
ROOT=Path(r'C:/Users/41240/OneDrive/文档/GitHub/practicum-project/Weikun')
def run(root=ROOT,output=Path('outputs/lag_analysis/results')):
 output=Path(output);output.mkdir(parents=True,exist_ok=True);(output/'figures').mkdir(exist_ok=True)
 ids=pd.read_csv(root/'fixed60_trajectory_outputs/fixed60_20261027/common_regions.csv',dtype={'zip':str}).zip.to_numpy();dates=pd.date_range('2020-03-01','2020-12-31')
 cols=['cases_today','cases_lag_1','cases_lag_7','cases_lag_14','nj_covid_pressure_7d','nj_covid_pressure_14d']
 f=pd.read_csv(root/'rolling_trajectory_outputs/inputs/nj_daily_features.csv.gz',usecols=['zip','date']+cols,dtype={'zip':str},parse_dates=['date']);f=f[f.zip.isin(ids)&f.date.isin(dates)]
 assert len(ids)==585 and not f.duplicated(['zip','date']).any()
 ar={c:f.pivot(index='zip',columns='date',values=c).reindex(index=ids,columns=dates).to_numpy(float) for c in cols};y=ar['cases_today'];assert np.isfinite(y).all()
 plt.rcParams.update({'font.family':'Arial','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
 rng=np.random.default_rng(20261104);rows=[];fig,ax=plt.subplots(2,3,figsize=(13,6.5))
 for j,month in enumerate([5,8,11]):
  ix=np.flatnonzero(dates.month==month)
  for i,lag in enumerate([1,7]):
   x=ar[f'cases_lag_{lag}'][:,ix];z=y[:,ix];xc=x-x.mean(1,keepdims=True);zc=z-z.mean(1,keepdims=True);num=(xc*zc).sum(0);den=(xc*xc).sum(0);slope=num.sum()/den.sum()
   B=2000;starts=rng.integers(0,len(ix),size=(B,int(np.ceil(len(ix)/7))));bi=((starts[:,:,None]+np.arange(7))%len(ix)).reshape(B,-1)[:,:len(ix)]
   # Resample whole daily cross-sections and recompute within-ZIP centering.
   bs=[]
   for k in bi:
    xx=x[:,k];zz=z[:,k];xx=xx-xx.mean(1,keepdims=True);zz=zz-zz.mean(1,keepdims=True);dd=(xx*xx).sum();bs.append((xx*zz).sum()/dd if dd else np.nan)
   lo,hi=np.nanquantile(bs,[.025,.975]);a=ax[i,j];a.scatter(x.ravel(),z.ravel(),s=3,alpha=.14,color=['#2563EB','#087F78'][i],rasterized=True);inter=z.mean()-slope*x.mean();line=np.linspace(0,x.max(),100);a.plot(line,inter+slope*line,color='#173654');a.set_title(f'{dates[ix[0]]:%b 2020}: lag {lag}\nWithin-ZIP slope {slope:.2f}');a.set_xlabel(f'Cases {lag} day(s) earlier');a.set_ylabel('Current daily cases');rows.append(dict(month=month,lag=lag,within_zip_slope=slope,ci95_low=lo,ci95_high=hi,observations=x.size))
 fig.tight_layout();fig.savefig(output/'figures/lag_relationships.png',dpi=220);plt.close(fig);pd.DataFrame(rows).to_csv(output/'monthly_lag_relationships.csv',index=False)
 variants={'L1':['cases_lag_1'],'L7':['cases_lag_7'],'L1_L7':['cases_lag_1','cases_lag_7'],'L1_L7_L14':['cases_lag_1','cases_lag_7','cases_lag_14']}
 origins=np.flatnonzero((dates>='2020-04-30')&(dates<='2020-12-28'));truth=np.stack([y[:,origins+h] for h in [1,2,3]],2);pred={v:np.full_like(truth,np.nan) for v in variants};audit=[];coefs=[];first=dates.get_loc('2020-04-29')
 for fit in np.unique(first+7*((origins-first)//7)):
  lo=fit-59;batch=np.flatnonzero((origins>=fit)&(origins<fit+7))
  for hh,h in enumerate([1,2,3]):
   train=np.arange(lo+14,fit-h+1);assert train[-1]+h<=fit and np.all(origins[batch]>fit-1)
   target=dates+pd.Timedelta(days=h)
   for k in range(2,8):ar[f'weekday_{k}']=np.broadcast_to((target.dayofweek==k-1).astype(float),y.shape)
   for k in range(2,13):ar[f'month_{k}']=np.broadcast_to((target.month==k).astype(float),y.shape)
   yt=y[:,train+h];ym=yt.mean(1);yc=yt-ym[:,None]
   for name,lags in variants.items():
    features=['cases_today']+lags+cols[-2:]+[f'weekday_{k}' for k in range(2,8)]+[f'month_{k}' for k in range(2,13)]
    xx=np.stack([ar[c][:,train] for c in features],2);pp=np.stack([ar[c][:,origins[batch]] for c in features],2);assert np.isfinite(xx).all() and np.isfinite(pp).all();xm=xx.mean(1);xc=xx-xm[:,None];norm=np.sqrt((xc*xc).mean((0,1)));scale=np.where(norm>1e-10,norm,1);zz=(xc/scale).reshape(-1,len(features));keep=[];q=[]
    for k in range(len(features)):
     if norm[k]<1e-10:continue
     v=zz[:,k].copy()
     for _ in range(2):
      for u in q:v-=u*(u@v)
     length=np.linalg.norm(v)
     if length<=1e-7*np.sqrt(len(v)):continue
     keep.append(k);q.append(v/length)
    b=np.linalg.lstsq(zz[:,keep],yc.ravel(),rcond=None)[0]/scale[keep];ph=np.einsum('ntp,p->nt',pp[:,:,keep],b)+(ym-xm[:,keep]@b)[:,None];pred[name][:,batch,hh]=np.maximum(ph,0)
    for k,coef in zip(keep,b):coefs.append(dict(variant=name,fit_date=str(dates[fit].date()),horizon=h,feature=features[k],coefficient=coef))
    audit.append(dict(variant=name,horizon=h,window_start=str(dates[lo].date()),fit_date=str(dates[fit].date()),latest_training_target=str(dates[train[-1]+h].date()),first_forecast_date=str(dates[origins[batch[0]]].date()),features=json.dumps(features)))
  print('Completed',dates[fit].date(),flush=True)
 metrics=[];daily={}
 for name,p in pred.items():
  assert np.isfinite(p).all();e=p-truth;daily[name]=np.abs(e).mean((0,2));direction=(np.sign(p[:,:,2]-p[:,:,0])==np.sign(truth[:,:,2]-truth[:,:,0])).mean();metrics.append(dict(variant=name,MAE=np.abs(e).mean(),RMSE=np.sqrt((e*e).mean()),bias=e.mean(),direction_accuracy=direction))
  np.savez_compressed(output/f'predictions_{name}.npz',predictions=p,actual_cases=truth,zip=ids,daily_forecast_dates=dates[origins].to_numpy())
 pd.DataFrame(metrics).to_csv(output/'validation_metrics.csv',index=False);pd.DataFrame(audit).to_csv(output/'training_audit.csv',index=False);pd.DataFrame(coefs).to_csv(output/'coefficients_by_fit.csv',index=False)
 tests=[]
 for name in list(variants)[1:]:
  delta=daily['L1']-daily[name];r=sm.OLS(delta,np.ones((len(delta),1))).fit(cov_type='HAC',cov_kwds={'maxlags':7});r28=sm.OLS(delta,np.ones((len(delta),1))).fit(cov_type='HAC',cov_kwds={'maxlags':28});starts=rng.integers(0,len(delta),size=(4000,int(np.ceil(len(delta)/14))));bi=((starts[:,:,None]+np.arange(14))%len(delta)).reshape(4000,-1)[:,:len(delta)];ci=np.quantile(delta[bi].mean(1),[.025,.975]);tests.append(dict(candidate=name,delta_MAE_L1_minus_candidate=delta.mean(),ci95_low=ci[0],ci95_high=ci[1],p_HAC7=r.pvalues[0],p_HAC28=r28.pvalues[0]))
 t=pd.DataFrame(tests);t['p_Holm_HAC7']=multipletests(t.p_HAC7,method='holm')[1];t['p_Holm_HAC28']=multipletests(t.p_HAC28,method='holm')[1];t.to_csv(output/'paired_comparisons.csv',index=False)
 m=pd.DataFrame(metrics);fig,axs=plt.subplots(1,3,figsize=(13,4))
 for a,col,title in zip(axs,['MAE','RMSE','direction_accuracy'],['Three-day path MAE','Three-day path RMSE','Endpoint direction accuracy']):
  v=m[col].to_numpy();v=v*100 if col=='direction_accuracy' else v;b=a.bar(m.variant,v,color=['#64748B','#88AEC1','#2563EB','#087F78']);a.bar_label(b,labels=[f'{x:.1f}%' if col=='direction_accuracy' else f'{x:.3f}' for x in v],padding=4);a.set_ylim(0,max(v)*1.22);a.set_title(title);a.grid(axis='y',alpha=.2);a.set_axisbelow(True)
 fig.tight_layout();fig.savefig(output/'figures/lag_prediction_comparison.png',dpi=220);plt.close(fig)
 protocol={'scope':'2020 exploratory development only','regions':585,'dates':243,'window':60,'refit':7,'warmup':14,'common_inputs':'cases_today, pressure7/14, target weekday/month, ZIP FE','excluded':'rolling means/std, local population rates, acceleration/jerk, sparse history, to avoid indirect lag information','variants':variants,'descriptive':'within-ZIP monthly slope with7day circular date-block bootstrap2000 pointwise CI. Whole ZIP cross sections resampled, few monthly blocks limits inference. Association not causation or GMM.','forecast_tests':'paired daily losses;HAC7/HAC28;Holm3contrasts separately;14day dateblockbootstrap4000 pointwiseCI','availability':'retrospective onset counts;real-time reporting availability unverified','main_models':'unchanged;diagnostic FE configurations only'}
 (output/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8');(output/'RESULTS.md').write_text('# Lag analysis\n\n'+pd.DataFrame(rows).to_markdown(index=False)+'\n\n'+m.to_markdown(index=False)+'\n\n'+t.to_markdown(index=False)+'\n\nPositive paired delta means candidate improves MAE over L1. Descriptive slopes and prediction gains answer different questions. No GMM validity tests or causal claims. Main models unchanged.\n',encoding='utf-8');return m
if __name__=='__main__':run()
