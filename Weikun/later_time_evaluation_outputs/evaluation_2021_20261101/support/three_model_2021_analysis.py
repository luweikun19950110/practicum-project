from pathlib import Path
from itertools import combinations
import json,hashlib
import numpy as np
import pandas as pd

def three_model_analysis(archives,output):
    """Matched retrospective diagnostics, not hyperparameter selection."""
    from scipy.stats import norm
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    loaded={};manifest={};ref=None
    for name,path in archives.items():
        with np.load(path,allow_pickle=False) as z:
            if ref is None:ref={k:z[k].copy() for k in ['zip','forecast_origins','horizons','actual_cases']}
            for k,v in ref.items():assert np.array_equal(z[k],v),f'{name}: {k} differs'
            loaded[name]=np.maximum(z['raw_predictions'].copy(),0)
        manifest[name]=dict(path=str(path),sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())
    a=ref['actual_cases'];dates=pd.to_datetime(ref['forecast_origins']);h=ref['horizons'];N,T,H=a.shape
    assert (N,T,H)==(585,362,3) and np.array_equal(h,[1,2,3])
    day={};summary=[];quarter=[];monthly=[];groups=[];horizons=[];classes=[];sensitivity=[]
    da=np.diff(a,axis=2);aa=np.diff(a,n=2,axis=2)[...,0];ad=np.sign(a[...,2]-a[...,0])
    for name,p in loaded.items():
        e=p-a;dp=np.diff(p,axis=2);ap=np.diff(p,n=2,axis=2)[...,0];pdirection=np.sign(p[...,2]-p[...,0])
        cm=np.array([[((ad==x)&(pdirection==y)).sum() for y in [-1,0,1]] for x in [-1,0,1]])
        for i,label in enumerate(['Declining','Endpoint-flat','Rising']):
            classes.append(dict(model=name,actual_class=label,actual_paths=int(cm[i].sum()),recall=cm[i,i]/cm[i].sum(),precision=cm[i,i]/cm[:,i].sum() if cm[:,i].sum() else np.nan))
        d=pd.DataFrame(dict(forecast_origin=dates,trajectory_MAE=np.abs(e).mean(axis=(0,2)),MSE=(e**2).mean(axis=(0,2)),mean_bias=e.mean(axis=(0,2)),direction_agreement=(ad==pdirection).mean(axis=0),shape_agreement=(np.sign(da)==np.sign(dp)).all(axis=2).mean(axis=0),change_MAE=np.abs(dp-da).mean(axis=(0,2)),acceleration_MAE=np.abs(ap-aa).mean(axis=0)))
        day[name]=d
        row=dict(model=name,regions=N,origins=T,paths=N*T,RMSE=float(np.sqrt(d.MSE.mean())),balanced_direction_accuracy=float(np.mean(np.diag(cm)/cm.sum(axis=1))),actual_endpoint_flat_share=float((ad==0).mean()),actual_all_zero_share=float((a==0).all(axis=2).mean()))
        row.update({k:float(d[k].mean()) for k in d if k not in ['forecast_origin','MSE']});summary.append(row)
        for freq,dest in [('Q',quarter),('M',monthly)]:
            for label,f in d.groupby(d.forecast_origin.dt.to_period(freq)):
                r=dict(model=name,period=str(label),origins=len(f),RMSE=float(np.sqrt(f.MSE.mean())))
                r.update({k:float(f[k].mean()) for k in f if k not in ['forecast_origin','MSE']});dest.append(r)
        for label,mask in [('all_paths',np.ones((N,T),bool)),('all_three_zero',(a==0).all(axis=2)),('endpoint_nonflat',ad!=0),('endpoint_flat',ad==0)]:
            groups.append(dict(model=name,group=label,paths=int(mask.sum()),MAE=float(np.abs(e[mask]).mean()),direction_agreement=float((ad[mask]==pdirection[mask]).mean()),shape_agreement=float((np.sign(da[mask])==np.sign(dp[mask])).all(axis=1).mean())))
        for hh,horizon in enumerate(h):
            er=e[...,hh];horizons.append(dict(model=name,horizon=int(horizon),MAE=float(np.abs(er).mean()),RMSE=float(np.sqrt((er**2).mean())),bias=float(er.mean())))
        # Prespecified sensitivity only, never choose the best-looking threshold.
        for threshold in [0.,0.5,1.]:
            classify=lambda x:np.where(x>threshold,1,np.where(x<-threshold,-1,0))
            actual_sign=classify((a[...,2]-a[...,0])/2);pred_sign=classify((p[...,2]-p[...,0])/2)
            ac=classify(da);pc=classify(dp)
            recalls=[(pred_sign[actual_sign==j]==j).mean() if (actual_sign==j).any() else np.nan for j in [-1,0,1]]
            sensitivity.append(dict(model=name,threshold=threshold,slope_threshold_units='cases/day',movement_threshold_units='cases/day with1-day spacing',direction_agreement=float((actual_sign==pred_sign).mean()),balanced_direction_accuracy=float(np.nanmean(recalls)),actual_endpoint_flat_share=float((actual_sign==0).mean()),always_flat_direction_reference=float((actual_sign==0).mean()),two_step_shape_agreement=float((ac==pc).all(axis=2).mean()),actual_both_steps_flat_share=float((ac==0).all(axis=2).mean()),primary=threshold==0))
    yearly=[]
    for model,d in day.items():
        for year,f in d.groupby(d.forecast_origin.dt.year):
            r=dict(model=model,year=int(year),origins=len(f),RMSE=float(np.sqrt(f.MSE.mean())))
            r.update({k:float(f[k].mean()) for k in f if k not in ['forecast_origin','MSE']});yearly.append(r)
    pd.DataFrame(yearly).to_csv(output/'year_comparison.csv',index=False)
    pd.concat([d.assign(model=m) for m,d in day.items()],ignore_index=True).to_csv(output/'daily_matched_scores.csv',index=False)
    summary=pd.DataFrame(summary);summary.to_csv(output/'three_model_overall.csv',index=False)
    for filename,data in [('quarter_comparison.csv',quarter),('month_comparison.csv',monthly),('path_group_comparison.csv',groups),('horizon_comparison.csv',horizons),('direction_class_recall.csv',classes),('direction_threshold_sensitivity.csv',sensitivity)]:pd.DataFrame(data).to_csv(output/filename,index=False)
    # Common date resampling preserves covariance across all models and regions.
    rng=np.random.default_rng(20261027);draws={}
    for block in [7,14]:
        start=rng.integers(0,T-block+1,(2000,int(np.ceil(T/block))))
        draws[block]=(start[...,None]+np.arange(block)).reshape(2000,-1)[:,:T]
    contrasts=[];primary_tests=[];daily_contrasts=[]
    for base,candidate in combinations(loaded.keys(),2):
        for metric in ['trajectory_MAE','direction_agreement','shape_agreement','change_MAE','acceleration_MAE']:
            diff=(day[candidate][metric]-day[base][metric]).to_numpy() if 'agreement' in metric else (day[base][metric]-day[candidate][metric]).to_numpy()
            for block,ix in draws.items():
                lo,hi=np.quantile(diff[ix].mean(axis=1),[.025,.975])
                contrasts.append(dict(reference=base,candidate=candidate,metric=metric,improvement=float(diff.mean()),ci95_low=float(lo),ci95_high=float(hi),block_days=block,definition='Positive favors candidate. Pointwise exploratory date-block interval, conditional on fitted models and this historical period.'))
            if metric=='trajectory_MAE':
                # HAC test on one regional-average paired loss series, not142k IID paths.
                centered=diff-diff.mean();lag=7;lrv=float(centered@centered/T)
                for k in range(1,lag+1):lrv+=2*(1-k/(lag+1))*float(centered[k:]@centered[:-k]/T)
                se=float(np.sqrt(max(lrv,0)/T));z=float(diff.mean()/se) if se>1e-15 else np.nan
                primary_tests.append(dict(reference=base,candidate=candidate,MAE_improvement=float(diff.mean()),HAC_SE=se,HAC_z=z,p_HAC_two_sided=float(2*norm.sf(abs(z))) if np.isfinite(z) else np.nan,HAC_lags=lag,dates=T,interpretation='Exploratory asymptotic paired loss test on meanZIP loss per date; nonstationarity/dependence and prior exploration limit inference. Not a model coefficient or causal test.'))
                daily_contrasts.extend(dict(reference=base,candidate=candidate,forecast_origin=str(date.date()),MAE_improvement=float(value)) for date,value in zip(dates,diff))
    tests=pd.DataFrame(primary_tests);valid=np.flatnonzero(np.isfinite(tests.p_HAC_two_sided));order=valid[np.argsort(tests.p_HAC_two_sided.to_numpy()[valid])];adjust=np.maximum.accumulate(tests.p_HAC_two_sided.to_numpy()[order]*(len(order)-np.arange(len(order))))
    tests['p_Holm']=np.nan;tests.loc[order,'p_Holm']=np.minimum(adjust,1)
    tests.to_csv(output/'primary_MAE_HAC_Holm_tests.csv',index=False)
    pd.DataFrame(contrasts).to_csv(output/'paired_date_block_intervals.csv',index=False)
    pd.DataFrame(daily_contrasts).to_csv(output/'paired_daily_MAE_improvements.csv',index=False)
    (output/'analysis_definition.json').write_text(json.dumps(dict(models=manifest,primary='Raw-count trajectory MAE, threshold0 direction is supporting; never select a sign threshold by its validation accuracy',thresholds=[0,0.5,1],threshold_interpretation='Different deadbands change truth labels, predicted labels and class balance; higher agreement does not imply improved original target prediction.',p_family='Three pairwise MAE differences, Holm correction. Supporting metrics have pointwise CIs only, no unadjusted p claims.',ci='Common moving date-block draws7days primary/14days sensitivity,2000; no IID region assumption',report_role='Exploratory2021 subsequent time evaluation with previously developed features/cohort; not final holdout.',no_new_features=True,no_pressure_ablation=True,no_model_refit_in_comparison=True),indent=2),encoding='utf8')
    report='# Three-model trajectory comparison:2021 subsequent time evaluation\n\n'+summary.to_string(index=False)+'\n\n## Reading the analysis\nCompare count MAE, RMSE, exact direction/shape and magnitude-of-change errors separately. Stratify by quarter and actual path group; groups overlap and do not partition all paths. Geographic diagnostics are separate. Parameters were fixed before the RF run, not optimized to validation scores.\n\n## Uncertainty\nPaired differences average losses across all ZIPs at each date before inference. Seven-day and14-day moving-block intervals are pointwise and exploratory. The primary MAE family includes three pairwise HAC tests, Holm adjusted. This is not a coefficient significance test, a clinical efficacy claim or a calibrated prediction interval. Nonstationary outbreaks and overlapping forecasts limit both asymptotic p-values and block intervals.\n\n## Strict-zero sensitivity\nThe same raw predictions are evaluated under0,0.5,1 cases/day deadbands, introduced as sensitivity values in Notebook21. Threshold0 remains primary. Threshold changes also alter actual labels and the always-flat reference; do not pick the threshold maximizing a model score. Exact-flat scores can be low for small continuous predictions even when count errors are small.\n'
    (output/'RESULTS.md').write_text(report,encoding='utf8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    names=list(loaded);short=['Dynamic Panel','XGBoost','Random Forest'];colors=['#64748b','#2563eb','#087f78']
    fig,axes=plt.subplots(1,3,figsize=(14,4))
    for ax,col,title in zip(axes,['trajectory_MAE','direction_agreement','shape_agreement'],['Trajectory MAE (cases)','Strict endpoint direction agreement','Strict two-step shape agreement']):
        bars=ax.bar(short,summary[col],color=colors);ax.set(title=title,ylim=(0,float(summary[col].max())*1.25));ax.grid(axis='y',alpha=.2)
        ax.bar_label(bars,labels=[f'{v:.1%}' if 'agreement' in col else f'{v:.3f}' for v in summary[col]],padding=3)
    fig.suptitle('Matched 2021 subsequent time evaluation | 585 ZIPs | 362 daily origins | 3-day paths')
    fig.tight_layout();fig.savefig(output/'01_three_model_comparison.png',dpi=240);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(16,4))
    for ax,col,title in zip(axes,['direction_agreement','two_step_shape_agreement','balanced_direction_accuracy'],['Endpoint direction agreement','Two-step shape agreement','Balanced direction accuracy']):
        for name,label,color in zip(names,short,colors):
            d=pd.DataFrame(sensitivity);d=d.loc[d.model.eq(name)];ax.plot(d.threshold,d[col],marker='o',label=label,color=color)
        ref=pd.DataFrame(sensitivity).loc[lambda d:d.model.eq(names[0])]
        reference_values=ref.always_flat_direction_reference if col=='direction_agreement' else ref.actual_both_steps_flat_share if col=='two_step_shape_agreement' else np.repeat(1/3,3)
        ax.plot(ref.threshold,reference_values,color='#d94841',ls='--',label='Always-flat classification reference')
        ax.set(title=title,xlabel='Deadband threshold (cases/day)',ylabel='Agreement',xticks=[0,.5,1],ylim=(0,1));ax.grid(alpha=.2);ax.legend(frameon=False,fontsize=7)
    fig.suptitle('Sensitivity only: thresholds change labels; primary threshold remains zero')
    fig.tight_layout();fig.savefig(output/'02_direction_threshold_sensitivity.png',dpi=240);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    q=pd.DataFrame(quarter);group=pd.DataFrame(groups)
    periods_sorted=sorted(q.period.unique());x=np.arange(len(periods_sorted))
    for i,(name,label,color) in enumerate(zip(names,short,colors)):
        d=q.loc[q.model.eq(name)];axes[0].bar(x+(i-1)*.24,d.trajectory_MAE,width=.24,label=label,color=color)
        d=group.loc[group.model.eq(name)].set_index('group');axes[1].bar(np.arange(2)+(i-1)*.24,d.loc[['all_three_zero','endpoint_nonflat'],'MAE'],width=.24,label=label,color=color)
    axes[0].set(title='Quarter-specific trajectory MAE',xticks=x,xticklabels=periods_sorted,ylabel='MAE (cases)')
    axes[0].tick_params(axis='x',labelrotation=65)
    axes[1].set(title='Selected actual path groups',xticks=[0,1],xticklabels=['All three days zero','Different endpoints'],ylabel='MAE (cases)')
    for ax in axes:ax.legend(frameon=False,fontsize=8);ax.grid(axis='y',alpha=.2)
    fig.tight_layout();fig.savefig(output/'03_quarter_and_path_groups.png',dpi=240);plt.close(fig)
    fig,axes=plt.subplots(4,1,figsize=(13,12),sharex=True)
    for name,label,color in zip(names,short,colors):axes[0].plot(dates,day[name].trajectory_MAE,label=label,color=color,lw=1)
    axes[0].set(title='ZIP-level trajectory MAE',ylabel='MAE (cases)');axes[0].legend(frameon=False,ncol=3)
    for hh,horizon in enumerate(h):
        ax=axes[hh+1];ax.plot(dates,a[...,hh].sum(axis=0),label='Actual',color='#111827',lw=1.4)
        for name,label,color in zip(names,short,colors):ax.plot(dates,loaded[name][...,hh].sum(axis=0),label=label,color=color,lw=1)
        ax.set(title=f'{int(horizon)}-day ahead: summed across 585 ZIPs',ylabel='Total daily cases');ax.legend(frameon=False,ncol=4,fontsize=8)
    for ax in axes:ax.grid(alpha=.2)
    axes[-1].set_xlabel('Forecast origin (target date=origin+horizon)')
    fig.suptitle('Actual and predicted activity alongside trajectory errors |2021 subsequent time evaluation')
    fig.text(.5,.012,'Aggregate curves can hide offsetting ZIP errors. No smoothing. Top panel scores ZIP-level paths, not aggregate totals.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.035,1,.97]);fig.savefig(output/'04_errors_and_actual_forecasts.png',dpi=220);plt.close(fig)
    fig,axes=plt.subplots(1,4,figsize=(14,4))
    for ax,date in zip(axes,pd.to_datetime(['2021-01-01','2021-07-01','2021-10-01','2021-12-01'])):
        t=dates.get_loc(date);ax.plot(h,a[:,t,:].sum(axis=0),color='#111827',marker='o',label='Actual')
        for name,label,color in zip(names,short,colors):ax.plot(h,loaded[name][:,t,:].sum(axis=0),color=color,marker='o',label=label)
        ax.set(title=f'Origin: {date.date()}',xlabel='Days ahead',xticks=h);ax.grid(alpha=.2);ax.legend(frameon=False,fontsize=7)
    axes[0].set_ylabel('Total daily cases across 585 ZIPs')
    fig.suptitle('Same-origin three-day paths: four calendar-selected illustrative origins, not representative scores')
    fig.tight_layout();fig.savefig(output/'05_same_origin_path_examples.png',dpi=240);plt.close(fig)
    return summary,tests
