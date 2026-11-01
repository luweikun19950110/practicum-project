# XGBoost vs Dynamic Panel: matched2020 rolling validation

           model  trajectory_MAE  pooled_RMSE  mean_bias  direction_agreement  balanced_direction_accuracy  two_step_shape_agreement  change_MAE  acceleration_MAE  change_sign_agreement  acceleration_sign_agreement
Dynamic Panel FE        0.774283     1.418396   0.067025             0.281552                     0.383913                  0.126116    0.896647          1.589743               0.283726                     0.313200
         XGBoost        0.754299     1.431245   0.003984             0.227357                     0.348201                  0.089951    0.870869          1.548966               0.223457                     0.270852

Both models use identical585 ZIPs,243 forecast origins,3 target days,60-calendar-day windows,14 within-window warmup and weekly refit dates. Both include the34 candidate columns and region identity. XGBoost represents ZIP as a native categorical input, not an FE coefficient or ordered ZIP number. Fixed200-tree depth3 configuration; no validation-based tuning/early stopping. This is a comparison of two implementations with different inductive biases, not causal attribution to nonlinearity alone.

Primary comparison: mean ZIP-path MAE. Positive paired improvement favors XGBoost. Seven-day moving-block intervals are primary descriptive uncertainty,14-day intervals sensitivity; no independent-ZIP assumption, p-values or post-selection claims. Period/cohort were previously explored. Raw-count changes, exact-flat signs and imbalance must be considered. Overall summaries can conceal differences by quarter or path type.
