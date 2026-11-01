# 病例激增任务v1：探索性结果

{
  "regions": 585,
  "origins": 243,
  "events_2020": 1838,
  "zips_with_events": 496,
  "qualifying_zip_days": 13212,
  "matched_targets_verified": true,
  "causal_prefix_checks_passed": true,
  "no_model_refit": true,
  "calibration_targets_end": "2020-08-31",
  "assessment_origins_start": "2020-09-01"
}

           model       phase  threshold  average_precision  positive_origin_share  positive_origins  events  detected_events  warning_episodes  false_warning_episodes  event_recall  warning_precision  false_warnings_per_30_at_risk_zip_days  mean_lead_days  median_lead_days  at_risk_zip_days
Dynamic Panel FE calibration          0           0.457213               0.009732               667     226              164               185                      21      0.725664           0.886486                                0.009192        1.048780               1.0             68537
Dynamic Panel FE  assessment          0           0.520026               0.059398              3299    1131              889              1309                     420      0.786030           0.679144                                0.226859        1.304837               1.0             55541
         XGBoost calibration          0           0.455995               0.009732               667     226              162               178                      16      0.716814           0.910112                                0.007004        1.043210               1.0             68537
         XGBoost  assessment          0           0.542057               0.059398              3299    1131              825               986                     161      0.729443           0.836714                                0.086963        1.135758               1.0             55541
   Random Forest calibration          0           0.458504               0.009732               667     226              165               191                      26      0.730088           0.863874                                0.011381        1.072727               1.0             68537
   Random Forest  assessment          0           0.540082               0.059398              3299    1131              897              1170                     273      0.793103           0.766667                                0.147459        1.230769               1.0             55541

先看事件数量与分布，再看assessment行。AP的参考是positive_origin_share，不是0.5。Lead time只描述检出的事件，不能忽略漏报。报警阈值只在4—8月选择；9—12月不调阈值。事件起点为第二次满足条件的确认日，不是生物学真实爆发日。误报预算按非活动、可评分的ZIP-days归一化。

如果最小阈值0已满足宽松的1/30误报预算，就保留0，不根据assessment寻找更好的阈值。无事件的地区也必须保留。后续先审查事件例子与敏感性，再决定冻结方案；不把研究定义当成官方疫情判定。

注意：确认日需要连续两天，因此提前1天的成功预警可能已有首个异常日作为输入。它不是在任何异常出现前的预警；也不能解释为已验证感染爆发。事件基线采用28天移动均值，持续缓慢上升可能被适应性基线吸收，数值依赖该代理定义。校准origin截至8/28，使三天目标不跨9/1。
