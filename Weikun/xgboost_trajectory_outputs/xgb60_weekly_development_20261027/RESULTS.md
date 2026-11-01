# XGBoost rolling60-day trajectory evaluation

  scope period  forecast_origins  regions  paths     RMSE  trajectory_MAE  mean_bias  slope_MAE  direction_agreement  two_step_shape_agreement  change_MAE  acceleration_MAE  all_zero_actual_path_share
overall    all               243      585 142155 1.431245        0.754299   0.003984   0.439963             0.227357                  0.089951    0.870869          1.548966                    0.428145
   year   2020               243      585 142155 1.431245        0.754299   0.003984   0.439963             0.227357                  0.089951    0.870869          1.548966                    0.428145
quarter 2020Q2                62      585  36270 0.950359        0.476298   0.104595   0.255649             0.167935                  0.061180    0.499099          0.903941                    0.575903
quarter 2020Q3                92      585  53820 0.821850        0.424450  -0.014825   0.235210             0.161464                  0.054738    0.460998          0.846753                    0.552861
quarter 2020Q4                89      585  52065 2.065333        1.288930  -0.046663   0.780015             0.336867                  0.146394    1.553541          2.724193                    0.196293

60 calendar days,14 within-window warmup days;45/44/43 supervised origins per horizon per ZIP. Weekly re-estimation, daily predictor updates. No Pressure ablation or seasonal naive. Primary score is ZIP-path trajectory MAE; change/acceleration and direction/shape are supplementary. Scores are retrospective and exploratory. See protocol.json and training_timing.csv for information boundaries. No coefficient p-values or causal feature interpretations are asserted for this XGBoost estimator.
