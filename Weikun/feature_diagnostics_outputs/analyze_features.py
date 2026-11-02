from pathlib import Path
import pandas as pd,numpy as np,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent;OUT=ROOT/('results' if (ROOT.parent/'nj_random_forest_trajectory').exists() else 'validation2020_20261102');OUT.mkdir(exist_ok=True);FIG=OUT/'figures';FIG.mkdir(exist_ok=True)
BASE=ROOT.parent
DPDIR=BASE/('nj_rolling_trajectory/results/rolling60_weekly_development_20261027' if (BASE/'nj_rolling_trajectory').exists() else 'rolling_trajectory_outputs/rolling60_weekly_development_20261027')
XDIR=BASE/('nj_xgboost_trajectory/results/xgb60_weekly_development_20261027' if (BASE/'nj_xgboost_trajectory').exists() else 'xgboost_trajectory_outputs/xgb60_weekly_development_20261027')
RDIR=BASE/('nj_random_forest_trajectory/results/rf60_weekly_development_20261027' if (BASE/'nj_random_forest_trajectory').exists() else 'random_forest_trajectory_outputs/rf60_weekly_development_20261027')
models=['Dynamic Panel FE','XGBoost','Random Forest'];colors=['#64748B','#2563EB','#087F78']
plt.rcParams.update({'font.family':'Arial','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
feat=pd.read_csv(RDIR/'candidate_features.csv')
group=dict(zip(feat.feature,feat.group));group['region_id']='ZIP identity'
# Include unused features as zero within each of the 105 weekly fits.
imp=[]
for model,folder,file,val in [('XGBoost',XDIR,'training_split_gain.csv','training_split_gain'),('Random Forest',RDIR,'training_impurity_importance.csv','training_impurity_importance')]:
 d=pd.read_csv(folder/file,parse_dates=['fit_date']);d['feature']=d.feature.where(~d.feature.str.startswith('region_'),'region_id') if model=='Random Forest' else d.feature
 d=d.groupby(['fit_date','horizon','feature'],as_index=False)[val].sum()
 d=d.pivot(index=['fit_date','horizon'],columns='feature',values=val).reindex(columns=feat.feature.tolist()+['region_id']).fillna(0)
 assert len(d)==105
 d=d.div(d.sum(axis=1),axis=0);d=d.stack(future_stack=True).rename('normalized_training_importance').reset_index();d['model']=model;d['feature_group']=d.feature.map(group);d['month']=d.fit_date.dt.to_period('M').astype(str);imp.append(d)
d=pd.concat(imp,ignore_index=True);d.to_csv(OUT/'training_importance_by_fit.csv',index=False)
summary=d.groupby(['model','feature','feature_group']).normalized_training_importance.agg(mean='mean',median='median',std='std',nonzero_share=lambda x:(x>0).mean()).reset_index();summary['rank']=summary.groupby('model')['mean'].rank(ascending=False,method='min');summary.to_csv(OUT/'training_importance_summary.csv',index=False)
d.groupby(['model','horizon','feature']).normalized_training_importance.mean().reset_index().to_csv(OUT/'training_importance_by_horizon.csv',index=False)
d.groupby(['model','month','feature']).normalized_training_importance.mean().reset_index().to_csv(OUT/'training_importance_by_month.csv',index=False)
f,axes=plt.subplots(1,2,figsize=(13,6))
for ax,m,c in zip(axes,models[1:],colors[1:]):
 top=summary[summary.model==m].nsmallest(10,'rank').sort_values('mean');names=top.feature.replace({'cases_mean_7d':'7-day mean cases','cases_mean_14d':'14-day mean cases','cases_today':'Cases today','region_id':'ZIP identity','cases_lag_1':'Cases 1 day ago','days_since_last_observed_case_censored':'Days since last case','nj_covid_pressure_14d':'14-day commuting pressure','nj_covid_pressure_7d':'7-day commuting pressure','case_rate_today_per_100k':'Current case rate / 100k','case_std_7d':'7-day case variability','case_std_14d':'14-day case variability','case_rate_14d_per_100k':'14-day case rate / 100k','case_rate_7d_per_100k':'7-day case rate / 100k'});ax.barh(names,top['mean'],color=c);ax.set(title=m,xlabel='Mean within-fit normalized training importance');ax.grid(axis='x',alpha=.2)
f.suptitle('Which features did the fitted trees use?\nTraining split diagnostics; values are not comparable between model types',fontsize=14);f.tight_layout();f.savefig(FIG/'01_tree_training_importance.png',dpi=220);plt.close(f)
# Coefficient stability: descriptive, never equate repeated correlated fits with independent samples.
c=pd.read_csv(DPDIR/'coefficients.csv',parse_dates=['fit_date'])
rows=[]
for h in [1,2,3]:
 for feature in feat.feature:
  v=c[(c.horizon==h)&(c.feature==feature)].coefficient
  rows.append(dict(feature=feature,horizon=h,estimable_fits=len(v),total_fits=35,median_coefficient=v.median(),p10_coefficient=v.quantile(.1),p90_coefficient=v.quantile(.9),positive_share_of_estimable_fits=(v>0).mean() if len(v) else np.nan,negative_share_of_estimable_fits=(v<0).mean() if len(v) else np.nan))
pd.DataFrame(rows).to_csv(OUT/'dp_coefficient_stability.csv',index=False)
c.to_csv(OUT/'dp_coefficients_by_fit.csv',index=False)
sel=['cases_today','cases_lag_1','cases_mean_7d','nj_covid_pressure_7d','nj_covid_pressure_14d','case_acceleration']
f,axes=plt.subplots(2,3,figsize=(14,6),sharex=True)
for ax,feature in zip(axes.ravel(),sel):
 for h,col in zip([1,2,3],colors):
  q=c[(c.feature==feature)&(c.horizon==h)];ax.plot(q.fit_date,q.coefficient,label=f'{h}-day ahead',color=col)
 ax.axhline(0,color='gray',ls='--',lw=.7);ax.set_title(feature,fontsize=10);ax.tick_params(axis='x',rotation=30);ax.grid(alpha=.15)
axes[0,0].legend(fontsize=8);f.suptitle('Dynamic Panel coefficient stability across weekly refits\nCoefficients describe conditional associations; omitted terms may be unidentifiable',fontsize=13);f.tight_layout();f.savefig(FIG/'02_dp_coefficient_stability.png',dpi=220);plt.close(f)
if (OUT/'group_ablation_summary.csv').exists():
 a=pd.read_csv(OUT/'group_ablation_summary.csv');families=['local_case_history','commuting_pressure','calendar']
 trajectory=[]
 for model,folder in zip(models,[DPDIR,XDIR,RDIR]):
  with np.load(folder/'predictions.npz',allow_pickle=False) as z: actual=z['actual_cases'];full=np.maximum(z['raw_predictions'],0)
  for g in families:
   with np.load(OUT/f'predictions_{model.split()[0]}_DROP_{g}.npz',allow_pickle=False) as z: drop=z['predictions']
   for variant,pred in [('FULL',full),('DROP',drop)]:
    direction=np.sign(pred[...,2]-pred[...,0]);truth=np.sign(actual[...,2]-actual[...,0]);change=np.diff(pred,axis=2)-np.diff(actual,axis=2)
    recalls=[(direction[truth==c]==c).mean() for c in [-1,0,1]]
    trajectory.append(dict(model=model,drop_group=g,variant=variant,direction_agreement=(direction==truth).mean(),decline_recall=recalls[0],flat_recall=recalls[1],rise_recall=recalls[2],balanced_direction_accuracy=np.mean(recalls),shape_agreement=(np.sign(np.diff(pred,axis=2))==np.sign(np.diff(actual,axis=2))).all(axis=2).mean(),change_MAE=np.abs(change).mean(),acceleration_MAE=np.abs(np.diff(pred,n=2,axis=2)-np.diff(actual,n=2,axis=2)).mean()))
 pd.DataFrame(trajectory).to_csv(OUT/'group_ablation_trajectory_diagnostics.csv',index=False)

 f,axes=plt.subplots(1,3,figsize=(14,4.8))
 for ax,g in zip(axes,families):
  q=a[a.drop_group==g].set_index('model').loc[models];x=np.arange(3);v=q.delta_MAE_DROP_minus_FULL.to_numpy();lo=q.ci95_low.to_numpy();hi=q.ci95_high.to_numpy()
  ax.errorbar(x,v,yerr=[np.maximum(v-lo,0),np.maximum(hi-v,0)],fmt='none',ecolor='#173654',capsize=5,zorder=3);ax.scatter(x,v,c=colors,s=65,zorder=4);ax.axhline(0,color='black',lw=.8,ls='--');ax.set(xticks=x,xticklabels=['Dynamic\nPanel','XGBoost','Random\nForest'],title=g.replace('_',' ').title(),ylabel='MAE after removal minus FULL MAE');ax.grid(axis='y',alpha=.2)
 f.suptitle('Does each feature group add predictive information?\nPositive = keeping the group helps; pointwise 95% date-block bootstrap intervals',fontsize=13);f.tight_layout();f.savefig(FIG/'03_group_ablation_intervals.png',dpi=220);plt.close(f)
 month=pd.read_csv(OUT/'group_ablation_by_month.csv');f,axes=plt.subplots(1,3,figsize=(14,4),sharex=True)
 for ax,g in zip(axes,families):
  for m,col in zip(models,colors):
   q=month[(month.drop_group==g)&(month.model==m)];ax.plot(q.month,q.delta_MAE_DROP_minus_FULL,'o-',label=m,color=col)
  ax.axhline(0,color='gray',ls='--');ax.set_title(g.replace('_',' ').title());ax.tick_params(axis='x',rotation=60);ax.grid(alpha=.15)
 axes[0].set_ylabel('MAE after removal minus FULL MAE');axes[0].legend(fontsize=8);f.suptitle('Feature-group contribution changes over time (2020 validation)',fontsize=14);f.tight_layout();f.savefig(FIG/'04_group_contribution_by_month.png',dpi=220);plt.close(f)
 lines=['# NJ feature diagnostics: 2020 validation','', 'Main full-feature models remain unchanged. Positive delta means removing the group increases error, so keeping it helps. All comparisons share 585 ZIPs, 243 daily forecast dates, three horizons, 60-day windows and weekly refits.','',a[['model','drop_group','FULL_MAE','DROP_MAE','delta_MAE_DROP_minus_FULL','relative_increase_pct','ci95_low','ci95_high','p_Holm','p_HAC28_Holm_sensitivity']].to_string(index=False),'','## Interpretation limits','- Loss-difference p-values address average predictive differences, not causal effects or individual coefficient significance.','- Bootstrap intervals are pointwise, while primary HAC p-values use Holm correction over nine planned contrasts. They need not agree near a cutoff.','- Daily aggregation preserves cross-ZIP dependence; overlapping paths/refits cause serial dependence. HAC lags 7 and 28 and 14-day date blocks are exploratory sensitivity choices.','- This validation period was inspected previously. These diagnostics do not constitute untouched final testing.','- Feature groups overlap in information. Local-history removal retains pressure derived from other ZIP case histories and retains ZIP identity.','- Calendar combines weekday and month. Some month dummies are constant within a 60-day window and cannot be separately estimated in FE.','- Tree split importance is training-based and biased by correlated predictors/split opportunities. XGBoost gain and RF impurity rankings are different quantities; normalized values cannot be compared directly across model types.','- DP repeated coefficient fits overlap heavily and can have dynamic-panel bias. Coefficient ranges and sign shares are descriptive, not confidence intervals or causal estimates.','- A small p-value does not imply a large useful improvement. A large p-value does not establish no effect.','- No model or feature selection is made automatically; pressure remains in the main specification.']
 (OUT/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
 print(a.to_string(index=False))
print('Saved diagnostic tables and figures:',OUT,flush=True)
