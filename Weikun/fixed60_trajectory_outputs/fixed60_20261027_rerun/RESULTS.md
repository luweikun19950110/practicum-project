# Fixed-60-day full-candidate trajectory benchmark

Training is restricted to March 1-April 29, 2020 (60 calendar days). Parameters fit once on April 30 and remain frozen throughout May. Daily predictor updates are allowed, but May labels never update parameters. Fourteen warmup days and horizon maturity leave 45/44/43 usable training origins for h=1/2/3, respectively. This is not 60 usable training pairs per horizon.

All 34 candidate columns enter the design; training-only constant/dependent columns are logged, not removed by predictive selection. Static geography is absorbed by ZIP FE. May month effects are unestimable from March-April and are not learned. Both Pressure candidates enter the design.

## Overall case metrics
               scope   horizon  observations      MAE     RMSE     bias  mean_actual
pooled_region_origin         1         16380 0.847427 1.644652 0.512567     0.586142
pooled_region_origin         2         16380 0.970863 1.910649 0.666664     0.561600
pooled_region_origin         3         16380 1.124773 2.279238 0.839333     0.541514
pooled_region_origin all_1_2_3         49140 0.981021 1.962175 0.672855     0.563085

## Trajectory metrics
 slope_flat_threshold              subgroup  trajectory_count  direction_agreement  slope_MAE
                  0.0                   all             16380             0.354335   0.412099
                  0.0        actual_nonflat              5643             0.488038   0.882422
                  0.0           actual_flat             10737             0.284064   0.164913
                  0.0 actual_all_three_zero              8631             0.328351   0.123248
                  0.5                   all             16380             0.804029   0.412099
                  0.5        actual_nonflat              1867             0.144081   1.516228
                  0.5           actual_flat             14513             0.888927   0.270060
                  0.5 actual_all_three_zero              8631             0.955162   0.123248
                  1.0                   all             16380             0.922405   0.412099
                  1.0        actual_nonflat               780             0.047436   2.188309
                  1.0           actual_flat             15600             0.966154   0.323288
                  1.0 actual_all_three_zero              8631             0.993743   0.123248

These direction rates pool ZIP-origin trajectories and do not mean that the same proportion of ZIPs is accurate. Exact-flat and all-zero paths are reported separately. Threshold sensitivity is descriptive, not tuned. Aggregate curves can hide offsetting regional errors and are supplementary. No per-ZIP accuracy table is produced. Raw predictions remain available for verification.

May primarily covers decline in this dataset. Results do not establish rising-wave or outbreak-warning performance. Historical replay uses later-developed feature definitions/cohort and retrospective onset history, not a prospective untouched test. No PR-AUC, warning lead time or residual Moran score is fabricated.
