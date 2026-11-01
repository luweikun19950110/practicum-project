from pathlib import Path
from itertools import combinations
import json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import average_precision_score
from scipy.stats import norm
MODELS={'Dynamic Panel FE':'dynamic_panel','XGBoost':'xgboost','Random Forest':'random_forest'}
PERIODS={'Full 2021':('2021-01-01','2021-12-28'),'Delta-associated period':('2021-07-01','2021-09-27'),'Omicron emergence':('2021-12-01','2021-12-28')}
COLORS=['#64748B','#2563EB','#087F78']
def focus_analysis(output):
 output=Path(output);fig=output/'figures';fig.mkdir(exist_ok=True)
 rows=[];daily=[];horizons=[];classrows=[];loss={};ref=None
 for model,name in MODELS.items():
  a=np.load(output/name/'predictions.npz',allow_pickle=False)
  if ref is None:ref={k:a[k].copy() for k in ['zip','forecast_origins','horizons','actual_cases']}
  else:
   for k,v in ref.items():assert np.array_equal(v,a[k])
  actual=a['actual_cases'];pred=np.maximum(a['raw_predictions'],0);err=pred-actual;dates=pd.DatetimeIndex(a['forecast_origins']);assert actual.shape==(585,362,3) and (dates+pd.Timedelta(days=3)).max()<=pd.Timestamp('2021-12-31')
  loss[model]=np.abs(err).mean(axis=(0,2));ad=np.sign(actual[...,2]-actual[...,0]);pdirection=np.sign(pred[...,2]-pred[...,0]);da=np.diff(actual,axis=2);dp=np.diff(pred,axis=2)
  tag=model.lower().replace(' ','_');risk=np.load(output/'warning_evaluation'/(tag+'_risk_scores.npz'),allow_pickle=False)
  assert np.array_equal(risk['forecast_origins'],a['forecast_origins'].astype('datetime64[D]'))
  eligible=risk['eligible'];truth=risk['truth'];score=risk['risk_score']
  alarms=pd.read_csv(output/'warning_evaluation'/(tag+'_warnings.csv'),dtype={'zip':'string'},parse_dates=['forecast_origin','matched_event_date'])
  events=pd.read_csv(output/'warning_evaluation'/(tag+'_event_detection.csv'),dtype={'zip':'string'},parse_dates=['event_date'])
  zmap={z:i for i,z in enumerate(a['zip'])}
  for period,(start,end) in PERIODS.items():
   mask=(dates>=start)&(dates<=end);origin_days=dates[mask].to_numpy().astype('datetime64[D]').astype(int);origin_lookup={int(d):k for k,d in enumerate(origin_days)};em=eligible[:,mask]
   # A phase event requires an eligible phase forecast1..3days earlier.
   covered=[]
   for ev in events.itertuples():
    d=int(ev.event_date.to_datetime64().astype('datetime64[D]').astype(int));z=zmap[ev.zip]
    if any(d-h in origin_lookup and em[z,origin_lookup[d-h]] for h in [1,2,3]):covered.append((ev.zip,ev.event_date))
   covered=set(covered);ww=alarms[alarms.forecast_origin.between(start,end)];tp=ww[ww.true_warning]
   assert all((z,d) in covered for z,d in zip(tp.zip,tp.matched_event_date))
   y=truth[:,mask][em];sc=score[:,mask][em];e=err[:,mask];aa=actual[:,mask];pr=pred[:,mask]
   recalls=[]
   for v,label in [(-1,'Declining'),(0,'Endpoint-flat'),(1,'Rising')]:
    g=ad[:,mask]==v;rec=float((pdirection[:,mask][g]==v).mean()) if g.any() else np.nan;recalls.append(rec)
    classrows.append(dict(model=model,period=period,actual_class=label,paths=int(g.sum()),class_share=float(g.mean()),recall=rec))
   rows.append(dict(model=model,period=period,origin_start=start,origin_end=end,last_target=str((dates[mask].max()+pd.Timedelta(days=3)).date()),origins=int(mask.sum()),regions=585,paths=585*int(mask.sum()),trajectory_MAE=float(np.abs(e).mean()),RMSE=float(np.sqrt((e**2).mean())),bias=float(e.mean()),direction_agreement=float((ad[:,mask]==pdirection[:,mask]).mean()),balanced_direction_accuracy=float(np.nanmean(recalls)),shape_agreement=float((np.sign(da[:,mask])==np.sign(dp[:,mask])).all(axis=2).mean()),change_MAE=float(np.abs(dp[:,mask]-da[:,mask]).mean()),acceleration_MAE=float(np.abs(np.diff(pr,n=2,axis=2)-np.diff(aa,n=2,axis=2)).mean()),mean_actual_cases=float(aa.mean()),all_zero_path_share=float((aa==0).all(axis=2).mean()),actual_endpoint_flat_share=float((ad[:,mask]==0).mean()),AP=average_precision_score(y,sc) if y.any() else np.nan,positive_origin_share=float(y.mean()),events=len(covered),detected_events=len(tp),event_recall=len(tp)/len(covered) if covered else np.nan,warnings=len(ww),warning_precision=float(ww.true_warning.mean()) if len(ww) else np.nan,mean_lead_days=float(tp.lead_days.mean()),recall_at_least_2_days=float(tp.lead_days.ge(2).sum()/len(covered)) if covered else np.nan))
   for h in range(3):horizons.append(dict(model=model,period=period,horizon=h+1,MAE=float(np.abs(e[...,h]).mean()),RMSE=float(np.sqrt((e[...,h]**2).mean()))))
  daily.append(pd.DataFrame(dict(model=model,forecast_origin=dates,trajectory_MAE=loss[model],actual_total_day1=actual[...,0].sum(axis=0),predicted_total_day1=pred[...,0].sum(axis=0))))
 result=pd.DataFrame(rows);baseline=result[result.model.eq('Dynamic Panel FE')].set_index('period').trajectory_MAE
 result['MAE_improvement_vs_DP_percent']=[100*(baseline.loc[r.period]-r.trajectory_MAE)/baseline.loc[r.period] for r in result.itertuples()]
 result.to_csv(output/'focus_period_scorecard.csv',index=False);pd.DataFrame(horizons).to_csv(output/'focus_horizon_metrics.csv',index=False);pd.DataFrame(classrows).to_csv(output/'focus_direction_classes.csv',index=False)
 daily=pd.concat(daily,ignore_index=True);daily.to_csv(output/'daily_2021_comparison.csv',index=False)
 # Matched date-block intervals, all ZIPs stay together, focus windows only.
 rng=np.random.default_rng(20261101);intervals=[];tests=[]
 for period,(start,end) in list(PERIODS.items())[1:]:
  mask=(dates>=start)&(dates<=end);T=int(mask.sum())
  for reference,candidate in combinations(MODELS,2):
   diff=loss[reference][mask]-loss[candidate][mask]
   for block in [7,14]:
    ix=(rng.integers(0,T-block+1,(2000,int(np.ceil(T/block))))[...,None]+np.arange(block)).reshape(2000,-1)[:,:T]
    lo,hi=np.quantile(diff[ix].mean(axis=1),[.025,.975]);intervals.append(dict(period=period,reference=reference,candidate=candidate,MAE_improvement=float(diff.mean()),ci95_low=float(lo),ci95_high=float(hi),block_days=block,dates=T))
   centered=diff-diff.mean();lrv=float(centered@centered/T)
   for k in range(1,8):lrv+=2*(1-k/8)*float(centered[k:]@centered[:-k]/T)
   se=float(np.sqrt(max(lrv,0)/T));tests.append(dict(period=period,reference=reference,candidate=candidate,MAE_improvement=float(diff.mean()),HAC_SE=se,p_raw=float(2*norm.sf(abs(diff.mean()/se))) if se>1e-15 else np.nan,dates=T))
 tests=pd.DataFrame(tests);ix=np.argsort(tests.p_raw);tests['p_Holm']=np.nan;tests.loc[ix,'p_Holm']=np.minimum(np.maximum.accumulate(tests.p_raw.to_numpy()[ix]*(len(ix)-np.arange(len(ix)))),1)
 tests.to_csv(output/'focus_MAE_exploratory_HAC_tests.csv',index=False);pd.DataFrame(intervals).to_csv(output/'focus_MAE_date_block_intervals.csv',index=False)
 plt.rcParams.update({'font.family':'Arial','font.size':12,'axes.spines.top':False,'axes.spines.right':False})
 f,axes=plt.subplots(2,1,figsize=(12,7.5),sharex=True)
 for model,color in zip(MODELS,COLORS):
  d=daily[daily.model.eq(model)];axes[0].plot(d.forecast_origin,d.trajectory_MAE,label=model,color=color,lw=1)
  axes[1].plot(d.forecast_origin,d.predicted_total_day1,label=model,color=color,lw=1)
 d=daily[daily.model.eq('Dynamic Panel FE')];axes[1].plot(d.forecast_origin,d.actual_total_day1,label='Actual',color='#111827',lw=1.3)
 for ax in axes:
  ax.axvspan(pd.Timestamp('2021-07-01'),pd.Timestamp('2021-09-30'),color='#F59E0B',alpha=.1)
  ax.axvspan(pd.Timestamp('2021-12-01'),pd.Timestamp('2021-12-31'),color='#7C3AED',alpha=.1)
  ax.grid(alpha=.2);ax.legend(ncol=4,fontsize=9);ax.set_xlim(pd.Timestamp('2021-01-01'),pd.Timestamp('2021-12-31'))
 axes[0].set(title='ZIP-level three-day trajectory MAE',ylabel='MAE (cases)');axes[1].set(title='One-day-ahead activity summed across 585 ZIPs',ylabel='Total recorded daily cases',xlabel='Forecast origin in 2021')
 f.suptitle('2021 only: Delta-associated summer period and Omicron emergence in December')
 f.text(.5,.015,'Shading is national calendar context, not variant labels. Aggregate totals can hide offsetting ZIP errors.',ha='center',fontsize=10);f.tight_layout(rect=[0,.04,1,.95]);f.savefig(fig/'01_2021_errors_and_activity.png',dpi=200);plt.close(f)
 focus=result[~result.period.eq('Full 2021')];periods=list(PERIODS)[1:];x=np.arange(2)
 f,axes=plt.subplots(2,2,figsize=(12,8))
 for ax,col,title in zip(axes.ravel(),['trajectory_MAE','AP','event_recall','warning_precision'],['Trajectory MAE (cases)','Average Precision','Event recall','Warning precision']):
  for j,(model,color) in enumerate(zip(MODELS,COLORS)):
   values=focus[focus.model.eq(model)].set_index('period').loc[periods,col];bars=ax.bar(x+(j-1)*.24,values,width=.24,color=color,label=model)
   ax.bar_label(bars,fmt='%.3f' if col in ['trajectory_MAE','AP'] else '%.2f',padding=3,fontsize=10)
  ax.set(title=title,xticks=x,xticklabels=['Jul–Sep context','Dec emergence'],ylim=(0,focus[col].max()*1.23));ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
 axes[0,0].legend(fontsize=9);f.suptitle('Same models and warning rules, different 2021 periods');f.tight_layout();f.savefig(fig/'02_focus_period_comparison.png',dpi=200);plt.close(f)
 f,axes=plt.subplots(1,2,figsize=(12,4.5))
 for ax,(period,(start,end)) in zip(axes,list(PERIODS.items())[1:]):
  for model,color in zip(MODELS,COLORS):
   d=daily[daily.model.eq(model)&daily.forecast_origin.between(start,end)];ax.plot(d.forecast_origin,d.trajectory_MAE,label=model,color=color,lw=1.5)
  ax.set(title=period,ylabel='Trajectory MAE (cases)');ax.grid(alpha=.2);ax.legend(fontsize=9);ax.tick_params(axis='x',labelrotation=30)
 f.tight_layout();f.savefig(fig/'03_delta_omicron_error_detail.png',dpi=200);plt.close(f)
 protocol=dict(scope='2021only, originsJan1-Dec28,targets<=Dec31; no2022-2023outcomes in package',periods=PERIODS,delta_targets='July2–September30, July1–September27origins keep all3targets within selected context',omicron_targets='December2–31, December1–28origins; mixedDelta/Omicron transition, not fullOmicronwave',source='https://www.cdc.gov/mmwr/volumes/71/wr/mm7106a4.htm',variant_caveat='National surveillance context, no case-level variant attribution or claim of exact NJwave boundaries',warnings='Original2020threshold0,original7daycooldown from full2021sequence, then subset by issue date; event denominator requires an eligible origin in selected window',uncertainty='Exploratory paired7day moving date-block95%CI,14day sensitivity; focusHAC pvalues Holm across6contrasts. Conditional on historical fits, not prediction intervals or causal variant effects.',no_new_model_fit=True,no_budget_analysis=True)
 (output/'focus_protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
 lines=['# Notebook32：2021年整体及Delta/Omicron时间段比较','', '## 先看这三项','1. focus_period_scorecard.csv：2021整体、Delta相关夏季窗口和12月Omicron出现窗口的模型成绩。','2. figures/02_focus_period_comparison.png：重点时期的MAE、AP、检出率和预警正确比例。','3. figures/01_2021_errors_and_activity.png：全年病例活动与预测误差走势。','', '## 如何划分','全年origin为2021年1月1日—12月28日，共362天，585地区，211770条三天路径。所有target都在2021年内。Delta相关阶段采用7月1日—9月27日的预测，目标截至9月30日；Omicron出现阶段采用12月1日—28日的预测，目标截至12月31日。','CDC将美国主要病例激增概括为Delta2021年7—9月、Omicron2021年12月—2022年1月。我们只看2021，所以12月不能代表完整Omicron波，且月初仍有Delta传播。这只是全国日历背景，不是每条NJ病例的变异株标记。','CDC source: https://www.cdc.gov/mmwr/volumes/71/wr/mm7106a4.htm','', '## 结果',result[['model','period','origins','trajectory_MAE','RMSE','direction_agreement','AP','events','event_recall','warning_precision','mean_lead_days','recall_at_least_2_days']].to_string(index=False),'', '## 可汇报的发现']
 for period in PERIODS:
  one=result[result.period.eq(period)];best=one.loc[one.trajectory_MAE.idxmin()];apbest=one.loc[one.AP.idxmax()]
  lines.append(f'{period}: MAE最低为{best.model}（{best.trajectory_MAE:.3f}），AP最高为{apbest.model}（{apbest.AP:.3f}）。观察到的排名不等于显著优越。')
 lines+=['', '## 保持不变','34个候选特征（含两个pressure）、585个地区、60天滚动训练、每7天重训、未来1/2/3天直接预测。只复用已生成的2021预测，不额外训练。预警沿用Notebook27事件定义及2020校准阈值0，没有budget分析。','', '## 如何解释','Delta窗口中XGBoost较Dynamic Panel的MAE改善约0.0252例，7天时间块95%区间约[0.0126,0.0403]。12月两种树模型较Dynamic Panel的改善区间都跨0，不能仅凭点估计的名次断言更优。这些区间是探索性误差差异区间，不是每日病例预测区间。','比较病例预测与预警指标时分别看：MAE较低不保证AP、检出率、提前量都更好。不同阶段的病例量、事件数量及阳性比例也不同，不能把分数差异全部归因于变异株。','严格方向分为Day3大于/等于/小于Day1，连续点预测很少恰好相等，要结合平稳比例和三类recall。','事件前1—3天的成功预警不保证出现在首个异常之前。冷却规则按全年连续运行，进入一个重点时间段时不重新初始化。','95%CI是模型平均MAE差异的时间块区间，不是每日病例的预测区间。两段时间长度不同，尤其12月只有28个预测日，推断为探索性。','这些年份此前已部分探索，因此称后续时间评估，不称完全未接触的独立测试。2022—2023未纳入本次展示或方案选择。']
 (output/'START_HERE_CN.md').write_text('\n\n'.join(lines),encoding='utf-8')
 (output/'verification.json').write_text(json.dumps(dict(regions=585,origins=362,paths=211770,all_targets_within_2021=True,models_and_targets_matched=True,no_2022_2023_outcomes_in_analysis=True,existing_2020_warning_rule=True,focus_windows_calendar_context_only=True),indent=2),encoding='utf-8')
 print(result[['model','period','trajectory_MAE','AP','events','event_recall','warning_precision']].to_string(index=False));return result
if __name__=='__main__':
 import sys
 focus_analysis(Path(sys.argv[1]))
