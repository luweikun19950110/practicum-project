# Compact FE model: pressure contribution and simple benchmarks

Same frozen feature list, 585 regions, 60-day training, weekly refits, direct days 1/2/3. Remove only 7-day pressure; fit again, preserving weekday controls, ZIP FE and local cases today/7-day mean. No reselection. Include persistence and previous-week target weekday benchmarks. Full/Backward are context from Notebook 16, not new searches.

## Later-2021 validation

| Model | Mean MAE | Mean RMSE | Bias |
|---|---:|---:|---:|
| BACKWARD_REFERENCE | 1.159535 | 2.003030 | -0.022042 |
| COMPACT_NO_PRESSURE | 1.127037 | 2.008233 | -0.189913 |
| COMPACT_WITH_PRESSURE | 1.164881 | 2.003248 | -0.027737 |
| FULL_REFERENCE | 1.159097 | 2.008269 | -0.000615 |
| PERSISTENCE | 1.346114 | 2.388163 | -0.069320 |
| SEASONAL_NAIVE | 1.383413 | 2.548214 | -0.302397 |

## Paired overall comparisons

Positive difference favors the compact model with pressure.

| Baseline | Delta MAE | 95% pointwise CI | Holm p |
|---|---:|---|---:|
| COMPACT_NO_PRESSURE | -0.037844 | [-0.068026, -0.006821] | 0.0923 |
| PERSISTENCE | 0.181233 | [0.143007, 0.210347] | 1.665e-18 |
| SEASONAL_NAIVE | 0.218532 | [0.153084, 0.285012] | 4.904e-07 |

Monthly results group by forecast-origin month; regional case-volume strata use 2020 only. Regional/monthly comparisons are descriptive, not additional independent hypothesis tests. No spatial Moran test without real spatial weights. These results are exploratory after earlier selection/window inspection, not final-test or causal evidence. 2022-2023 test data are not evaluated. Intervals are pointwise date-block resampling of fixed forecasts; no full-pipeline uncertainty.
