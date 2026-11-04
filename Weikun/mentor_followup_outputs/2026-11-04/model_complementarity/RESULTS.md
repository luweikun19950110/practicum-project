# Three-model complementarity

| actual_class        |   paths |   DP_recall |   XGB_recall |   RF_recall |   at_least_one_correct |   at_least_two_correct |   all_three_correct |   all_three_wrong |
|:--------------------|--------:|------------:|-------------:|------------:|-----------------------:|-----------------------:|--------------------:|------------------:|
| Declining           |   30267 |   0.474345  |   0.475964   |    0.440116 |              0.772425  |             0.452209   |            0.165791 |          0.227575 |
| Exact endpoint-flat |   80714 |   0.0918428 |   0.00377877 |    0        |              0.0937879 |             0.00183363 |            0        |          0.906212 |
| Rising              |   31174 |   0.585552  |   0.564862   |    0.579361 |              0.861808  |             0.597357   |            0.27061  |          0.138192 |

| rule                   |   events |   detected_events |   warning_episodes |   false_warning_episodes |   event_recall |   warning_precision |   false_warnings_per_30_at_risk_zip_days |   mean_lead_days |   median_lead_days |   at_risk_zip_days |
|:-----------------------|---------:|------------------:|-------------------:|-------------------------:|---------------:|--------------------:|-----------------------------------------:|-----------------:|-------------------:|-------------------:|
| Dynamic Panel FE       |     1131 |               889 |               1309 |                      420 |       0.78603  |            0.679144 |                                0.226859  |          1.30484 |                  1 |              55541 |
| XGBoost                |     1131 |               825 |                986 |                      161 |       0.729443 |            0.836714 |                                0.0869628 |          1.13576 |                  1 |              55541 |
| Random Forest          |     1131 |               897 |               1170 |                      273 |       0.793103 |            0.766667 |                                0.147459  |          1.23077 |                  1 |              55541 |
| At least 1 model votes |     1131 |               910 |               1378 |                      468 |       0.804598 |            0.660377 |                                0.252786  |          1.33516 |                  1 |              55541 |
| At least 2 model votes |     1131 |               885 |               1123 |                      238 |       0.782493 |            0.788068 |                                0.128554  |          1.20791 |                  1 |              55541 |
| At least 3 model votes |     1131 |               817 |                963 |                      146 |       0.72237  |            0.84839  |                                0.0788607 |          1.12362 |                  1 |              55541 |

Event overlap among original individual warning systems:

|   models_detecting |   events |     share |
|-------------------:|---------:|----------:|
|                  0 |      153 | 0.135279  |
|                  1 |       93 | 0.0822281 |
|                  2 |      137 | 0.121132  |
|                  3 |      748 | 0.661362  |

Union of correct paths is retrospective coverage, not attainable accuracy without knowing which model is correct. Voting rules are prospective functions of model outputs only. Votes are formed on the same ZIP-date BEFORE applying one shared cooldown and event matching, rather than unioning already-matched warnings. Individual thresholds are retained from original calibration; no new assessment tuning. This is exploratory 2020 analysis. Model votes are correlated; three votes do not constitute three independent pieces of evidence. The min/max model envelope is model disagreement, not a confidence or prediction interval.
