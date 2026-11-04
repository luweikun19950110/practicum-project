# 分别以三个模型为起点

所有组合采用OR规则：同一ZIP、同一预报日期任一个模型报警就报警。随后重新执行统一7天冷却期和一对一事件匹配。

| starting_model   | added_models                     |   event_detection_pct |   correct_warning_pct |   detection_change_pp |   precision_change_pp |   detected_events |   false_warnings |   extra_events |   extra_false_warnings |
|:-----------------|:---------------------------------|----------------------:|----------------------:|----------------------:|----------------------:|------------------:|-----------------:|---------------:|-----------------------:|
| Dynamic Panel FE | None                             |                78.603 |                67.914 |                 0     |                 0     |               889 |              420 |              0 |                      0 |
| Dynamic Panel FE | XGBoost                          |                79.134 |                67.752 |                 0.531 |                -0.163 |               895 |              426 |              6 |                      6 |
| Dynamic Panel FE | Random Forest                    |                80.46  |                66.086 |                 1.857 |                -1.829 |               910 |              467 |             21 |                     47 |
| Dynamic Panel FE | XGBoost + Random Forest          |                80.46  |                66.038 |                 1.857 |                -1.877 |               910 |              468 |             21 |                     48 |
| XGBoost          | None                             |                72.944 |                83.671 |                 0     |                 0     |               825 |              161 |              0 |                      0 |
| XGBoost          | Dynamic Panel FE                 |                79.134 |                67.752 |                 6.189 |               -15.92  |               895 |              426 |             70 |                    265 |
| XGBoost          | Random Forest                    |                79.576 |                76.142 |                 6.631 |                -7.529 |               900 |              282 |             75 |                    121 |
| XGBoost          | Dynamic Panel FE + Random Forest |                80.46  |                66.038 |                 7.515 |               -17.634 |               910 |              468 |             85 |                    307 |
| Random Forest    | None                             |                79.31  |                76.667 |                 0     |                 0     |               897 |              273 |              0 |                      0 |
| Random Forest    | Dynamic Panel FE                 |                80.46  |                66.086 |                 1.149 |               -10.581 |               910 |              467 |             13 |                    194 |
| Random Forest    | XGBoost                          |                79.576 |                76.142 |                 0.265 |                -0.525 |               900 |              282 |              3 |                      9 |
| Random Forest    | Dynamic Panel FE + XGBoost       |                80.46  |                66.038 |                 1.149 |               -10.629 |               910 |              468 |             13 |                    195 |

变化单位为百分点。extra_events是净变化，组合冷却期可能使部分原有检出丢失，不能将净变化解释为纯新增覆盖。所有方案采用同一1131个事件、2020年9—12月探索性验证。不是重新训练融合模型，也不是证明统计显著改善。加入另外两个的结果来自Notebook34同一规则的三模型OR结果。