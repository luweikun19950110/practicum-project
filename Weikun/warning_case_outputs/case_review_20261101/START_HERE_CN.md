# Notebook31：预警案例与漏报诊断

## 先看什么
1. selected_cases.csv：三个例子的ZIP与日期。
2. figures/01_shared_success.png：三个模型都成功检出的事件。
3. figures/02_xgb_miss_other_detect.png：XGBoost漏报、其他模型检出的事件。
4. figures/03_xgb_false_warning.png：XGBoost发出预警，但未来3天无事件确认。
5. missed_reason_summary.csv：全部漏报的规则层面原因。

## 图怎么读
上图给出真实病例、真实3天均值及事后可计算的实际阈值，星号为事件确认日，黑虚线为选定预测日。未来真实值仅用于事后核对。红点仅表示当日满足条件，事件还需要连续两天和重置规则。下图比较从同一个日期出发的未来1/2/3天真实病例路径和预测路径。

## 案例选择
按结果分组后，取真实MA3中位数附近案例，避免只选最好看的图。这仍是解释性例子，不代表总体表现。成功/漏报评价用整个事件前1—3天窗口，而图中只展示一个共同预测日。

                 case   zip forecast_origin event_date  pool_size
       shared_success 07755      2020-11-14 2020-11-16        748
xgb_miss_other_detect 07869      2020-09-25 2020-09-26        153
    xgb_false_warning 08829      2020-11-27        NaT        161

## 所有漏报的诊断
           model  Above-threshold opportunity blocked by cooldown  No eligible score exceeded threshold
Dynamic Panel FE                                               84                                   158
         XGBoost                                               27                                   279
   Random Forest                                               49                                   185

No eligible score exceeded threshold：事件前三天没有可预警、且风险分数超过现有阈值的机会。Above-threshold opportunity blocked by cooldown：虽然出现满足分数条件的机会，但过去7天已经发过预警，冷却规则阻止再次报警。这解释的是现有报警规则的行为，不是疫情机制或模型因果归因。

误报也可能只是时间没有对上：未来3天没有确认，不能解释为之后永远没有病例上升。各例子的三个模型是否实际发报警、是否处于冷却期、风险分数是多少，请看case_model_diagnostics.csv。主事件定义与模型都不变，没有使用Notebook30的预算阈值。
