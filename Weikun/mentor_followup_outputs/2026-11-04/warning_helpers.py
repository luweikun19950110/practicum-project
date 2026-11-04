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

