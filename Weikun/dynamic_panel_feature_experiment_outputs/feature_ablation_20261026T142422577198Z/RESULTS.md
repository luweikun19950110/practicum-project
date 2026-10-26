# NJ feature experiments: validation results

Mean MAE/RMSE average the three horizon-specific scores. Lower is better. This is exploratory validation, not final holdout inference.

| Window | Model | Mean MAE | Mean RMSE | Rank |
|---|---|---:|---:|---:|
| 30 | H0_weekly_mean | 1.096835 | 1.913533 | 1 |
| 30 | D1_acceleration | 1.097616 | 1.914579 | 2 |
| 30 | D2_jerk | 1.097655 | 1.914764 | 3 |
| 30 | H1_history_extended | 1.097805 | 1.915039 | 4 |
| 30 | P1_rich_pressure7 | 1.101561 | 1.902110 | 5 |
| 30 | P2_rich_pressure14 | 1.106624 | 1.908184 | 6 |
| 30 | P0_basic_pressure7 | 1.127330 | 1.950848 | 7 |
| 30 | B0_basic | 1.133520 | 1.987143 | 8 |
| 60 | H0_weekly_mean | 1.088668 | 1.891208 | 1 |
| 60 | P1_rich_pressure7 | 1.088990 | 1.880957 | 2 |
| 60 | D2_jerk | 1.090895 | 1.892660 | 3 |
| 60 | D1_acceleration | 1.090944 | 1.892841 | 4 |
| 60 | H1_history_extended | 1.091228 | 1.893485 | 5 |
| 60 | P2_rich_pressure14 | 1.091891 | 1.886296 | 6 |
| 60 | P0_basic_pressure7 | 1.129681 | 1.953936 | 7 |
| 60 | B0_basic | 1.143925 | 1.990922 | 8 |

## Planned overall comparisons, primary 30-day window

Positive delta means improvement. CIs are pointwise date-block bootstrap intervals. P-values are exploratory HAC tests adjusted across all 64 planned contrasts.

| Comparison | Delta MAE | 95% CI | Raw p | Holm p |
|---|---:|---|---:|---:|
| weekly_mean | 0.036685 | [0.020227, 0.055978] | 7.931e-05 | 0.004679 |
| lag14_and_volatility | -0.000971 | [-0.002298, 0.000960] | 0.2564 | 1 |
| acceleration | 0.000189 | [-0.000015, 0.000431] | 0.1006 | 1 |
| jerk | -0.000039 | [-0.000117, 0.000114] | 0.5613 | 1 |
| pressure7_basic | 0.006190 | [-0.023495, 0.052874] | 0.7642 | 1 |
| pressure7_rich | -0.003906 | [-0.027417, 0.027986] | 0.7871 | 1 |
| pressure14_rich | -0.008969 | [-0.035892, 0.021164] | 0.5442 | 1 |
| pressure14_vs_pressure7 | -0.005063 | [-0.015255, 0.000520] | 0.2208 | 1 |

Inspect metrics_by_quarter, individual horizons, bias, regional distribution and the 60-day sensitivity before retaining a feature. Do not select solely by p<0.05. See METHODS.md for interpretation and inference limits.
