# Three versus seven day warning assessment

| model            |   horizon_days | phase      |   threshold |      AP |   positive_zip_date_share |   forecast_dates |   eligible_events |   detected_events |   warning_episodes |   false_warning_episodes |   event_detection_rate |   warning_precision |   mean_lead_days |   median_lead_days |   false_warnings_per_30_at_risk_zip_days |   at_risk_zip_days |   common_eligible_events |   common_detected_events |   common_event_detection_rate |
|:-----------------|---------------:|:-----------|------------:|--------:|--------------------------:|-----------------:|------------------:|------------------:|-------------------:|-------------------------:|-----------------------:|--------------------:|-----------------:|-------------------:|-----------------------------------------:|-------------------:|-------------------------:|-------------------------:|------------------------------:|
| Dynamic Panel FE |              3 | assessment |           0 | 0.52355 |                   0.05682 |              115 |              1039 |               820 |               1229 |                      409 |                0.78922 |             0.66721 |          1.31951 |                  1 |                                  0.22965 |              53430 |                     1039 |                      820 |                       0.78922 |
| Dynamic Panel FE |              7 | assessment |           0 | 0.369   |                   0.12843 |              115 |              1125 |               918 |               1614 |                      696 |                0.816   |             0.56877 |          2.02832 |                  1 |                                  0.39079 |              53430 |                     1039 |                      917 |                       0.88258 |
| XGBoost          |              3 | assessment |           0 | 0.5442  |                   0.05682 |              115 |              1039 |               761 |                918 |                      157 |                0.73244 |             0.82898 |          1.13535 |                  1 |                                  0.08815 |              53430 |                     1039 |                      761 |                       0.73244 |
| XGBoost          |              7 | assessment |           0 | 0.48608 |                   0.12843 |              115 |              1125 |               793 |                927 |                      134 |                0.70489 |             0.85545 |          1.32787 |                  1 |                                  0.07524 |              53430 |                     1039 |                      792 |                       0.76227 |
| Random Forest    |              3 | assessment |           0 | 0.54338 |                   0.05682 |              115 |              1039 |               831 |               1097 |                      266 |                0.79981 |             0.75752 |          1.23827 |                  1 |                                  0.14935 |              53430 |                     1039 |                      831 |                       0.79981 |
| Random Forest    |              7 | assessment |           0 | 0.48901 |                   0.12843 |              115 |              1125 |               889 |               1158 |                      269 |                0.79022 |             0.7677  |          1.64904 |                  1 |                                  0.15104 |              53430 |                     1039 |                      888 |                       0.85467 |

## Seven minus three

| model            |   detection_change_pp |   common_event_detection_change_pp |   precision_change_pp |   AP_change |   mean_lead_change |   extra_false_warnings |
|:-----------------|----------------------:|-----------------------------------:|----------------------:|------------:|-------------------:|-----------------------:|
| Dynamic Panel FE |               2.67796 |                            9.3359  |              -9.84359 |    -0.15455 |            0.70881 |                    287 |
| XGBoost          |              -2.75461 |                            2.98364 |               2.64716 |    -0.05811 |            0.19252 |                    -23 |
| Random Forest    |              -0.95853 |                            5.48604 |               1.01824 |    -0.05437 |            0.41078 |                      3 |

{
  "regions": 585,
  "common_forecast_dates": 239,
  "calibration_last_forecast_date": "2020-08-24",
  "calibration_targets_end": "2020-08-31",
  "assessment_first_forecast_date": "2020-09-01",
  "assessment_last_forecast_date": "2020-12-24",
  "assessment_dates": 115,
  "common_events": 1039,
  "case_surge_definition": "Original MA3 > 28-earlier-MA3 mean +2SD; sum3>=5; two consecutive days; reset after7 nonqualifying days",
  "warning_horizons": [
    3,
    7
  ],
  "cooldown_days": 7,
  "threshold_rule": "Original fixed nonnegative grid; smallest satisfying calibration false-alert criterion<=1 per30 at-risk ZIPdays",
  "new_model_training": false,
  "causality": "Issued predictions plus actual history through forecast date only; risk uses no future actual values",
  "three_day_risk_reproduced": true,
  "interpretation": "Changing horizon changes label prevalence and matching opportunity. Common-event recall uses intersection of eligible event catalogs; precision uses each native1..H-day matching. No untouched test or significance claim. Onset-date replay does not establish real-time availability."
}

Event definition remains MA3; seven refers to forecast/warning horizon, not seven-day smoothing. Same common daily forecast dates. The original published three-day numbers used a different calibration end date and four extra late-December origins; use the matched values here. Wider event windows make matching easier and change the target; a better recall is not proof of a better same-horizon forecasting model. AP across horizons uses different positive labels. Lead includes detected events only; missed events and false alerts must be considered. Warnings may follow already visible abnormal activity.
