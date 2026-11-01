# NJ三天轨迹分析：汇报与下一步

配套：NJ_Trajectory_Analysis_Update.pptx。前9页主讲，后6页备选。沿用浅蓝背景、深蓝标题、蓝/灰/青图表。12张图均由Python从已有模型结果绘制；标题、Key Findings和说明文字可以在PowerPoint中编辑，图是独立PNG。每页备注包含英文讲稿、指标定义和来源。

## 这次汇报要回答什么

不是仅列出“跑了哪些模型”，而是讲清：**同样的预测任务下，模型改善了什么、没有改善什么，以及结论受哪些条件影响。**

当前对比：Dynamic Panel FE、XGBoost、Random Forest。不含SEIR，不新增seasonal naive，不做Pressure去留实验。三模型都保留34个候选特征，包括7/14天Pressure；DP在每个训练窗口使用可识别项，另有地区固定效应。

这是2020年开发/验证的回顾性分析。当前PPT没有新增2021—2023年的预测结果，也不是把之前固定60天训练、只评估5月的结果拿来混用。

## 主讲9页：约5分钟

### 1｜From Case Records to Three-Day Paths（35秒）

**分析问题：数据如何从个人记录变成地区日期面板？**

- 原始2,656,888行，去除完全重复、检查ZIP和日期后，纳入1,040,394条有合格onset信息的记录。
- 按ZIP × onset日期汇总，并补齐日历，得到598 × 1,461 =873,678行。每行是一个地区的一天，与原始个人记录的单位不同。
- 三模型实际比较使用相同585个ZIP。598不表示598个ZIP都进入当前模型比较。
- 60.65%原始记录缺少onset而排除。这些记录**没有被当成0**。补0指有效来源里某个ZIP/日期没有合格记录的组合，依据你确认的来源规则；不能因此说全部感染病例都被完整记录。

可讲：We built a complete NJ region-by-day panel, but missing onset dates remain a major limitation. Every model comparison uses the same585 ZIPs.

### 2｜A Common Rolling Evaluation（35秒）

**分析问题：比较是否公平，是否按时间预测未来？**

- 60天滚动历史、每7天重训、每天预测未来1/2/3天。
- 初始历史2020/3/1—4/29，评分origin为4/30—12/28，让三天目标都落在2020年内。
- 585 ZIP ×243 origins =142,155条三天路径。每条是一个ZIP在一个预测日发出的三个未来日病例数。
- 重训时只纳入已经发生的训练目标；日历天数不等于每个horizon都能使用60个训练样本，尚需历史特征预热和目标成熟。
- 这是按回顾性onset数据做的时间回放；病例当时是否已被录入仍未验证。

可讲：We use one common protocol: sixty days of history, weekly refitting, and a new three-day forecast every day. We compare models on exactly the same paths.

### 3｜Lower Count Error Does Not Mean Better Shape（35秒）

**分析问题：病例数预测更准，是否意味着轨迹更准？**

| 指标 | Dynamic Panel | XGBoost | Random Forest |
|---|---:|---:|---:|
| Trajectory MAE，越低越好 |0.7743|0.7543|0.7519|
| 严格两步shape agreement |12.61%|9.00%|8.38%|

MAE是每条路径三个日误差绝对值的平均，再平均所有路径。Shape要求Day2−Day1、Day3−Day2的正负/零方向都匹配。两者回答的问题不同；连续预测很难恰好输出零变化，严格shape很苛刻。

可讲：Trees slightly improve count MAE, while Dynamic Panel more often matches both movement directions. There is no single winner across every objective.

### 4｜Where Do the MAE Gains Occur?（35秒）

**分析问题：总体改善来自哪些路径？**

- 42.8%的真实路径连续三天均为0。树模型在零路径及endpoint-flat路径上误差更低。
- 对Day1与Day3不同的路径，DP MAE1.2905，XGB1.2966，RF1.2923；树模型没有表现出更低误差。
- 因此不能将整体MAE下降直接讲成“更善于捕捉病例变化/疫情爆发”。
- 图中两个组互不重叠但不穷尽样本；尚有非全零、首尾相等的路径。数量规模也会影响组间MAE。

可讲：Much of the pooled gain comes from low-count or endpoint-flat paths. On changing paths, the tree models do not improve MAE over Dynamic Panel.

### 5｜Performance Changes Across the Year（30秒）

**分析问题：同一模型是否在所有阶段都领先？**

RF在部分Q2最低，XGB在Q3/Q4略低。Q4误差明显上升，但也伴随更高病例规模；不能直接认定模型机制在秋季失效。Q2只包含4/30起的评分日期，不是完整季度。季度排名是描述性比较，没有分别检验每个季度显著性。

可讲：The ranking changes by period, and autumn errors are much larger. This is why we need temporal evaluation beyond one development period.

### 6｜How Clear Are the MAE Differences?（35秒）

**分析问题：小幅改善是否稳定？**

- 横轴是前一个模型相对后一个模型的MAE减少量，正数有利于前者。
- XGB相对DP减少0.0200，RF相对DP减少0.0224病例。7天日期块bootstrap的95%区间位于0右边。
- RF相对XGB只减少0.0024，区间跨0；HAC检验经3个预定MAE比较的Holm校正后p=0.675。
- 因而不能声称RF明确优于XGB。区间是探索性、逐项区间，不是未来预测区间；p值针对预测损失差异，不是特征系数。

可讲：Both tree models show small MAE gains over Dynamic Panel in this period. The difference between Random Forest and XGBoost is much less clear.

### 7｜Direction Accuracy Depends on the Rule（35秒）

**分析问题：更高的accuracy有没有实际信息？**

方向用(Day3−Day1)/2定义；允许±0.5或±1病例/天为flat是敏感性分析。当阈值为1时，约90.7%样本实际属于flat，始终预测flat也可得约90.7%总accuracy。Balanced accuracy是上升/下降/平稳各类召回率的平均，此时约33—34%。

所以保留严格零阈值的既有定义，并同时报告类别构成和敏感性；不能挑最漂亮的90.7%当作已实现的有效捕捉率。

可讲：Overall direction accuracy rises when we widen the flat category, but an always-flat reference improves by almost the same amount. Class balance changes the interpretation.

### 8｜Geographic Error Remains（30秒）

**分析问题：预测误差还有没有地理聚集？**

RF平均Residual Moran's I在三个horizon较低，但这是描述性结果，不是已经检验其显著优于别的模型。正的I表示附近地区误差倾向同号；不能说明感染由某个地区传到另一个地区。

8-neighbor是给每个地区选最近8个地理邻居，对称合并后有的地区会超过8个，并非只看8个ZIP。使用地理位置权重，不是通勤权重。进一步细节放备注。

可讲：Random Forest leaves less residual geographic clustering on average, but spatial structure remains. Predictive error and geographic diagnostics both matter.

### 9｜Next: Test Whether These Findings Persist（30秒）

**下一步执行顺序：**

1. 冻结当前3模型、34特征定义、共同地区、60天/每7天规则、三天target和指标，不再根据后续年份挑选更好看的方案。
2. 对2021—2023年做三模型一致的滚动回顾性时间评估，按年、季度、路径类型比较MAE/RMSE/bias、方向/shape、变化量/加速度和空间残差。每次fit的所有训练标签须在fit时已成熟。
3. 因这些年份在早期工作中已经查看过，称“后续时间评估”，不称“完全未接触的最终test”。
4. 最后确定outbreak的事件标签、连续risk score、warning阈值和事件匹配规则，才引入PR-AUC和warning lead time；三天trajectory本身不等于outbreak。

可讲：Next, we will freeze the current comparison and assess whether the findings persist across2021 to2023. After that, we can define and evaluate the outbreak-warning task.

## 备选6页：老师追问时使用

10. **Feature pool：**34=15病例历史+2 Pressure+17日历编码。地区身份额外处理：DP固定效应、XGB类别、RF one-hot。17日历=6星期+11月份，以一个类别为参照。静态人口和通勤数据是2021版本；不能声称动态随年份更新。
11. **Actual vs predicted：**585 ZIP汇总的三天ahead曲线。每点来自新origin，非一次发出的半年预测；地区间误差可以抵消，曲线贴合不是地区准确率。
12. **Same-origin路径：**4/30与12/1两例，横轴1/2/3 day ahead。这是说明预测输出，不是挑两个例子替代整体证据。
13. **变化与加速度：**两步差分分别为Day2−Day1和Day3−Day2；加速度为Day3−2Day2+Day1。数值误差略低与符号匹配率略低并不矛盾。三天未来点不能单独算三阶差分jerk。
14. **RMSE/bias：**DP RMSE最低1.4184；XGB平均偏差最接近0，约+0.004。接近0的bias可能来自正负误差抵消。
15. **Definitions/limits：**区分回顾性和实时可用性、缺失onset与补零、ZIP–ZCTA未验证、探索性比较与正式独立测试。

## 这份PPT可以支持的结论

我们已经完成了统一规则下的三模型分析，并发现：**数量误差、轨迹形状和空间残差的模型排名并不完全一致；总体分数受到零病例路径、疫情阶段和方向定义的影响。**这本身就是完整的数据分析发现，无需把结果包装成已解决预测问题。

目前不能说：模型已能有效提前预警疫情、RF所有指标最好、90.7%意味着有效识别变化、Residual Moran完全消失，或已经完成2021—2023年的当前协议评估。

## 数据来源索引

- 清理统计：workspace `outputs/real_covid_cleaning_20261022/processed/cleaning_manifest.json`，源自Notebook07；病例与地理候选面板来自Notebook09。
- 当前DP：`Weikun/rolling_trajectory_outputs/rolling60_weekly_development_20261027/`。
- 当前XGB：`Weikun/xgboost_trajectory_outputs/xgb60_weekly_development_20261027/`。
- 当前RF及统一比较：`Weikun/random_forest_trajectory_outputs/rf60_weekly_development_20261027/comparison/`。
- 关键CSV：`three_model_overall.csv`、`path_group_comparison.csv`、`quarter_comparison.csv`、`paired_date_block_intervals.csv`、`primary_MAE_HAC_Holm_tests.csv`、`direction_threshold_sensitivity.csv`、`residual_moran_comparison.csv`。

完整英文讲稿和具体数值定义在PPT备注中；Python图的单独PNG在同目录的`figures`子文件夹。
