from pathlib import Path
import json,itertools
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

NAMES=['Dynamic Panel FE','XGBoost','Random Forest']
PATHS=['rolling_trajectory_outputs/rolling60_weekly_development_20261027/predictions.npz','xgboost_trajectory_outputs/xgb60_weekly_development_20261027/predictions.npz','random_forest_trajectory_outputs/rf60_weekly_development_20261027/predictions.npz']
def load_models(root):
 data=[]
 for p in PATHS:
  with np.load(Path(root)/p,allow_pickle=False) as z:data.append({k:z[k].copy() for k in z.files})
 for d in data[1:]:
  for k in ['zip','forecast_origins','actual_cases','horizons']:assert np.array_equal(d[k],data[0][k]),k
 return data

def complementarity(root,output):
 from warning_helpers import warning_events
 root=Path(root);output=Path(output)/'model_complementarity';output.mkdir(parents=True,exist_ok=True)
 data=load_models(root);truth=data[0]['actual_cases'];dates=data[0]['forecast_origins'];ids=data[0]['zip']
 actual=np.sign(truth[:,:,2]-truth[:,:,0]);pred=np.stack([np.sign(np.maximum(d['raw_predictions'],0)[:,:,2]-np.maximum(d['raw_predictions'],0)[:,:,0]) for d in data])
 correct=pred==actual;rows=[];patterns=[]
 for cls,label in [(-1,'Declining'),(0,'Exact endpoint-flat'),(1,'Rising')]:
  mask=actual==cls;v=correct[:,mask];counts=v.sum(axis=0)
  rows.append(dict(actual_class=label,paths=int(mask.sum()),DP_recall=v[0].mean(),XGB_recall=v[1].mean(),RF_recall=v[2].mean(),at_least_one_correct=(counts>=1).mean(),at_least_two_correct=(counts>=2).mean(),all_three_correct=(counts==3).mean(),all_three_wrong=(counts==0).mean()))
  for bits in itertools.product([False,True],repeat=3):patterns.append(dict(actual_class=label,DP_correct=bits[0],XGB_correct=bits[1],RF_correct=bits[2],paths=int((v==np.array(bits)[:,None]).all(axis=0).sum())))
 pd.DataFrame(rows).to_csv(output/'direction_overlap_by_actual_class.csv',index=False);pd.DataFrame(patterns).to_csv(output/'direction_correctness_patterns.csv',index=False)
 # Union of correct outcomes is descriptive coverage, NOT a deployable selector.
 rules=[]
 for cls,label in [(-1,'Declining'),(1,'Rising')]:
  for votes in [1,2,3]:
   alert=(pred==cls).sum(axis=0)>=votes;positive=actual==cls
   rules.append(dict(direction=label,required_votes=votes,alerts=int(alert.sum()),recall=(alert&positive).sum()/positive.sum(),precision=(alert&positive).sum()/alert.sum() if alert.any() else np.nan))
 pd.DataFrame(rules).to_csv(output/'direction_vote_rules.csv',index=False)
 warning=root/'outbreak_task_outputs'/'case_surge_v1_20261101'
 if not warning.exists():
  matches=list(root.rglob('case_surge_v1_20261101/warning_metrics.csv'));assert matches,'Locate Notebook 27 warning outputs';warning=matches[0].parent
 risk=[]
 for m in NAMES:
  f=pd.read_csv(warning/(m.lower().replace(' ','_')+'_risk_scores.csv.gz'),dtype={'zip':str})
  f=f.sort_values(['zip','forecast_origin']).reset_index(drop=True);risk.append(f)
 for f in risk[1:]:
  for k in ['zip','forecast_origin','eligible','event_in_next_3_days']:assert f[k].equals(risk[0][k]),k
 wd=np.sort(risk[0].forecast_origin.unique()).astype('datetime64[D]');n=len(wd)
 scores=np.stack([f.risk_score.to_numpy().reshape(len(ids),n) for f in risk]);eligible=risk[0].eligible.to_numpy().reshape(len(ids),n)
 labels=pd.read_csv(warning/'daily_event_labels_2020.csv.gz',dtype={'zip':str},parse_dates=['date'])
 pivot=labels.pivot(index='zip',columns='date',values='onset').reindex(ids);calendar=pivot.columns.to_numpy().astype('datetime64[D]');onsets=pivot.to_numpy(bool)
 thresholds=pd.read_csv(warning/'warning_metrics.csv').query("phase=='calibration'").set_index('model').threshold.reindex(NAMES).to_numpy()
 votes=scores>thresholds[:,None,None];mask=wd>=np.datetime64('2020-09-01');metrics=[];evectors=[]
 for m,v in zip(NAMES,votes):
  met,alarms,ev=warning_events(v[:,mask].astype(float),eligible[:,mask],onsets,wd[mask],calendar,.5)
  metrics.append(dict(rule=m,**met));evectors.append(ev.set_index(['region_index','event_date']).detected)
  alarms.to_csv(output/(m.split()[0]+'_warning_episodes.csv'),index=False)
 event=pd.concat(evectors,axis=1,keys=NAMES);assert event.notna().all().all();event['models_detecting']=event[NAMES].sum(axis=1);event.reset_index().to_csv(output/'event_detection_overlap.csv',index=False)
 overlap=event.models_detecting.value_counts().reindex(range(4),fill_value=0).rename_axis('models_detecting').reset_index(name='events');overlap['share']=overlap.events/len(event);overlap.to_csv(output/'event_overlap_counts.csv',index=False)
 pairs=[]
 for left,right in itertools.combinations(NAMES,2):
  x,y=event[left],event[right];pairs.append(dict(model_A=left,model_B=right,both_detect=int((x&y).sum()),only_A=int((x&~y).sum()),only_B=int((~x&y).sum()),both_miss=int((~x&~y).sum()),jaccard=(x&y).sum()/(x|y).sum()))
 pd.DataFrame(pairs).to_csv(output/'event_pair_overlap.csv',index=False)
 for k in [1,2,3]:
  met,alarms,ev=warning_events((votes.sum(axis=0)>=k)[:,mask].astype(float),eligible[:,mask],onsets,wd[mask],calendar,.5)
  metrics.append(dict(rule=f'At least {k} model votes',**met));alarms.to_csv(output/f'vote{k}_warning_episodes.csv',index=False)
 pd.DataFrame(metrics).to_csv(output/'warning_vote_metrics.csv',index=False)
 fig,ax=plt.subplots(figsize=(10,4));r=pd.DataFrame(rows).set_index('actual_class');r[['DP_recall','XGB_recall','RF_recall','at_least_one_correct']].plot.bar(ax=ax);ax.set(ylabel='Fraction of actual paths',ylim=(0,1),title='Do models recognize different paths?');ax.tick_params(axis='x',rotation=0);fig.tight_layout();fig.savefig(output/'direction_overlap.png',dpi=200);plt.close(fig)
 fig,axs=plt.subplots(1,2,figsize=(12,4));r=pd.DataFrame(metrics)
 from matplotlib.ticker import PercentFormatter
 for ax,key,title in zip(axs,['event_recall','warning_precision'],['Detected events / eligible events','Correct warnings / issued warnings']):
  bars=ax.bar(np.arange(len(r)),r[key],color=['#64748b','#2563eb','#087f78']*2);ax.set(xticks=np.arange(len(r)),xticklabels=['DP','XGBoost','RF','1+ votes','2+ votes','3 votes'],ylim=(0,1),title=title);ax.yaxis.set_major_formatter(PercentFormatter(1));ax.bar_label(bars,labels=[f'{100*x:.1f}%' for x in r[key]],padding=3)
 fig.tight_layout();fig.savefig(output/'warning_vote_comparison.png',dpi=200);plt.close(fig)
 text='# Three-model complementarity\n\n'+pd.DataFrame(rows).to_markdown(index=False)+'\n\n'+r.to_markdown(index=False)+'\n\nEvent overlap among original individual warning systems:\n\n'+overlap.to_markdown(index=False)+'\n\nUnion of correct paths is retrospective coverage, not attainable accuracy without knowing which model is correct. Voting rules are prospective functions of model outputs only. Votes are formed on the same ZIP-date BEFORE applying one shared cooldown and event matching, rather than unioning already-matched warnings. Individual thresholds are retained from original calibration; no new assessment tuning. This is exploratory 2020 analysis. Model votes are correlated; three votes do not constitute three independent pieces of evidence. The min/max model envelope is model disagreement, not a confidence or prediction interval.\n'
 (output/'RESULTS.md').write_text(text,encoding='utf-8');return r

def seven_summary(root,output):
 root=Path(root);folder=Path(output)/'seven_day_trajectory';data=load_models(root);rows=[];diag=[];saved={}
 for name,d in zip(NAMES,data):
  with np.load(folder/f'predictions_{name.split()[0]}_7day.npz') as z:p=z['predictions'];a=z['actual_cases'];dates=z['daily_forecast_dates']
  ix=pd.Index(d['forecast_origins']).get_indexer(dates);assert (ix>=0).all();assert np.array_equal(a[:,:,:3],d['actual_cases'][:,ix,:])
  old=np.maximum(d['raw_predictions'][:,ix,:],0);assert np.allclose(old,p[:,:,:3],rtol=1e-5,atol=1e-5),'Days 1-3 must reproduce existing models'
  saved[name]=p
  for h in range(7):rows.append(dict(model=name,horizon=h+1,MAE=np.abs(p[:,:,h]-a[:,:,h]).mean(),RMSE=np.sqrt(((p[:,:,h]-a[:,:,h])**2).mean()),bias=(p[:,:,h]-a[:,:,h]).mean(),forecast_dates=len(dates),regions=len(p)))
  for H in [3,7]:
   aa=a[:,:,:H];pp=p[:,:,:H];direction=np.sign(aa[:,:,-1]-aa[:,:,0]);pred=np.sign(pp[:,:,-1]-pp[:,:,0]);rec=[(pred[direction==c]==c).mean() for c in [-1,0,1]]
   diag.append(dict(model=name,path_days=H,path_MAE=np.abs(pp-aa).mean(),path_RMSE=np.sqrt(((pp-aa)**2).mean()),endpoint_direction_accuracy=(pred==direction).mean(),always_flat_reference=(direction==0).mean(),balanced_direction_accuracy=np.mean(rec),decline_recall=rec[0],flat_recall=rec[1],rise_recall=rec[2],strict_shape_accuracy=(np.sign(np.diff(pp,axis=2))==np.sign(np.diff(aa,axis=2))).all(axis=2).mean(),mean_daily_change_MAE=np.abs(np.diff(pp,axis=2)-np.diff(aa,axis=2)).mean(),endpoint_change_MAE=np.abs((pp[:,:,-1]-pp[:,:,0])-(aa[:,:,-1]-aa[:,:,0])).mean()))
 r=pd.DataFrame(rows);r.to_csv(folder/'horizon_metrics.csv',index=False);t=pd.DataFrame(diag);t.to_csv(folder/'matched_3_vs_7_day_paths.csv',index=False)
 fig,ax=plt.subplots(figsize=(9,4))
 for name,g in r.groupby('model',sort=False):ax.plot(g.horizon,g.MAE,'o-',label=name)
 ax.set(xlabel='Days ahead',ylabel='ZIP-level MAE (cases)',title='Same forecast dates: error by forecast horizon');ax.legend();fig.tight_layout();fig.savefig(folder/'horizon_MAE.png',dpi=200);plt.close(fig)
 fig,axs=plt.subplots(1,2,figsize=(11,4))
 for name,g in t.groupby('model',sort=False):
  axs[0].plot(g.path_days,g.endpoint_direction_accuracy,'o-',label=name);axs[1].plot(g.path_days,g.balanced_direction_accuracy,'o-',label=name)
 for ax,title in zip(axs,['Endpoint direction accuracy','Mean recall across 3 direction classes']):ax.set(title=title,xlabel='Path length (days)',xticks=[3,7],ylim=(0,1));ax.legend()
 fig.tight_layout();fig.savefig(folder/'direction_3_vs_7.png',dpi=200);plt.close(fig)
 fig,axs=plt.subplots(2,2,figsize=(11,7))
 for ax,day in zip(axs.ravel(),['2020-05-01','2020-07-01','2020-09-01','2020-11-01']):
  j=pd.Index(dates).get_loc(pd.Timestamp(day));ax.plot(range(1,8),a[:,j,:].sum(axis=0),'k-o',label='Actual')
  for name,p in saved.items():ax.plot(range(1,8),p[:,j,:].sum(axis=0),'o-',label=name)
  ax.set(title=f'Daily forecast date: {day}',xlabel='Days ahead',ylabel='Cases summed across 585 ZIPs',xticks=range(1,8));ax.legend(fontsize=8)
 fig.suptitle('Seven-day paths on four fixed calendar dates (aggregate illustration)');fig.tight_layout();fig.savefig(folder/'seven_day_path_examples.png',dpi=200);plt.close(fig)
 audits=[]
 for name,relative in zip(NAMES,PATHS):
  timing=pd.read_csv((root/relative).parent/'training_timing.csv');timing['model']=name;timing['prediction_source']='reused original Day 1-3 fits';audits.append(timing)
 audit=pd.concat(audits,ignore_index=True);audit.to_csv(folder/'reused_day1_3_training_audit.csv',index=False)
 new=pd.read_csv(folder/'training_audit.csv');assert (pd.to_datetime(new.latest_training_target)<=pd.to_datetime(new.fit_date)).all()
 assert (pd.to_datetime(audit.latest_training_target)<=pd.to_datetime(audit.fit_date)).all()
 (folder/'verification.json').write_text(json.dumps(dict(regions=int(len(a)),forecast_dates=len(dates),paths=int(len(a)*len(dates)),new_horizon_fits=int(len(new.query('horizon>=4'))),reused_horizon_fits=len(audit),first_three_horizons_match_original=True,all_training_labels_matured=True,targets_end_by='2020-12-31',horizon_definition='7 separate daily counts, not 7-day moving average'),indent=2))
 (folder/'RESULTS.md').write_text('# Seven-day supplementary trajectory analysis\n\n'+t.to_markdown(index=False)+'\n\n'+r.to_markdown(index=False)+'\n\nSame 585 ZIPs and Apr 30–Dec 24 daily forecast dates for both path lengths. 60 calendar days with 14-day warmup, weekly refits. All 34 candidates plus ZIP identity. Each horizon has its own direct model; only matured labels enter training. Days 1–3 reproduce prior predictions. Seven-day endpoint direction and six-step shape are different tasks from three-day direction and two-step shape: higher scores do not by themselves prove a better model. Read class recall and flat prevalence alongside accuracy. No outbreak labels, warning thresholds or lead-time results are changed here. 2020 exploratory historical replay; not untouched testing.\n',encoding='utf-8');return t
