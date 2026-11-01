from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

MODELS=['Dynamic Panel FE','XGBoost','Random Forest']
BUDGETS=[0.,.05,.1,.25,.5,1.,2.]

def evaluate(score,eligible,event_days,origins,threshold,details=False):
    # Ordinal day arrays, one-to-one matching, issue cooldown seven calendar days.
    n=score.shape[0]; exposure=int(eligible.sum()); rows=[]; ne=tp=fp=early=0; leads=[]
    for z in range(n):
        ev=[int(d) for d in event_days[z] if np.any(eligible[z]&((d-origins)>=1)&((d-origins)<=3))]
        ne+=len(ev); matched=set(); last=-1000000
        for k in np.flatnonzero(eligible[z]&(score[z]>threshold)):
            d=int(origins[k])
            if d-last<7:continue
            last=d
            choices=[e for e in ev if e not in matched and 1<=e-d<=3]
            target=min(choices) if choices else None
            if target is None:fp+=1
            else:
                matched.add(target);tp+=1;leads.append(target-d);early+=int(target-d>=2)
            if details:rows.append((z,d,target,target-d if target is not None else np.nan))
    return dict(events=ne,detected_events=tp,false_warnings=fp,warnings=tp+fp,
                event_recall=tp/ne if ne else np.nan,warning_precision=tp/(tp+fp) if tp+fp else np.nan,
                recall_at_least_2_days=early/ne if ne else np.nan,
                false_warnings_per_1000_at_risk_zip_days=fp*1000/exposure,
                at_risk_zip_days=exposure,mean_lead_days=float(np.mean(leads)) if leads else np.nan),rows

def run(root,output):
    root,output=Path(root),Path(output);output.mkdir(parents=True,exist_ok=True);fig=output/'figures';fig.mkdir(exist_ok=True)
    source=root/'outbreak_task_outputs'/'case_surge_v1_20261101'
    if not source.exists():raise FileNotFoundError(source)
    catalog=pd.read_csv(source/'event_catalog_2020.csv',dtype={'zip':'string'},parse_dates=['event_date'])
    grids=[];chosen=[];metrics=[];reference=None;hashes={}
    for model in MODELS:
        tag=model.lower().replace(' ','_');path=source/(tag+'_risk_scores.csv.gz');hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        df=pd.read_csv(path,dtype={'zip':'string'},parse_dates=['forecast_origin'])
        ids=np.sort(df.zip.unique());dates=np.sort(df.forecast_origin.unique()).astype('datetime64[D]');orig=dates.astype(int)
        score=df.pivot(index='zip',columns='forecast_origin',values='risk_score').reindex(index=ids,columns=dates).to_numpy()
        eligible=df.pivot(index='zip',columns='forecast_origin',values='eligible').reindex(index=ids,columns=dates).to_numpy(dtype=bool)
        truth=df.pivot(index='zip',columns='forecast_origin',values='event_in_next_3_days').reindex(index=ids,columns=dates).to_numpy(dtype=bool)
        if reference is None:reference=(ids,dates,eligible,truth)
        else:
            for a,b in zip(reference,(ids,dates,eligible,truth)):assert np.array_equal(a,b)
        event_days=[catalog.loc[catalog.zip.eq(z),'event_date'].to_numpy().astype('datetime64[D]').astype(int) for z in ids]
        cal=(dates>=np.datetime64('2020-04-30'))&(dates<=np.datetime64('2020-08-28'))
        assess=(dates>=np.datetime64('2020-09-01'))&(dates<=np.datetime64('2020-12-28'))
        assert dates[cal].max()+np.timedelta64(3,'D')<dates[assess].min()
        positive=score[:,cal][eligible[:,cal]&(score[:,cal]>0)]
        thresholds=np.unique(np.r_[0,np.quantile(positive,np.linspace(0,1,81)),.25,.5,1,2,3,5,10,np.inf])
        local=[]
        for threshold in thresholds:
            met,_=evaluate(score[:,cal],eligible[:,cal],event_days,orig[cal],threshold)
            local.append(dict(model=model,threshold=threshold,**met))
        grids.extend(local)
        # No assumed monotonicity: cooldown can change event matching at each threshold.
        for budget in BUDGETS:
            allowed=[r for r in local if r['false_warnings_per_1000_at_risk_zip_days']<=budget+1e-12]
            pick=sorted(allowed,key=lambda r:(-r['event_recall'],r['false_warnings_per_1000_at_risk_zip_days'],r['threshold']))[0]
            chosen.append(dict(budget_per_1000=budget,**pick))
            for phase,mask in [('calibration',cal),('assessment',assess)]:
                met,rows=evaluate(score[:,mask],eligible[:,mask],event_days,orig[mask],pick['threshold'],True)
                metrics.append(dict(model=model,budget_per_1000=budget,threshold=pick['threshold'],phase=phase,**met))
                alarms=pd.DataFrame(rows,columns=['region_index','origin_day','event_day','lead_days'])
                if len(alarms):
                    alarms['zip']=ids[alarms.region_index.to_numpy()]
                    alarms['forecast_origin']=pd.to_datetime(alarms.origin_day,unit='D').dt.strftime('%Y-%m-%d')
                    alarms['matched_event_date']=pd.to_datetime(alarms.event_day,unit='D').dt.strftime('%Y-%m-%d')
                alarms.to_csv(output/f'{tag}_budget_{budget:g}_{phase}_warnings.csv',index=False)
        # Saved zero-threshold results must exactly reproduce Notebook27.
        old=pd.read_csv(source/'warning_metrics.csv');old=old[(old.model==model)&(old.phase=='assessment')].iloc[0]
        check,_=evaluate(score[:,assess],eligible[:,assess],event_days,orig[assess],0)
        assert check['events']==old.events and check['detected_events']==old.detected_events
        assert check['false_warnings']==old.false_warning_episodes
        print('Finished:',model,flush=True)
    g=pd.DataFrame(grids);c=pd.DataFrame(chosen);m=pd.DataFrame(metrics);a=m[m.phase.eq('assessment')].copy()
    g.to_csv(output/'calibration_threshold_grid.csv',index=False);c.to_csv(output/'calibration_selected_thresholds.csv',index=False)
    m.to_csv(output/'metrics_by_budget.csv',index=False);a.to_csv(output/'assessment_by_budget.csv',index=False)
    plt.rcParams.update({'font.family':'Arial','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    colors=['#64748B','#2563EB','#087F78']
    f,axes=plt.subplots(1,3,figsize=(15,4.5))
    for model,color in zip(MODELS,colors):
        q=a[a.model.eq(model)].sort_values('budget_per_1000')
        for ax,col,title in zip(axes,['event_recall','warning_precision','recall_at_least_2_days'],['Event recall','Warning precision','Recall with at least 2-day lead']):
            ax.plot(q.budget_per_1000,q[col],'o-',color=color,label=model);ax.set(xlabel='Calibration budget: false warnings / 1,000 at-risk ZIP-days',ylabel=title,ylim=(0,1));ax.grid(alpha=.2)
    axes[0].legend(fontsize=9);f.suptitle('Same calibration budgets; Sep–Dec 2020 exploratory assessment',fontsize=14)
    f.tight_layout();f.savefig(fig/'01_budget_tradeoff.png',dpi=200,bbox_inches='tight');plt.close(f)
    f,axes=plt.subplots(1,2,figsize=(11,4.5))
    for model,color in zip(MODELS,colors):
        q=a[a.model.eq(model)].sort_values('budget_per_1000')
        axes[0].plot(q.false_warnings_per_1000_at_risk_zip_days,q.event_recall,'o-',label=model,color=color)
        axes[1].plot(q.budget_per_1000,q.false_warnings_per_1000_at_risk_zip_days,'o-',label=model,color=color)
    axes[0].set(xlabel='Realized assessment false warnings / 1,000 at-risk ZIP-days',ylabel='Event recall',ylim=(0,1))
    axes[1].plot([0,2],[0,2],'--',color='gray',label='Budget reference')
    axes[1].set(xlabel='Calibration budget / 1,000 at-risk ZIP-days',ylabel='Realized assessment false-warning rate')
    for ax in axes:ax.grid(alpha=.2);ax.legend(fontsize=8)
    f.suptitle('A calibration budget is not a guarantee of future false-warning rates');f.tight_layout();f.savefig(fig/'02_realized_false_warning_rates.png',dpi=200,bbox_inches='tight');plt.close(f)
    protocol=dict(primary_definition='Notebook27 MA3 unchanged',budgets_per_1000_at_risk_zip_days=BUDGETS,threshold_candidates='0, calibration-only positive-score quantiles (81 positions), fixed values .25,.5,1,2,3,5,10 and infinity; never negative',selection='maximize calibration event recall subject to budget; ties lower realized false warning rate, then lower threshold',calibration='Apr30-Aug28 2020 origins, targets end Aug31',assessment='Sep1-Dec28 2020, previously inspected, exploratory',warning_policy='score strictly greater than threshold; seven-day issue cooldown; one-to-one matching before confirmation by1..3days',early_recall='events detected at least2days before confirmation / all eligible events; not conditional on detection',comparison='same labels,585ZIPs,dates and horizon for all models; calibration budget equal, realized assessment rate may differ',limitations=['quantile grid is finite','calibration has226events vs1131assessment events; epidemic activity shifts','no inference of pre-biological-onset warning','no formal statistical superiority tests','no model refit; no2021-2023outcomes'],source_sha256=hashes)
    (output/'comparison_definition.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    report='# Notebook30：相同误报预算下比较模型\n\n先看 figures/01_budget_tradeoff.png 和 assessment_by_budget.csv。\n\n主事件定义仍为3天。用4—8月选择阈值，9—12月只计算表现。每1000个可预警ZIP日允许0/.05/.1/.25/.5/1/2次误报。一个ZIP的1000天或多个ZIP累计1000天均是相同暴露单位，不是1000个事件，也不是误报百分比。阈值不允许小于0，以保留预测满足病例激增条件这一要求。\n\n每个预算下选择校准期事件检出率最高的阈值。冷却期会使表现不完全单调，所以逐个阈值实际计算，不假定单调。相同的是校准预算，不保证后续实际误报率相同；必须结合02图。\n\n'+a[['model','budget_per_1000','threshold','event_recall','warning_precision','recall_at_least_2_days','false_warnings_per_1000_at_risk_zip_days','false_warnings','detected_events']].to_string(index=False)+'\n\n0预算仅意味着校准期没有误报，不意味着后续不会误报。非负阈值下若宽松预算已经饱和，更多预算不一定提高检出率。9—12月此前已经查看，属于探索性分析，不能称为全新独立测试。当前不按后续期最优分数选择最终预算或最终模型。\n'
    (output/'RESULTS_CN.md').write_text(report,encoding='utf-8')
    (output/'verification.json').write_text(json.dumps(dict(same_cohort_verified=True,notebook27_zero_threshold_reproduced=True,calibration_targets_before_assessment=True,no_model_refit=True,regions=len(ids),assessment_events=int(a.events.iloc[0])),indent=2),encoding='utf-8')
    print(a[['model','budget_per_1000','event_recall','warning_precision','recall_at_least_2_days','false_warnings_per_1000_at_risk_zip_days']].to_string(index=False));return m
