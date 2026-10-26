# Validation-only training-window comparison

Selected starting window for the pressure model: **30 days**, using mean validation MAE across horizons 1/2/3. No test forecasts were generated.

| Model | Window days | Mean MAE | Mean RMSE | Rank within model |
|---|---:|---:|---:|---:|
| Dynamic panel FE | 30 | 1.133520 | 1.987143 | 1 |
| Dynamic panel FE | 60 | 1.143925 | 1.990922 | 2 |
| Dynamic panel FE | 90 | 1.158000 | 2.007207 | 3 |
| Dynamic panel FE | 180 | 1.188397 | 2.027721 | 4 |
| Dynamic panel FE + pressure | 30 | 1.127330 | 1.950848 | 1 |
| Dynamic panel FE + pressure | 60 | 1.129681 | 1.953936 | 2 |
| Dynamic panel FE + pressure | 90 | 1.135229 | 1.967213 | 3 |
| Dynamic panel FE + pressure | 180 | 1.151396 | 1.990443 | 4 |

Both variants were fitted/scored on the same matched region set, and every candidate used identical validation rows. Candidate runs also save all-region reference metrics, but rankings use the matched-cohort results only. Simple benchmark predictions are unchanged across windows. The primary model is selected by a declared MAE rule; the no-pressure model ranking is also retained. Do not compare each model at a different window to isolate a pressure effect.

The choice is conditional on this validation period and the retrospective recorded-onset outcome. Existing onset-missingness and ZIP/ZCTA assumptions still apply. Test results inspected earlier are not newly untouched evidence.
