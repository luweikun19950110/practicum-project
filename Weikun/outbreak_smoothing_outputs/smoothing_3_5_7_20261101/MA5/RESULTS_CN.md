# 病例激增任务v1：探索性结果

{
  "regions": 585,
  "origins": 243,
  "events_2020": 1755,
  "zips_with_events": 492,
  "qualifying_zip_days": 16138,
  "matched_targets_verified": true,
  "causal_prefix_checks_passed": true,
  "no_model_refit": true,
  "calibration_targets_end": "2020-08-31",
  "assessment_origins_start": "2020-09-01"
}

           model       phase  threshold  average_precision  positive_origin_share  positive_origins  events  detected_events  warning_episodes  false_warning_episodes  event_recall  warning_precision  false_warnings_per_30_at_risk_zip_days  mean_lead_days  median_lead_days  at_risk_zip_days
Dynamic Panel FE calibration          0           0.505713               0.008960               615     209              157               184                      27      0.751196           0.853261                                0.011800        1.146497               1.0             68642
Dynamic Panel FE  assessment          0           0.612649               0.057126              3125    1082              892              1304                     412      0.824399           0.684049                                0.225943        1.511211               1.0             54704
         XGBoost calibration          0           0.498821               0.008960               615     209              149               174                      25      0.712919           0.856322                                0.010926        1.107383               1.0             68642
         XGBoost  assessment          0           0.635929               0.057126              3125    1082              863              1024                     161      0.797597           0.842773                                0.088293        1.289687               1.0             54704
   Random Forest calibration          0           0.505628               0.008960               615     209              160               193                      33      0.765550           0.829016                                0.014423        1.131250               1.0             68642
   Random Forest  assessment          0           0.635364               0.057126              3125    1082              894              1168                     274      0.826248           0.765411                                0.150263        1.434004               1.0             54704

先看事件数量与分布，再看assessment行。AP的参考是positive_origin_share，不是0.5。Lead time只描述检出的事件，不能忽略漏报。报警阈值只在4—8月选择；9—12月不调阈值。事件起点为第二次满足条件的确认日，不是生物学真实爆发日。误报预算按非活动、可评分的ZIP-days归一化。

如果最小阈值0已满足宽松的1/30误报预算，就保留0，不根据assessment寻找更好的阈值。无事件的地区也必须保留。后续先审查事件例子与敏感性，再决定冻结方案；不把研究定义当成官方疫情判定。

注意：确认日需要连续两天，因此提前1天的成功预警可能已有首个异常日作为输入。它不是在任何异常出现前的预警；也不能解释为已验证感染爆发。事件基线采用28天移动均值，持续缓慢上升可能被适应性基线吸收，数值依赖该代理定义。校准origin截至8/28，使三天目标不跨9/1。
