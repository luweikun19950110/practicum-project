# Individual backward feature selection

Common regions: 585; window 30 days, weekly refits, horizons 1/2/3. Initial columns 34, retained 21, including six weekday controls. ZIP FE are additional. No 2022-2023 test data scored.

Single numeric features were considered for deletion separately. Month dummies remain a single categorical unit. Weekday and region FE are forced. Every accepted removal is followed by a new round of refits. Stop if the best deletion fails to improve early-2021 mean MAE by at least 0.1%. P-values do not choose deletions. This threshold is a declared heuristic, not a statistical guarantee.

The feature list is frozen using January-June 2021 only, then checked July-December 2021. Parameters in that later period may use prior observed outcomes when refitting, as in the rolling forecast design. These periods have been examined in earlier work: neither results nor p-values are confirmatory. Adaptive selection biases inference; Holm adjustment over examined contrasts does not repair that bias. CIs are pointwise date-block intervals from fixed forecasts, not full-pipeline resampling.

## Retained columns

- cases_today
- cases_lag_1
- cases_lag_7
- cases_lag_14
- cases_mean_7d
- case_std_7d
- case_std_14d
- case_acceleration
- case_jerk
- case_rate_today_per_100k
- case_rate_7d_per_100k
- case_rate_14d_per_100k
- no_previous_observed_case
- nj_covid_pressure_7d
- nj_covid_pressure_14d
- target_weekday_2
- target_weekday_3
- target_weekday_4
- target_weekday_5
- target_weekday_6
- target_weekday_7

## Removed columns

- cases_mean_14d
- days_since_last_observed_case_censored
- target_month_2
- target_month_3
- target_month_4
- target_month_5
- target_month_6
- target_month_7
- target_month_8
- target_month_9
- target_month_10
- target_month_11
- target_month_12

Start with selection_path.csv, selected_features.json and full_vs_selected_by_horizon.csv. candidate_trials.csv records every attempted deletion. Features omitted temporarily for training rank are logged separately; this is not selection. Static FE-absorbed features remain candidates for tree models. Pressure removal, if selected, does not prove it lacks value for other estimators, forecast horizons or warning outputs.
