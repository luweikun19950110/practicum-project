# Three-model trajectory comparison:2021 subsequent time evaluation

           model  regions  origins  paths     RMSE  balanced_direction_accuracy  actual_endpoint_flat_share  actual_all_zero_share  trajectory_MAE  mean_bias  direction_agreement  shape_agreement  change_MAE  acceleration_MAE
Dynamic Panel FE      585      362 211770 1.901808                     0.399752                    0.423979               0.266237        1.107401   0.078543             0.362837         0.180337    1.317798          2.303290
         XGBoost      585      362 211770 1.939047                     0.353569                    0.423979               0.266237        1.098323  -0.016996             0.307319         0.132634    1.299819          2.280820
   Random Forest      585      362 211770 1.900485                     0.341408                    0.423979               0.266237        1.090408   0.065933             0.295056         0.120201    1.304884          2.287952

## Reading the analysis
Compare count MAE, RMSE, exact direction/shape and magnitude-of-change errors separately. Stratify by quarter and actual path group; groups overlap and do not partition all paths. Geographic diagnostics are separate. Parameters were fixed before the RF run, not optimized to validation scores.

## Uncertainty
Paired differences average losses across all ZIPs at each date before inference. Seven-day and14-day moving-block intervals are pointwise and exploratory. The primary MAE family includes three pairwise HAC tests, Holm adjusted. This is not a coefficient significance test, a clinical efficacy claim or a calibrated prediction interval. Nonstationary outbreaks and overlapping forecasts limit both asymptotic p-values and block intervals.

## Strict-zero sensitivity
The same raw predictions are evaluated under0,0.5,1 cases/day deadbands, introduced as sensitivity values in Notebook21. Threshold0 remains primary. Threshold changes also alter actual labels and the always-flat reference; do not pick the threshold maximizing a model score. Exact-flat scores can be low for small continuous predictions even when count errors are small.
