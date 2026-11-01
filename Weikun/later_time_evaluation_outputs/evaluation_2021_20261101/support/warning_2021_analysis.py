from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import average_precision_score,precision_recall_curve

def event_labels(counts):
    """Causal labels; onset is confirmation, never backdated."""
    s=pd.Series(np.asarray(counts,dtype=float))
    ma=s.rolling(3,min_periods=3).mean()
    hist=ma.shift(3).rolling(28,min_periods=28)
    mean,sd=hist.mean(),hist.std(ddof=1)
    threshold=mean+2*sd
    qualify=(ma>threshold)&(s.rolling(3).sum()>=5)&threshold.notna()
    valid=threshold.notna().to_numpy()
    # Smooth continuous excess with the same sign as the two qualification gates.
    scale=np.maximum(sd.to_numpy(),1.)
    margin=np.minimum((ma.to_numpy()-threshold.to_numpy())/scale,
                      (s.rolling(3).sum().to_numpy()-5+1e-9)/(3*scale))
    active=np.zeros(len(s),bool);onset=np.zeros(len(s),bool)
    in_event=False;off=0
    for k in range(len(s)):
        if in_event:
            off=0 if qualify.iloc[k] else off+1
            if off>=7:in_event=False;off=0
        elif k>0 and qualify.iloc[k] and qualify.iloc[k-1]:
            in_event=True;onset[k]=True
        active[k]=in_event
    return dict(ma=ma.to_numpy(),threshold=threshold.to_numpy(),sd=sd.to_numpy(),
                qualify=qualify.to_numpy(),valid=valid,margin=margin,active=active,onset=onset)

def warning_events(score,eligible,truth_onset,origins,dates,threshold):
    """Seven-day issue cooldown. One alarm matches at most one event."""
    rows=[];events=[]
    for z in range(len(score)):
        event_dates=dates[truth_onset[z]]
        # Denominator: events with at least one scored eligible origin 1..3 days before.
        covered=[d for d in event_dates if np.any(eligible[z]&((d-origins).astype('timedelta64[D]').astype(int)>=1)&((d-origins).astype('timedelta64[D]').astype(int)<=3))]
        matched=set();last=None
        for k,d in enumerate(origins):
            if not eligible[z,k] or not score[z,k]>threshold:continue
            if last is not None and (d-last).astype('timedelta64[D]').astype(int)<7:continue
            last=d
            candidates=[e for e in covered if e not in matched and 1<=int((e-d)/np.timedelta64(1,'D'))<=3]
            target=min(candidates) if candidates else None
            if target is not None:matched.add(target)
            rows.append(dict(region_index=z,forecast_origin=str(d)[:10],matched_event_date=str(target)[:10] if target is not None else '',
                             true_warning=target is not None,lead_days=float((target-d)/np.timedelta64(1,'D')) if target is not None else np.nan))
        for d in covered:events.append(dict(region_index=z,event_date=str(d)[:10],detected=d in matched))
    alarms=pd.DataFrame(rows,columns=['region_index','forecast_origin','matched_event_date','true_warning','lead_days'])
    ev=pd.DataFrame(events,columns=['region_index','event_date','detected'])
    tp=int(alarms.true_warning.sum()) if len(alarms) else 0;fp=len(alarms)-tp
    exposure=int(eligible.sum())
    metrics=dict(events=len(ev),detected_events=int(ev.detected.sum()) if len(ev) else 0,warning_episodes=len(alarms),false_warning_episodes=fp,
                 event_recall=tp/len(ev) if len(ev) else np.nan,warning_precision=tp/len(alarms) if len(alarms) else np.nan,
                 false_warnings_per_30_at_risk_zip_days=fp*30/exposure if exposure else np.nan,
                 mean_lead_days=float(alarms.lead_days.mean()) if len(alarms) else np.nan,
                 median_lead_days=float(alarms.lead_days.median()) if len(alarms) else np.nan,at_risk_zip_days=exposure)
    return metrics,alarms,ev


def analyze_warnings(root,runs,output):
    from sklearn.metrics import average_precision_score
    root,output=Path(root),Path(output);output.mkdir(parents=True,exist_ok=True);fig=output/'figures';fig.mkdir(exist_ok=True)
    models=list(runs);ref=np.load(Path(runs[models[0]])/'predictions.npz',allow_pickle=False)
    ids=ref['zip'];origins=ref['forecast_origins'].astype('datetime64[D]');origin_days=origins.astype(int)
    frame=pd.read_csv(root/'rolling_trajectory_outputs/inputs/nj_daily_features.csv.gz',usecols=['zip','date','cases_today'],dtype={'zip':'string'},parse_dates=['date'])
    frame=frame[frame.zip.isin(ids)]
    dates=pd.date_range('2020-01-01','2021-12-31').to_numpy().astype('datetime64[D]')
    counts=frame.pivot(index='zip',columns='date',values='cases_today').reindex(index=ids,columns=dates).to_numpy(float)
    assert np.isfinite(counts).all();pos=np.searchsorted(dates,origins)
    assert np.array_equal(np.stack([counts[:,pos+h] for h in [1,2,3]],axis=-1),ref['actual_cases'])
    labs=[event_labels(row) for row in counts]
    onset=np.stack([r['onset'] for r in labs]);active=np.stack([r['active'] for r in labs]);valid=np.stack([r['valid'] for r in labs])
    old_labels=pd.read_csv(root/'outbreak_task_outputs/case_surge_v1_20261101/daily_event_labels_2020.csv.gz',dtype={'zip':'string'},parse_dates=['date'])
    old_dates=dates[dates<np.datetime64('2021-01-01')]
    for field,values in [('onset',onset),('active',active)]:
        old_array=old_labels.pivot(index='zip',columns='date',values=field).reindex(index=ids,columns=old_dates).to_numpy(dtype=bool)
        assert np.array_equal(old_array,values[:,:len(old_dates)]),'2020 event policy changed'
    eligible=(~active[:,pos])&valid[:,pos]
    future=np.stack([onset[:,pos+h] for h in [1,2,3]],axis=-1).any(axis=-1)
    old=pd.read_csv(root/'outbreak_task_outputs/case_surge_v1_20261101/warning_metrics.csv')
    threshold=old[old.phase.eq('calibration')].set_index('model').threshold.to_dict()
    allmetrics=[];riskdict={};missedcatalog=[]
    labels={'overall':np.repeat('2021',len(origins)),'year':pd.DatetimeIndex(origins).year.astype(str),'quarter':pd.DatetimeIndex(origins).to_period('Q').astype(str)}
    origin_index={int(d):i for i,d in enumerate(origin_days)}
    for model,run in runs.items():
        data=np.load(Path(run)/'predictions.npz',allow_pickle=False)
        for k in ['zip','forecast_origins','horizons','actual_cases']:assert np.array_equal(data[k],ref[k])
        pred=np.maximum(data['raw_predictions'],0);score=np.empty(eligible.shape)
        for j,k in enumerate(pos):
            seq=np.concatenate([counts[:,k-32:k+1],pred[:,j]],axis=1)
            means=np.full(seq.shape,np.nan);means[:,2:]=(seq[:,2:]+seq[:,1:-1]+seq[:,:-2])/3
            margins=[]
            for d in range(seq.shape[1]-4,seq.shape[1]):
                baseline=means[:,d-30:d-2];assert baseline.shape[1]==28 and np.isfinite(baseline).all()
                mu=baseline.mean(axis=1);sd=baseline.std(axis=1,ddof=1);scale=np.maximum(sd,1)
                margins.append(np.minimum((means[:,d]-mu-2*sd)/scale,(seq[:,d-2:d+1].sum(axis=1)-5+1e-9)/(3*scale)))
            margins=np.stack(margins,axis=1);score[:,j]=np.maximum.reduce([np.minimum(margins[:,h-1],margins[:,h]) for h in [1,2,3]])
        assert np.isfinite(score).all();alarms=[];evrows=[]
        for z in range(len(ids)):
            # One event denominator across all three models, based solely on eligibility.
            covered=[]
            for d in dates[onset[z]].astype(int):
                if any((d-h) in origin_index and eligible[z,origin_index[d-h]] for h in [1,2,3]):covered.append(int(d))
            eventset=set(covered);matched=set();last=-1000000;matched_origin={}
            for j in np.flatnonzero(eligible[z]&(score[z]>threshold[model])):
                d=int(origin_days[j])
                if d-last<7:continue
                last=d;candidate=[d+h for h in [1,2,3] if d+h in eventset and d+h not in matched]
                e=min(candidate) if candidate else None
                if e is not None:matched.add(e);matched_origin[e]=d
                alarms.append(dict(zip=ids[z],forecast_origin=pd.Timestamp(np.datetime64(d,'D')),matched_event_date=pd.Timestamp(np.datetime64(e,'D')) if e is not None else pd.NaT,true_warning=e is not None,lead_days=e-d if e is not None else np.nan))
            for e in covered:
                evrows.append(dict(zip=ids[z],event_date=pd.Timestamp(np.datetime64(e,'D')),detected=e in matched,lead_days=e-matched_origin[e] if e in matched else np.nan))
        warn=pd.DataFrame(alarms);events=pd.DataFrame(evrows);tag=model.lower().replace(' ','_')
        warn.to_csv(output/(tag+'_warnings.csv'),index=False);events.to_csv(output/(tag+'_event_detection.csv'),index=False)
        np.savez_compressed(output/(tag+'_risk_scores.npz'),zip=ids,forecast_origins=origins,risk_score=score,eligible=eligible,truth=future)
        riskdict[model]=score
        for scope,values in labels.items():
            if scope=='overall':wp=np.repeat('2021',len(warn));ep=np.repeat('2021',len(events))
            elif scope=='year':wp=warn.forecast_origin.dt.year.astype(str).to_numpy();ep=events.event_date.dt.year.astype(str).to_numpy()
            else:wp=warn.forecast_origin.dt.to_period('Q').astype(str).to_numpy();ep=events.event_date.dt.to_period('Q').astype(str).to_numpy()
            for period in np.unique(values):
                mask=values==period;ww=warn.loc[wp==period];ee=events.loc[ep==period]
                y=future[:,mask][eligible[:,mask]];sc=score[:,mask][eligible[:,mask]]
                tp=int(ww.true_warning.sum());n=int(eligible[:,mask].sum())
                allmetrics.append(dict(model=model,scope=scope,period=period,threshold=threshold[model],AP=average_precision_score(y,sc) if y.any() else np.nan,positive_origin_share=float(y.mean()),at_risk_zip_days=n,events=len(ee),detected_events=int(ee.detected.sum()),event_recall=float(ee.detected.mean()),warning_episodes=len(ww),warning_precision=tp/len(ww) if len(ww) else np.nan,false_warning_episodes=len(ww)-tp,mean_lead_days=float(ee.lead_days.mean()),median_lead_days=float(ee.lead_days.median()),recall_at_least_2_days=float(ee.lead_days.ge(2).sum()/len(ee)),false_warnings_per_1000_at_risk_zip_days=(len(ww)-tp)*1000/n))
        print('Warning analysis finished:',model,flush=True)
    metrics=pd.DataFrame(allmetrics);metrics.to_csv(output/'warning_metrics_by_period.csv',index=False)
    for scope in ['overall','year','quarter']:
        table=metrics[metrics.scope.eq(scope)]
        for _,g in table.groupby('period'):
            assert g.events.nunique()==1 and g.at_risk_zip_days.nunique()==1 and g.positive_origin_share.nunique()==1
    colors=['#64748B','#2563EB','#087F78'];plt.rcParams.update({'font.family':'Arial','font.size':12,'axes.spines.top':False,'axes.spines.right':False})
    f,axes=plt.subplots(2,2,figsize=(12,8))
    for m,c in zip(models,colors):
        d=metrics[metrics.model.eq(m)&metrics.scope.eq('year')].sort_values('period')
        for ax,col,title in zip(axes.ravel(),['AP','event_recall','warning_precision','recall_at_least_2_days'],['Average Precision','Event recall','Warning precision','Recall with at least 2-day lead']):
            ax.plot(d.period,d[col],'o-',color=c,label=m);ax.set(title=title,xlabel='Year',ylim=(0,1));ax.grid(alpha=.2)
    axes[0,0].legend(fontsize=9);f.suptitle('Later-year warning performance using the unchanged 2020 threshold');f.tight_layout();f.savefig(fig/'01_yearly_warning_comparison.png',dpi=200);plt.close(f)
    protocol=dict(definition='Original Notebook27 MA3, baseline28means gap3, +2SD, minimum3day sum5, two-day confirmation, seven-day reset',threshold_source='2020 calibration only, unchanged per model',thresholds=threshold,truth='Full continuous2020–2023recorded onset history; no annual reset of event state',cooldown='Start evaluation with no carried alert onJan1 2021, then continuous7day issue cooldown across2021; no yearly reset',period_basis='AP and precision by forecast-origin period; recall and lead by event-confirmation period. Cross-period matched alerts retain their original issue dates.',denominator='all eligible events with at least one scored inactive origin1..3days before confirmation',limitations=['onset availability retrospective','prior2021exploration means not untouched finaltest','lead refers to confirmation, not biological onset','no model or alert parameter tuned on these outcomes','last3days2021origins excluded, earlier year-end origins retained within evaluation stage'],no_budget_analysis=True)
    (output/'warning_protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8');return metrics
