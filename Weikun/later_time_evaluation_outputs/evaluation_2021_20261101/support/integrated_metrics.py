from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from residual_moran_2021 import residual_moran

def run(output,geography):
    output=Path(output); geography=Path(geography)
    target=output/'integrated_metrics';target.mkdir(exist_ok=True)
    models={'dynamic_panel':'Dynamic Panel FE','xgboost':'XGBoost','random_forest':'Random Forest'}
    all_tables=[]
    for key,name in models.items():
        folder=target/key
        if (folder/'residual_moran_by_origin_horizon.csv').exists():
            table=pd.read_csv(folder/'residual_moran_by_origin_horizon.csv')
        else:
            table,_=residual_moran(output/key/'predictions.npz',geography,folder)
        table['model']=name;all_tables.append(table)
    all_tests=pd.concat(all_tables,ignore_index=True)
    # One declared family across all models, dates and horizons for final reporting.
    pv=all_tests.p_permutation_two_sided.to_numpy();valid=np.isfinite(pv)
    inds=np.flatnonzero(valid);order=inds[np.argsort(pv[inds],kind='stable')]
    q=np.full(len(pv),np.nan)
    q[order]=np.minimum(1,np.minimum.accumulate((pv[order]*len(order)/np.arange(1,len(order)+1))[::-1])[::-1])
    all_tests['q_BH_all_models']=q
    all_tests.to_csv(target/'residual_moran_all_models.csv',index=False)
    periods={'Full 2021':('2021-01-01','2021-12-28'),'Delta-associated period':('2021-07-01','2021-09-27'),'Omicron emergence':('2021-12-01','2021-12-28')}
    summaries=[]
    for period,(start,end) in periods.items():
        selected=all_tests[all_tests.forecast_origin.between(start,end)]
        for (model,h),g in selected.groupby(['model','horizon']):
            summaries.append(dict(model=model,period=period,horizon=h,dates=len(g),mean_Moran_I=g.Moran_I.mean(),median_Moran_I=g.Moran_I.median(),BH_significant_share=g.q_BH_all_models.lt(.05).mean(),positive_BH_significant_share=(g.Moran_I.gt(0)&g.q_BH_all_models.lt(.05)).mean()))
    spatial=pd.DataFrame(summaries);spatial.to_csv(target/'residual_moran_period_summary.csv',index=False)
    scores=pd.read_csv(output/'focus_period_scorecard.csv')
    warnings=pd.read_csv(output/'warning_evaluation/warning_metrics_by_period.csv')
    overall=warnings[warnings.scope.eq('overall')].set_index('model')
    for h in [1,2,3]:
        sub=spatial[spatial.horizon.eq(h)][['model','period','mean_Moran_I','positive_BH_significant_share']].rename(columns={'mean_Moran_I':f'Moran_I_h{h}','positive_BH_significant_share':f'positive_BH_share_h{h}'})
        scores=scores.merge(sub,on=['model','period'],validate='one_to_one')
    scores['median_lead_days']=np.where(scores.period.eq('Full 2021'),scores.model.map(overall.median_lead_days),np.nan)
    scores.to_csv(target/'unified_evaluation_scorecard.csv',index=False)
    colors=['#64748B','#2563EB','#087F78']; names=list(models.values())
    fig,axes=plt.subplots(3,1,figsize=(12,8),sharex=True)
    for h,ax in enumerate(axes,1):
        for name,c in zip(names,colors):
            d=all_tests[(all_tests.model==name)&(all_tests.horizon==h)]
            ax.plot(pd.to_datetime(d.forecast_origin),d.Moran_I,color=c,lw=1,label=name)
        ax.axhline(-1/584,color='black',ls='--',lw=.8)
        ax.set(title=f'{h}-day ahead',ylabel="Residual Moran's I");ax.grid(alpha=.2)
    axes[0].legend(ncol=3,frameon=False);axes[-1].set_xlabel('Forecast origin in 2021')
    fig.tight_layout();fig.savefig(target/'residual_moran_comparison_2021.png',dpi=220);plt.close(fig)
    (target/'metric_definitions.json').write_text(json.dumps(dict(spatial='Same previous symmetric union8-neighbor geographic weights, row standardized. 999permutations, seed20261027. Per-model q preserved. Primary reporting uses BH across all3models x362dates x3horizons =3258tests.',interpretation='Mean I is descriptive. Lower positive I suggests less residual clustering under this graph, not proof of better forecasts or transmission removal. No paired significance test for model differences in I. Exact ZIP-ZCTA mapping unvalidated. Count residual exchangeability may fail.',lead='Mean and median lead among detected events only. Reference is second qualifying-day confirmation, not first abnormal day. Missed events excluded from lead mean. Rule and thresholds unchanged.',changes='No retraining, no forecasts changed, only2021diagnostics.',scope='2022–2023 excluded.'),indent=2),encoding='utf-8')
    print(scores[scores.period.eq('Full 2021')][['model','trajectory_MAE','AP','event_recall','warning_precision','mean_lead_days','median_lead_days','Moran_I_h1','Moran_I_h2','Moran_I_h3']].to_string(index=False),flush=True)
    return scores

if __name__=='__main__':
    import sys
    run(sys.argv[1],sys.argv[2])
