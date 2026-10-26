# Frozen feature combinations: 30 vs 60-day windows

Feature membership is taken unchanged from the three-method Notebook 15 run. All 585 regions, forecast origins and horizons match the 30-day comparison. Only the rolling parameter training window changes to 60 days. Weekly refits still use only outcomes dated at or before each fit date. No feature search and no 2022-2023 test evaluation.

## Later-2021 validation

| Window | Method | Columns | MAE | RMSE | Bias |
|---|---|---:|---:|---:|---:|
| 30 | BACKWARD | 21 | 1.178472 | 2.018709 | -0.011035 |
| 30 | FORWARD | 9 | 1.171625 | 2.013175 | -0.038075 |
| 30 | FULL | 34 | 1.180819 | 2.023986 | 0.021619 |
| 30 | STEPWISE | 9 | 1.171625 | 2.013175 | -0.038075 |
| 60 | BACKWARD | 21 | 1.159535 | 2.003030 | -0.022042 |
| 60 | FORWARD | 9 | 1.164881 | 2.003248 | -0.027737 |
| 60 | FULL | 34 | 1.159097 | 2.008269 | -0.000615 |
| 60 | STEPWISE | 9 | 1.164881 | 2.003248 | -0.027737 |

Forward and Stepwise produced identical lists; their forecasts and scores are identical, not independent replications. Column counts include six weekday controls; ZIP FE are additional. Check horizon-specific results and paired differences, not only average ranks.

The lists were selected on early 2021 with a 30-day model, so this asks whether those same lists remain useful at 60 days, not which features would be selected afresh at 60 days. Both parts of 2021 were examined in earlier work. This is exploratory sensitivity analysis and cannot establish a final independent winner. HAC tests and pointwise block CIs do not account fully for prior selection; Holm correction across 20 comparisons does not repair that bias. Positive delta MAE favors the candidate named in paired_comparisons.csv.
