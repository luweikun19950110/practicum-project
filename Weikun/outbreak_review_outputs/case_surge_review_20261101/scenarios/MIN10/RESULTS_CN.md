# 病例激增任务v1：探索性结果

{
  "regions": 585,
  "origins": 243,
  "events_2020": 1030,
  "zips_with_events": 374,
  "qualifying_zip_days": 7488,
  "matched_targets_verified": true,
  "causal_prefix_checks_passed": true,
  "no_model_refit": true,
  "calibration_targets_end": "2020-08-31",
  "assessment_origins_start": "2020-09-01"
}

           model       phase  threshold  average_precision  positive_origin_share  positive_origins  events  detected_events  warning_episodes  false_warning_episodes  event_recall  warning_precision  false_warnings_per_30_at_risk_zip_days  mean_lead_days  median_lead_days  at_risk_zip_days
Dynamic Panel FE calibration          0           0.461844               0.002351               165      57               43                45                       2      0.754386           0.955556                                0.000855        1.000000               1.0             70189
Dynamic Panel FE  assessment          0           0.559344               0.031127              1921     657              500               672                     172      0.761035           0.744048                                0.083610        1.252000               1.0             61715
         XGBoost calibration          0           0.448181               0.002351               165      57               40                46                       6      0.701754           0.869565                                0.002565        1.000000               1.0             70189
         XGBoost  assessment          0           0.551975               0.031127              1921     657              463               558                      95      0.704718           0.829749                                0.046180        1.146868               1.0             61715
   Random Forest calibration          0           0.462025               0.002351               165      57               45                52                       7      0.789474           0.865385                                0.002992        1.044444               1.0             70189
   Random Forest  assessment          0           0.543116               0.031127              1921     657              508               670                     162      0.773212           0.758209                                0.078749        1.248031               1.0             61715

先看事件数量与分布，再看assessment行。AP的参考是positive_origin_share，不是0.5。Lead time只描述检出的事件，不能忽略漏报。报警阈值只在4—8月选择；9—12月不调阈值。事件起点为第二次满足条件的确认日，不是生物学真实爆发日。误报预算按非活动、可评分的ZIP-days归一化。

如果最小阈值0已满足宽松的1/30误报预算，就保留0，不根据assessment寻找更好的阈值。无事件的地区也必须保留。后续先审查事件例子与敏感性，再决定冻结方案；不把研究定义当成官方疫情判定。

注意：确认日需要连续两天，因此提前1天的成功预警可能已有首个异常日作为输入。它不是在任何异常出现前的预警；也不能解释为已验证感染爆发。事件基线采用28天移动均值，持续缓慢上升可能被适应性基线吸收，数值依赖该代理定义。校准origin截至8/28，使三天目标不跨9/1。
