# 病例激增任务v1：探索性结果

{
  "regions": 585,
  "origins": 243,
  "events_2020": 1625,
  "zips_with_events": 491,
  "qualifying_zip_days": 18869,
  "matched_targets_verified": true,
  "causal_prefix_checks_passed": true,
  "no_model_refit": true,
  "calibration_targets_end": "2020-08-31",
  "assessment_origins_start": "2020-09-01"
}

           model       phase  threshold  average_precision  positive_origin_share  positive_origins  events  detected_events  warning_episodes  false_warning_episodes  event_recall  warning_precision  false_warnings_per_30_at_risk_zip_days  mean_lead_days  median_lead_days  at_risk_zip_days
Dynamic Panel FE calibration          0           0.502525               0.007949               546     186              143               172                      29      0.768817           0.831395                                0.012665        1.188811               1.0             68692
Dynamic Panel FE  assessment          0           0.633050               0.053904              2878     992              784              1179                     395      0.790323           0.664970                                0.221948        1.572704               1.0             53391
         XGBoost calibration          0           0.488719               0.007949               546     186              136               159                      23      0.731183           0.855346                                0.010045        1.154412               1.0             68692
         XGBoost  assessment          0           0.650027               0.053904              2878     992              779               932                     153      0.785282           0.835837                                0.085970        1.331194               1.0             53391
   Random Forest calibration          0           0.496866               0.007949               546     186              146               181                      35      0.784946           0.806630                                0.015286        1.164384               1.0             68692
   Random Forest  assessment          0           0.652963               0.053904              2878     992              774              1044                     270      0.780242           0.741379                                0.151711        1.457364               1.0             53391

先看事件数量与分布，再看assessment行。AP的参考是positive_origin_share，不是0.5。Lead time只描述检出的事件，不能忽略漏报。报警阈值只在4—8月选择；9—12月不调阈值。事件起点为第二次满足条件的确认日，不是生物学真实爆发日。误报预算按非活动、可评分的ZIP-days归一化。

如果最小阈值0已满足宽松的1/30误报预算，就保留0，不根据assessment寻找更好的阈值。无事件的地区也必须保留。后续先审查事件例子与敏感性，再决定冻结方案；不把研究定义当成官方疫情判定。

注意：确认日需要连续两天，因此提前1天的成功预警可能已有首个异常日作为输入。它不是在任何异常出现前的预警；也不能解释为已验证感染爆发。事件基线采用28天移动均值，持续缓慢上升可能被适应性基线吸收，数值依赖该代理定义。校准origin截至8/28，使三天目标不跨9/1。
