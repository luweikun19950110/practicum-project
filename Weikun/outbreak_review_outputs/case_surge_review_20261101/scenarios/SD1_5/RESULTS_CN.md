# 病例激增任务v1：探索性结果

{
  "regions": 585,
  "origins": 243,
  "events_2020": 1965,
  "zips_with_events": 497,
  "qualifying_zip_days": 17160,
  "matched_targets_verified": true,
  "causal_prefix_checks_passed": true,
  "no_model_refit": true,
  "calibration_targets_end": "2020-08-31",
  "assessment_origins_start": "2020-09-01"
}

           model       phase  threshold  average_precision  positive_origin_share  positive_origins  events  detected_events  warning_episodes  false_warning_episodes  event_recall  warning_precision  false_warnings_per_30_at_risk_zip_days  mean_lead_days  median_lead_days  at_risk_zip_days
Dynamic Panel FE calibration          0           0.450214               0.011141               758     258              200               237                      37      0.775194           0.843882                                0.016315        1.050000               1.0             68034
Dynamic Panel FE  assessment          0           0.541467               0.068169              3536    1219              982              1392                     410      0.805578           0.705460                                0.237127        1.304481               1.0             51871
         XGBoost calibration          0           0.450055               0.011141               758     258              193               228                      35      0.748062           0.846491                                0.015433        1.062176               1.0             68034
         XGBoost  assessment          0           0.569269               0.068169              3536    1219              929              1106                     177      0.762100           0.839964                                0.102369        1.137783               1.0             51871
   Random Forest calibration          0           0.458190               0.011141               758     258              198               235                      37      0.767442           0.842553                                0.016315        1.055556               1.0             68034
   Random Forest  assessment          0           0.562131               0.068169              3536    1219              968              1264                     296      0.794094           0.765823                                0.171194        1.219008               1.0             51871

先看事件数量与分布，再看assessment行。AP的参考是positive_origin_share，不是0.5。Lead time只描述检出的事件，不能忽略漏报。报警阈值只在4—8月选择；9—12月不调阈值。事件起点为第二次满足条件的确认日，不是生物学真实爆发日。误报预算按非活动、可评分的ZIP-days归一化。

如果最小阈值0已满足宽松的1/30误报预算，就保留0，不根据assessment寻找更好的阈值。无事件的地区也必须保留。后续先审查事件例子与敏感性，再决定冻结方案；不把研究定义当成官方疫情判定。

注意：确认日需要连续两天，因此提前1天的成功预警可能已有首个异常日作为输入。它不是在任何异常出现前的预警；也不能解释为已验证感染爆发。事件基线采用28天移动均值，持续缓慢上升可能被适应性基线吸收，数值依赖该代理定义。校准origin截至8/28，使三天目标不跨9/1。
