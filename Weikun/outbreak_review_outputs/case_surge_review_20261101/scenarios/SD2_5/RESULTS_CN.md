# 病例激增任务v1：探索性结果

{
  "regions": 585,
  "origins": 243,
  "events_2020": 1657,
  "zips_with_events": 492,
  "qualifying_zip_days": 9918,
  "matched_targets_verified": true,
  "causal_prefix_checks_passed": true,
  "no_model_refit": true,
  "calibration_targets_end": "2020-08-31",
  "assessment_origins_start": "2020-09-01"
}

           model       phase  threshold  average_precision  positive_origin_share  positive_origins  events  detected_events  warning_episodes  false_warning_episodes  event_recall  warning_precision  false_warnings_per_30_at_risk_zip_days  mean_lead_days  median_lead_days  at_risk_zip_days
Dynamic Panel FE calibration          0           0.444752               0.008508               587     198              146               167                      21      0.737374           0.874251                                0.009131        1.034247               1.0             68992
Dynamic Panel FE  assessment          0           0.501292               0.048816              2892     987              791              1175                     384      0.801418           0.673191                                0.194453        1.281922               1.0             59243
         XGBoost calibration          0           0.439233               0.008508               587     198              138               158                      20      0.696970           0.873418                                0.008697        1.043478               1.0             68992
         XGBoost  assessment          0           0.519105               0.048816              2892     987              744               889                     145      0.753799           0.836895                                0.073426        1.096774               1.0             59243
   Random Forest calibration          0           0.445672               0.008508               587     198              148               174                      26      0.747475           0.850575                                0.011306        1.047297               1.0             68992
   Random Forest  assessment          0           0.514346               0.048816              2892     987              788              1049                     261      0.798379           0.751192                                0.132168        1.190355               1.0             59243

先看事件数量与分布，再看assessment行。AP的参考是positive_origin_share，不是0.5。Lead time只描述检出的事件，不能忽略漏报。报警阈值只在4—8月选择；9—12月不调阈值。事件起点为第二次满足条件的确认日，不是生物学真实爆发日。误报预算按非活动、可评分的ZIP-days归一化。

如果最小阈值0已满足宽松的1/30误报预算，就保留0，不根据assessment寻找更好的阈值。无事件的地区也必须保留。后续先审查事件例子与敏感性，再决定冻结方案；不把研究定义当成官方疫情判定。

注意：确认日需要连续两天，因此提前1天的成功预警可能已有首个异常日作为输入。它不是在任何异常出现前的预警；也不能解释为已验证感染爆发。事件基线采用28天移动均值，持续缓慢上升可能被适应性基线吸收，数值依赖该代理定义。校准origin截至8/28，使三天目标不跨9/1。
