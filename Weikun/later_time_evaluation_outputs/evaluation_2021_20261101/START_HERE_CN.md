# Notebook32：2021年整体及Delta/Omicron时间段比较



## 先看这三项

1. focus_period_scorecard.csv：2021整体、Delta相关夏季窗口和12月Omicron出现窗口的模型成绩。

2. figures/02_focus_period_comparison.png：重点时期的MAE、AP、检出率和预警正确比例。

3. figures/01_2021_errors_and_activity.png：全年病例活动与预测误差走势。



## 如何划分

全年origin为2021年1月1日—12月28日，共362天，585地区，211770条三天路径。所有target都在2021年内。Delta相关阶段采用7月1日—9月27日的预测，目标截至9月30日；Omicron出现阶段采用12月1日—28日的预测，目标截至12月31日。

CDC将美国主要病例激增概括为Delta2021年7—9月、Omicron2021年12月—2022年1月。我们只看2021，所以12月不能代表完整Omicron波，且月初仍有Delta传播。这只是全国日历背景，不是每条NJ病例的变异株标记。

CDC source: https://www.cdc.gov/mmwr/volumes/71/wr/mm7106a4.htm



## 结果

           model                  period  origins  trajectory_MAE     RMSE  direction_agreement       AP  events  event_recall  warning_precision  mean_lead_days  recall_at_least_2_days
Dynamic Panel FE               Full 2021      362        1.107401 1.901808             0.362837 0.518445    2752      0.805596           0.732166        1.237709                0.157703
Dynamic Panel FE Delta-associated period       89        0.903360 1.335991             0.320791 0.521343     791      0.780025           0.761728        1.141005                0.092288
Dynamic Panel FE       Omicron emergence       28        2.395511 3.894977             0.406471 0.591606     475      0.840000           0.585903        1.553885                0.357895
         XGBoost               Full 2021      362        1.098323 1.939047             0.307319 0.528637    2752      0.763808           0.827885        1.107517                0.074855
         XGBoost Delta-associated period       89        0.878156 1.355764             0.297820 0.520073     791      0.729456           0.825465        1.067591                0.042984
         XGBoost       Omicron emergence       28        2.305367 4.110713             0.407387 0.626145     475      0.812632           0.844639        1.142487                0.107368
   Random Forest               Full 2021      362        1.090408 1.900485             0.295056 0.544281    2752      0.804506           0.773315        1.200090                0.139535
   Random Forest Delta-associated period       89        0.890599 1.348418             0.289504 0.536163     791      0.787611           0.764417        1.181380                0.117573
   Random Forest       Omicron emergence       28        2.285973 3.964947             0.389499 0.644166     475      0.837895           0.772816        1.329146                0.237895



## 可汇报的发现

Full 2021: MAE最低为Random Forest（1.090），AP最高为Random Forest（0.544）。观察到的排名不等于显著优越。

Delta-associated period: MAE最低为XGBoost（0.878），AP最高为Random Forest（0.536）。观察到的排名不等于显著优越。

Omicron emergence: MAE最低为Random Forest（2.286），AP最高为Random Forest（0.644）。观察到的排名不等于显著优越。



## 保持不变

34个候选特征（含两个pressure）、585个地区、60天滚动训练、每7天重训、未来1/2/3天直接预测。只复用已生成的2021预测，不额外训练。预警沿用Notebook27事件定义及2020校准阈值0，没有budget分析。



## 如何解释

Delta窗口中XGBoost较Dynamic Panel的MAE改善约0.0252例，7天时间块95%区间约[0.0126,0.0403]。12月两种树模型较Dynamic Panel的改善区间都跨0，不能仅凭点估计的名次断言更优。这些区间是探索性误差差异区间，不是每日病例预测区间。

比较病例预测与预警指标时分别看：MAE较低不保证AP、检出率、提前量都更好。不同阶段的病例量、事件数量及阳性比例也不同，不能把分数差异全部归因于变异株。

严格方向分为Day3大于/等于/小于Day1，连续点预测很少恰好相等，要结合平稳比例和三类recall。

事件前1—3天的成功预警不保证出现在首个异常之前。冷却规则按全年连续运行，进入一个重点时间段时不重新初始化。

95%CI是模型平均MAE差异的时间块区间，不是每日病例的预测区间。两段时间长度不同，尤其12月只有28个预测日，推断为探索性。

这些年份此前已部分探索，因此称后续时间评估，不称完全未接触的独立测试。2022—2023未纳入本次展示或方案选择。