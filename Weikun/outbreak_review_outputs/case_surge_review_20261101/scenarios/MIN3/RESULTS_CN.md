# 病例激增任务v1：探索性结果

{
  "regions": 585,
  "origins": 243,
  "events_2020": 2548,
  "zips_with_events": 538,
  "qualifying_zip_days": 17789,
  "matched_targets_verified": true,
  "causal_prefix_checks_passed": true,
  "no_model_refit": true,
  "calibration_targets_end": "2020-08-31",
  "assessment_origins_start": "2020-09-01"
}

           model       phase  threshold  average_precision  positive_origin_share  positive_origins  events  detected_events  warning_episodes  false_warning_episodes  event_recall  warning_precision  false_warnings_per_30_at_risk_zip_days  mean_lead_days  median_lead_days  at_risk_zip_days
Dynamic Panel FE calibration          0           0.452856               0.021082              1395     474              381               434                      53      0.803797           0.877880                                0.024029        1.041995               1.0             66171
Dynamic Panel FE  assessment          0           0.503618               0.084562              4319    1483             1158              1716                     558      0.780850           0.674825                                0.327753        1.305699               1.0             51075
         XGBoost calibration          0           0.460485               0.021082              1395     474              382               420                      38      0.805907           0.909524                                0.017228        1.036649               1.0             66171
         XGBoost  assessment          0           0.543063               0.084562              4319    1483             1161              1339                     178      0.782873           0.867065                                0.104552        1.119724               1.0             51075
   Random Forest calibration          0           0.457832               0.021082              1395     474              378               434                      56      0.797468           0.870968                                0.025389        1.052910               1.0             66171
   Random Forest  assessment          0           0.545267               0.084562              4319    1483             1208              1500                     292      0.814565           0.805333                                0.171512        1.194536               1.0             51075

先看事件数量与分布，再看assessment行。AP的参考是positive_origin_share，不是0.5。Lead time只描述检出的事件，不能忽略漏报。报警阈值只在4—8月选择；9—12月不调阈值。事件起点为第二次满足条件的确认日，不是生物学真实爆发日。误报预算按非活动、可评分的ZIP-days归一化。

如果最小阈值0已满足宽松的1/30误报预算，就保留0，不根据assessment寻找更好的阈值。无事件的地区也必须保留。后续先审查事件例子与敏感性，再决定冻结方案；不把研究定义当成官方疫情判定。

注意：确认日需要连续两天，因此提前1天的成功预警可能已有首个异常日作为输入。它不是在任何异常出现前的预警；也不能解释为已验证感染爆发。事件基线采用28天移动均值，持续缓慢上升可能被适应性基线吸收，数值依赖该代理定义。校准origin截至8/28，使三天目标不跨9/1。
