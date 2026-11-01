# Random Forest rolling60-day trajectory evaluation

  scope period  forecast_origins  regions  paths     RMSE  trajectory_MAE  mean_bias  slope_MAE  direction_agreement  two_step_shape_agreement  change_MAE  acceleration_MAE  all_zero_actual_path_share
overall    all               243      585 142155 1.435766        0.751885   0.061614   0.440017             0.220759                  0.083831    0.868983          1.546024                    0.428145
   year   2020               243      585 142155 1.435766        0.751885   0.061614   0.440017             0.220759                  0.083831    0.868983          1.546024                    0.428145
quarter 2020Q2                62      585  36270 0.940897        0.452005   0.046503   0.248373             0.157899                  0.053405    0.484042          0.883861                    0.575903
quarter 2020Q3                92      585  53820 0.900230        0.430482  -0.001731   0.235921             0.161966                  0.054032    0.461928          0.847962                    0.552861
quarter 2020Q4                89      585  52065 2.043021        1.293028   0.137621   0.784498             0.325324                  0.135830    1.557920          2.728897                    0.196293

60 calendar days,14 within-window warmup days;45/44/43 supervised origins per horizon per ZIP. Weekly re-estimation, daily predictor updates. No Pressure ablation or seasonal naive. Primary score is ZIP-path trajectory MAE; change/acceleration and direction/shape are supplementary. Scores are retrospective and exploratory. See protocol.json and training_timing.csv for information boundaries. No coefficient p-values or causal feature interpretations are asserted for this Random Forest estimator.
