# 本轮实际发现

- 移除本地病例历史后，MAE上升：Dynamic Panel **23.55%**、XGBoost **3.46%**、RF **88.20%**。这是在其他输入（含pressure和ZIP身份）保留时的额外贡献，不是所有模型对本地历史的绝对依赖程度。
- 7天HAC、九次比较Holm调整下，这三项的p值分别约0.000050、0.000000071、0.000603。但改用28天HAC后，DP和RF调整p值为0.057和0.168，XGBoost为0.0037。因此DP/RF的显著性对相关结构假设敏感，不要只选一个最漂亮的p值汇报。
- pressure移除后的MAE变化：DP **−0.93%**、XGBoost **+0.26%**、RF **−0.31%**，所有区间跨0，没有稳定显著证据。小幅变化不能证明pressure完全无用，也不改变主模型必须保留pressure的设定。
- calendar移除后的MAE变化约 **+0.57% / +0.32% / −0.42%**，区间也跨0，证据较弱。
- 两个树模型训练时最重视7天/14天病例平均值。它们高度相关，单个变量的重要性可能被相互分担。训练重要性和移除后的验证贡献是不同概念。
- DP的7天pressure系数在105个“训练日期×horizon”估计中都为正，14天系数符号更不稳定。这是有其他特征控制时的描述性关联，不是因果，也不是显著性证明。
- 数量误差和方向准确率不一定同步：例如移除本地历史后DP的数量MAE变差，但方向准确率反而提高。需要结合flat类别召回率看，不能用方向总体准确率单独选择模型。

# 先看什么

1. `group_ablation_summary.csv`：最重要的组移除对照。正的 delta 表示移除后误差增大，保留该组有帮助；负值表示移除后更好。
2. `figures/03_group_ablation_intervals.png`：改善幅度和点对点95%日期分块区间。
3. `group_ablation_by_horizon.csv`、`figures/04_group_contribution_by_month.png`：未来1/2/3天和不同月份的效果是否一致。
4. `training_importance_summary.csv`、`figures/01_tree_training_importance.png`：模型训练时主要用了哪些变量。XGBoost和RF用的指标不同，数值不能横向比较。
5. `dp_coefficient_stability.csv`、`figures/02_dp_coefficient_stability.png`：Dynamic Panel系数随训练日期如何变化，不是因果估计。
6. `high_correlation_pairs.csv`：哪些变量提供相似信息。

## p值怎么读

- `p_HAC7_raw`：平均配对预测误差差异的原始探索性p值。
- `p_Holm`：同时做9个主比较后，调整的p值。优先看这一列。
- `p_HAC28_Holm_sensitivity`：采用更长时间相关范围后的敏感性检查。
- 先看误差差异有多大，再看区间和p值。p<0.05不说明改善很大，也不说明因果；p>=0.05不证明完全无用。
- 区间是日期分块bootstrap的点对点95%区间，p值是HAC并经过Holm调整，接近阈值时两者可能给出不同结论。
- 所有结果来自已看过的2020验证期，只能作为探索性证据。

## 这次不改变什么

主模型仍使用全部34个候选特征和ZIP身份，包括两个pressure。移除只用于诊断。没有重新选择最终模型，没有运行2021–2023，也没有改outbreak或trajectory定义。没有将训练重要性当作预测效果的证明。

Notebook默认读取已保存结果；无需再次训练。完整重跑会训练945个模型，耗时较长。大型预测文件保留在本地输出文件夹，Git默认忽略这些诊断NPZ。
