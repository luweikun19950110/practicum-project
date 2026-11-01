# Rolling60-day trajectory evaluation

  scope period  forecast_origins  regions  paths     RMSE  trajectory_MAE  mean_bias  slope_MAE  direction_agreement  two_step_shape_agreement  change_MAE  acceleration_MAE  all_zero_actual_path_share
overall    all               243      585 142155 1.418396        0.774283   0.067025   0.455175             0.281552                  0.126116    0.896647          1.589743                    0.428145
   year   2020               243      585 142155 1.418396        0.774283   0.067025   0.455175             0.281552                  0.126116    0.896647          1.589743                    0.428145
quarter 2020Q2                62      585  36270 1.040407        0.498861   0.118157   0.283829             0.278991                  0.145547    0.565715          1.021620                    0.575903
quarter 2020Q3                92      585  53820 0.772692        0.426897   0.009563   0.241424             0.206447                  0.089521    0.469918          0.864522                    0.552861
quarter 2020Q4                89      585  52065 2.030217        1.325246   0.090802   0.795497             0.360972                  0.150408    1.568296          2.735180                    0.196293

60 calendar days,14 within-window warmup days;45/44/43 supervised origins per horizon per ZIP. Weekly re-estimation, daily predictor updates. No Pressure ablation or seasonal naive. Primary score is ZIP-path trajectory MAE; change/acceleration and direction/shape are supplementary. Scores are retrospective and exploratory. See protocol.json and training_timing.csv for information boundaries. No coefficient p-values are asserted for this rolling dynamic-FE estimator.
