# Three-model trajectory comparison:2020 rolling validation

           model  regions  origins  paths     RMSE  balanced_direction_accuracy  actual_endpoint_flat_share  actual_all_zero_share  trajectory_MAE  mean_bias  direction_agreement  shape_agreement  change_MAE  acceleration_MAE
Dynamic Panel FE      585      243 142155 1.418396                     0.383913                    0.567789               0.428145        0.774283   0.067025             0.281552         0.126116    0.896647          1.589743
         XGBoost      585      243 142155 1.431245                     0.348201                    0.567789               0.428145        0.754299   0.003984             0.227357         0.089951    0.870869          1.548966
   Random Forest      585      243 142155 1.435766                     0.339826                    0.567789               0.428145        0.751885   0.061614             0.220759         0.083831    0.868983          1.546024

## Reading the analysis
Compare count MAE, RMSE, exact direction/shape and magnitude-of-change errors separately. Stratify by quarter and actual path group; groups overlap and do not partition all paths. Geographic diagnostics are separate. Parameters were fixed before the RF run, not optimized to validation scores.

## Uncertainty
Paired differences average losses across all ZIPs at each date before inference. Seven-day and14-day moving-block intervals are pointwise and exploratory. The primary MAE family includes three pairwise HAC tests, Holm adjusted. This is not a coefficient significance test, a clinical efficacy claim or a calibrated prediction interval. Nonstationary outbreaks and overlapping forecasts limit both asymptotic p-values and block intervals.

## Strict-zero sensitivity
The same raw predictions are evaluated under0,0.5,1 cases/day deadbands, introduced as sensitivity values in Notebook21. Threshold0 remains primary. Threshold changes also alter actual labels and the always-flat reference; do not pick the threshold maximizing a model score. Exact-flat scores can be low for small continuous predictions even when count errors are small.

## Key findings
RF MAE0.7519, XGB0.7543, DP0.7743. RF-XGB improvement0.0024 has7-day blockCI[-0.0087,0.0138], so there is no clear difference in average quantity error between the two tree models. DP has lowerRMSE and higher strict direction/shape agreement. Changing-endpoint MAE is not improved by either tree model. Under a1-case/day slope deadband, approximately90.7% direction agreement matches the always-flat classification reference; this is not evidence of90% meaningful trend prediction. RF spatial correlation is descriptively lower, not a paired significance test. See FINDINGS_CN.md.
