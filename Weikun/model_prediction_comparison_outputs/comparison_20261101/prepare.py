from pathlib import Path
import numpy as np,pandas as pd,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path('C:/Users/41240/OneDrive/文档/GitHub/practicum-project/Weikun');out=Path('outputs/model_comparison_slides');(out/'figures').mkdir(exist_ok=True)
models=['Dynamic Panel FE','XGBoost','Random Forest'];colors=['#64748B','#2563EB','#087F78']
files=[root/'rolling_trajectory_outputs/rolling60_weekly_development_20261027/predictions.npz',root/'xgboost_trajectory_outputs/xgb60_weekly_development_20261027/predictions.npz',root/'random_forest_trajectory_outputs/rf60_weekly_development_20261027/predictions.npz']
arrays=[np.load(p,allow_pickle=False) for p in files];ref=arrays[0]
for a in arrays:
 for k in ['zip','forecast_origins','actual_cases','horizons']:assert np.array_equal(a[k],ref[k])
dates=pd.to_datetime(ref['forecast_origins']);months=dates.to_period('M').astype(str);rows=[];monthly=[];overall=[]
for m,a in zip(models,arrays):
 error=np.maximum(a['raw_predictions'],0)-a['actual_cases'];ae=np.abs(error)
 for h in range(3):rows.append(dict(model=m,horizon=h+1,MAE=float(ae[:,:,h].mean()),RMSE=float(np.sqrt((error[:,:,h]**2).mean())),bias=float(error[:,:,h].mean())))
 overall.append(dict(model=m,trajectory_MAE=float(ae.mean()),trajectory_RMSE=float(np.sqrt((error**2).mean())),bias=float(error.mean())))
 for month in sorted(set(months)):
  mask=months==month;monthly.append(dict(model=m,month=month,origins=int(mask.sum()),trajectory_MAE=float(ae[:,mask].mean()),actual_mean=float(a['actual_cases'][:,mask].mean())))
r=pd.DataFrame(rows);o=pd.DataFrame(overall);q=pd.DataFrame(monthly);base=o.trajectory_MAE.iloc[0];o['improvement_percent']=100*(base-o.trajectory_MAE)/base
pivot=q.pivot(index='month',columns='model',values='trajectory_MAE');full=pivot.loc['2020-05':];wins={m:int((full[m]<full[models[0]]).sum()) for m in models[1:]}
r.to_csv(out/'metrics_by_horizon.csv',index=False);o.to_csv(out/'overall_trajectory_metrics.csv',index=False);q.to_csv(out/'monthly_trajectory_metrics.csv',index=False)
plt.rcParams.update({'font.family':'Arial','font.size':14,'axes.spines.top':False,'axes.spines.right':False})
f,ax=plt.subplots(figsize=(7.2,4.2));x=np.arange(3);w=.23
for j,(m,c) in enumerate(zip(models,colors)):
 vals=r[r.model.eq(m)].MAE.to_numpy();bars=ax.bar(x+(j-1)*w,vals,width=w,color=c,label=m)
 ax.bar_label(bars,fmt='%.3f',padding=3,fontsize=11)
ax.set(xticks=x,xticklabels=['1 day','2 days','3 days'],xlabel='Forecast horizon',ylabel='MAE (cases)',ylim=(0,r.MAE.max()*1.25));ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True);ax.legend(fontsize=10,ncol=3,loc='upper center',bbox_to_anchor=(.5,1.20),frameon=False);f.tight_layout();f.savefig(out/'figures/01_horizon_mae.png',dpi=200,bbox_inches='tight');plt.close(f)
f,ax=plt.subplots(figsize=(4.9,4.2));bars=ax.bar(['Dynamic\nPanel','XGBoost','Random\nForest'],o.trajectory_MAE,color=colors)
ax.bar_label(bars,fmt='%.3f',padding=4,fontsize=15);ax.set(ylabel='Three-day trajectory MAE (cases)',ylim=(0,o.trajectory_MAE.max()*1.24));ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True);f.tight_layout();f.savefig(out/'figures/02_trajectory_mae.png',dpi=200,bbox_inches='tight');plt.close(f)
f,ax=plt.subplots(figsize=(9,4.6));displaymonths=list(full.index)
for m,c in zip(models,colors):ax.plot(np.arange(len(displaymonths)),full[m],'o-',lw=2.2,color=c,label=m)
ax.set(xticks=np.arange(len(displaymonths)),xticklabels=[pd.Period(m).strftime('%b') for m in displaymonths],xlabel='Forecast-origin month in 2020',ylabel='Three-day trajectory MAE (cases)',ylim=(0,full.max().max()*1.12));ax.grid(alpha=.2);ax.legend(fontsize=12);f.tight_layout();f.savefig(out/'figures/03_monthly_trajectory_mae.png',dpi=200,bbox_inches='tight');plt.close(f)
summary=dict(regions=len(ref['zip']),forecast_origins=len(dates),start=str(dates.min().date()),end=str(dates.max().date()),months_compared=8,month_basis='forecast origin, May-Dec; April30 partial month excluded from stability plot only',wins_vs_dynamic_panel=wins,overall=o.to_dict('records'),monthly=full.reset_index().to_dict('records'),same_targets_verified=True,prediction='raw predictions clipped at0, equal ZIP-origin-horizon weights',trajectory_MAE='mean of absolute errors across3horizons perZIP-origin, then mean overZIP-origins',interpretation='2020 development/rolling validation, not independent final test. Monthly counts are descriptive, no significance claim. Different epidemic activity affects absolute error levels.')
(out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
