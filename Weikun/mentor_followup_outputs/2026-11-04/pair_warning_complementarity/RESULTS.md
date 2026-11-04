# Pairwise warning combinations

| rule                                 |   events |   detected_events |   warning_episodes |   false_warning_episodes |   event_recall |   warning_precision |   false_warnings_per_30_at_risk_zip_days |   mean_lead_days |   median_lead_days |   at_risk_zip_days |
|:-------------------------------------|---------:|------------------:|-------------------:|-------------------------:|---------------:|--------------------:|-----------------------------------------:|-----------------:|-------------------:|-------------------:|
| Dynamic Panel FE                     |     1131 |               889 |               1309 |                      420 |       0.78603  |            0.679144 |                                0.226859  |          1.30484 |                  1 |              55541 |
| XGBoost                              |     1131 |               825 |                986 |                      161 |       0.729443 |            0.836714 |                                0.0869628 |          1.13576 |                  1 |              55541 |
| Random Forest                        |     1131 |               897 |               1170 |                      273 |       0.793103 |            0.766667 |                                0.147459  |          1.23077 |                  1 |              55541 |
| Dynamic Panel FE + XGBoost OR        |     1131 |               895 |               1321 |                      426 |       0.791335 |            0.677517 |                                0.2301    |          1.31173 |                  1 |              55541 |
| Dynamic Panel FE + XGBoost AND       |     1131 |               820 |                974 |                      154 |       0.725022 |            0.841889 |                                0.0831818 |          1.12805 |                  1 |              55541 |
| Dynamic Panel FE + Random Forest OR  |     1131 |               910 |               1377 |                      467 |       0.804598 |            0.660857 |                                0.252246  |          1.33407 |                  1 |              55541 |
| Dynamic Panel FE + Random Forest AND |     1131 |               876 |               1101 |                      225 |       0.774536 |            0.79564  |                                0.121532  |          1.19863 |                  1 |              55541 |
| XGBoost + Random Forest OR           |     1131 |               900 |               1182 |                      282 |       0.795756 |            0.761421 |                                0.15232   |          1.23444 |                  1 |              55541 |
| XGBoost + Random Forest AND          |     1131 |               822 |                974 |                      152 |       0.72679  |            0.843943 |                                0.0821015 |          1.13017 |                  1 |              55541 |

## Changes against members

| pair                             | logic   | baseline         |   event_recall_delta_pp |   warning_precision_delta_pp |   detected_events_delta |   false_warnings_delta |   newly_detected_events |   previously_detected_now_missed |
|:---------------------------------|:--------|:-----------------|------------------------:|-----------------------------:|------------------------:|-----------------------:|------------------------:|---------------------------------:|
| Dynamic Panel FE + XGBoost       | OR      | Dynamic Panel FE |                0.530504 |                    -0.162735 |                       6 |                      6 |                       7 |                                1 |
| Dynamic Panel FE + XGBoost       | OR      | XGBoost          |                6.18921  |                   -15.9197   |                      70 |                    265 |                     124 |                               54 |
| Dynamic Panel FE + XGBoost       | AND     | Dynamic Panel FE |               -6.1008   |                    16.2745   |                     -69 |                   -266 |                      54 |                              123 |
| Dynamic Panel FE + XGBoost       | AND     | XGBoost          |               -0.442087 |                     0.517512 |                      -5 |                     -7 |                       2 |                                7 |
| Dynamic Panel FE + Random Forest | OR      | Dynamic Panel FE |                1.85676  |                    -1.82874  |                      21 |                     47 |                      32 |                               11 |
| Dynamic Panel FE + Random Forest | OR      | Random Forest    |                1.14943  |                   -10.581    |                      13 |                    194 |                      60 |                               47 |
| Dynamic Panel FE + Random Forest | AND     | Dynamic Panel FE |               -1.14943  |                    11.6496   |                     -13 |                   -195 |                      47 |                               60 |
| Dynamic Panel FE + Random Forest | AND     | Random Forest    |               -1.85676  |                     2.89737  |                     -21 |                    -48 |                      11 |                               32 |
| XGBoost + Random Forest          | OR      | XGBoost          |                6.6313   |                    -7.52927  |                      75 |                    121 |                      97 |                               22 |
| XGBoost + Random Forest          | OR      | Random Forest    |                0.265252 |                    -0.524535 |                       3 |                      9 |                       4 |                                1 |
| XGBoost + Random Forest          | AND     | XGBoost          |               -0.265252 |                     0.722851 |                      -3 |                     -9 |                       1 |                                4 |
| XGBoost + Random Forest          | AND     | Random Forest    |               -6.6313   |                     7.72758  |                     -75 |                   -121 |                      22 |                               97 |

## Original individual rescue

| missed_by        | rescued_by       |   missed_events |   rescued_events |   rescue_rate |
|:-----------------|:-----------------|----------------:|-----------------:|--------------:|
| Dynamic Panel FE | XGBoost          |             242 |               61 |      0.252066 |
| XGBoost          | Dynamic Panel FE |             306 |              125 |      0.408497 |
| Dynamic Panel FE | Random Forest    |             242 |               79 |      0.326446 |
| Random Forest    | Dynamic Panel FE |             234 |               71 |      0.303419 |
| XGBoost          | Random Forest    |             306 |               98 |      0.320261 |
| Random Forest    | XGBoost          |             234 |               26 |      0.111111 |

Same-ZIP-date OR/AND precedes shared seven-day cooldown and one-to-one event matching. Original thresholds retained. Exploratory 2020 validation. Changes in percentage points. No retraining or significance claim.