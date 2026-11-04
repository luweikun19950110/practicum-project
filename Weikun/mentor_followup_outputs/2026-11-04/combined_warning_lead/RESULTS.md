# Combination warning lead time: three and seven day horizons

| rule         |   horizon_days |   eligible_events |   detected_events |   warning_episodes |   false_warning_episodes |   event_detection_rate |   warning_precision |   mean_lead_days |   median_lead_days |   false_warnings_per_30_at_risk_zip_days |   at_risk_zip_days |
|:-------------|---------------:|------------------:|------------------:|-------------------:|-------------------------:|-----------------------:|--------------------:|-----------------:|-------------------:|-----------------------------------------:|-------------------:|
| DP           |              3 |              1039 |               820 |               1229 |                      409 |                0.78922 |             0.66721 |          1.31951 |                  1 |                                  0.22965 |              53430 |
| XGBoost      |              3 |              1039 |               761 |                918 |                      157 |                0.73244 |             0.82898 |          1.13535 |                  1 |                                  0.08815 |              53430 |
| RF           |              3 |              1039 |               831 |               1097 |                      266 |                0.79981 |             0.75752 |          1.23827 |                  1 |                                  0.14935 |              53430 |
| DP + XGBoost |              3 |              1039 |               826 |               1241 |                      415 |                0.795   |             0.66559 |          1.32567 |                  1 |                                  0.23302 |              53430 |
| DP + RF      |              3 |              1039 |               840 |               1294 |                      454 |                0.80847 |             0.64915 |          1.34881 |                  1 |                                  0.25491 |              53430 |
| XGBoost + RF |              3 |              1039 |               833 |               1107 |                      274 |                0.80173 |             0.75248 |          1.2413  |                  1 |                                  0.15385 |              53430 |
| All three    |              3 |              1039 |               840 |               1295 |                      455 |                0.80847 |             0.64865 |          1.35    |                  1 |                                  0.25547 |              53430 |
| DP           |              7 |              1125 |               918 |               1614 |                      696 |                0.816   |             0.56877 |          2.02832 |                  1 |                                  0.39079 |              53430 |
| XGBoost      |              7 |              1125 |               793 |                927 |                      134 |                0.70489 |             0.85545 |          1.32787 |                  1 |                                  0.07524 |              53430 |
| RF           |              7 |              1125 |               889 |               1158 |                      269 |                0.79022 |             0.7677  |          1.64904 |                  1 |                                  0.15104 |              53430 |
| DP + XGBoost |              7 |              1125 |               925 |               1632 |                      707 |                0.82222 |             0.56679 |          2.03459 |                  1 |                                  0.39697 |              53430 |
| DP + RF      |              7 |              1125 |               949 |               1711 |                      762 |                0.84356 |             0.55465 |          2.11802 |                  1 |                                  0.42785 |              53430 |
| XGBoost + RF |              7 |              1125 |               893 |               1170 |                      277 |                0.79378 |             0.76325 |          1.65957 |                  1 |                                  0.15553 |              53430 |
| All three    |              7 |              1125 |               949 |               1715 |                      766 |                0.84356 |             0.55335 |          2.11275 |                  1 |                                  0.4301  |              53430 |

## Same events detected under both horizons

| rule         |   events_detected_by_both |   mean_lead_3 |   mean_lead_7 |   mean_paired_difference |   earlier_7day |   same_lead |   later_7day |
|:-------------|--------------------------:|--------------:|--------------:|-------------------------:|---------------:|------------:|-------------:|
| DP           |                       820 |       1.31951 |       1.74512 |                  0.42561 |            135 |         669 |           16 |
| XGBoost      |                       761 |       1.13535 |       1.15375 |                  0.0184  |              7 |         753 |            1 |
| RF           |                       831 |       1.23827 |       1.39952 |                  0.16125 |             56 |         771 |            4 |
| DP + XGBoost |                       826 |       1.32567 |       1.75908 |                  0.43341 |            139 |         670 |           17 |
| DP + RF      |                       840 |       1.34881 |       1.81667 |                  0.46786 |            157 |         665 |           18 |
| XGBoost + RF |                       833 |       1.2413  |       1.40576 |                  0.16447 |             58 |         770 |            5 |
| All three    |                       840 |       1.35    |       1.81429 |                  0.46429 |            158 |         663 |           19 |

{
  "forecast_dates": "2020-09-01 to 2020-12-24,115daily dates",
  "regions": 585,
  "combination": "OR on same ZIP/date before common7daycooldown andone-to-one earliest-eventmatching",
  "thresholds": "Retain Notebook37 calibration per model and horizon; all0",
  "lead": "Rule-defined event start minus matched alert date,onlydetected events",
  "event_rule": "Unchanged Notebook27 three-day smoothing;secondqualifyingday start",
  "warning_horizons": [
    3,
    7
  ],
  "comparability": "Different detected subsets. Same-detected-event timing comparison saved separately. Nativeeligible eventdenominators1039vs1125. Do notmix oldSep1-Dec28 three-day figures.",
  "new_model_training": false,
  "verified_individuals_reproduce_notebook37": true
}

Read lead with detection and false warnings, never alone. Longer matching range mechanically permits longer leads. Mean lead uses different detected subsets. Not a demonstration of warning before the first abnormal day or real-time onset availability. 2020 exploratory validation, no untouched test or significance claim.