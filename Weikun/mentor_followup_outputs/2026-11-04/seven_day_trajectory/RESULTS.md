# Seven-day supplementary trajectory analysis

| model            |   path_days |   path_MAE |   path_RMSE |   endpoint_direction_accuracy |   always_flat_reference |   balanced_direction_accuracy |   decline_recall |   flat_recall |   rise_recall |   strict_shape_accuracy |   mean_daily_change_MAE |   endpoint_change_MAE |
|:-----------------|------------:|-----------:|------------:|------------------------------:|------------------------:|------------------------------:|-----------------:|--------------:|--------------:|------------------------:|------------------------:|----------------------:|
| Dynamic Panel FE |           3 |   0.757117 |     1.38346 |                      0.278661 |                0.572821 |                      0.382637 |         0.47081  |    0.0922099  |      0.58489  |              0.124686   |                0.873468 |              0.888373 |
| Dynamic Panel FE |           7 |   0.821149 |     1.52898 |                      0.281708 |                0.563316 |                      0.376961 |         0.349846 |    0.0893601  |      0.691676 |              0.0196474  |                0.885451 |              1.0074   |
| XGBoost          |           3 |   0.736912 |     1.39624 |                      0.224368 |                0.572821 |                      0.347703 |         0.476315 |    0.00362097 |      0.563172 |              0.0883739  |                0.847431 |              0.857756 |
| XGBoost          |           7 |   0.7784   |     1.49887 |                      0.227257 |                0.563316 |                      0.342313 |         0.448542 |    0.00458354 |      0.573815 |              0.00384794 |                0.861385 |              0.936917 |
| Random Forest    |           3 |   0.734404 |     1.39972 |                      0.218296 |                0.572821 |                      0.33999  |         0.439106 |    0          |      0.580863 |              0.0823445  |                0.845029 |              0.85774  |
| Random Forest    |           7 |   0.774893 |     1.49529 |                      0.226807 |                0.563316 |                      0.341684 |         0.383333 |    0          |      0.64172  |              0.00255337 |                0.859798 |              0.937887 |

| model            |   horizon |      MAE |    RMSE |        bias |   forecast_dates |   regions |
|:-----------------|----------:|---------:|--------:|------------:|-----------------:|----------:|
| Dynamic Panel FE |         1 | 0.729459 | 1.32539 |  0.0655281  |              239 |       585 |
| Dynamic Panel FE |         2 | 0.75492  | 1.3776  |  0.0809028  |              239 |       585 |
| Dynamic Panel FE |         3 | 0.786972 | 1.44479 |  0.0963735  |              239 |       585 |
| Dynamic Panel FE |         4 | 0.818916 | 1.51746 |  0.107765   |              239 |       585 |
| Dynamic Panel FE |         5 | 0.85215  | 1.58898 |  0.130378   |              239 |       585 |
| Dynamic Panel FE |         6 | 0.884492 | 1.66155 |  0.147908   |              239 |       585 |
| Dynamic Panel FE |         7 | 0.921131 | 1.74193 |  0.168549   |              239 |       585 |
| XGBoost          |         1 | 0.71809  | 1.35149 |  0.0226543  |              239 |       585 |
| XGBoost          |         2 | 0.735326 | 1.38974 |  0.0178318  |              239 |       585 |
| XGBoost          |         3 | 0.757319 | 1.44589 |  0.0145448  |              239 |       585 |
| XGBoost          |         4 | 0.778656 | 1.49896 |  0.00535938 |              239 |       585 |
| XGBoost          |         5 | 0.800182 | 1.54241 |  0.00673156 |              239 |       585 |
| XGBoost          |         6 | 0.819165 | 1.59436 | -0.00906748 |              239 |       585 |
| XGBoost          |         7 | 0.840066 | 1.64617 | -0.0157837  |              239 |       585 |
| Random Forest    |         1 | 0.716735 | 1.35818 |  0.0715244  |              239 |       585 |
| Random Forest    |         2 | 0.733507 | 1.39675 |  0.076339   |              239 |       585 |
| Random Forest    |         3 | 0.75297  | 1.44295 |  0.0837036  |              239 |       585 |
| Random Forest    |         4 | 0.775753 | 1.49962 |  0.0797143  |              239 |       585 |
| Random Forest    |         5 | 0.795306 | 1.54153 |  0.0831749  |              239 |       585 |
| Random Forest    |         6 | 0.81447  | 1.5831  |  0.0851545  |              239 |       585 |
| Random Forest    |         7 | 0.835507 | 1.62546 |  0.0922825  |              239 |       585 |

Same 585 ZIPs and Apr 30–Dec 24 daily forecast dates for both path lengths. 60 calendar days with 14-day warmup, weekly refits. All 34 candidates plus ZIP identity. Each horizon has its own direct model; only matured labels enter training. Days 1–3 reproduce prior predictions. Seven-day endpoint direction and six-step shape are different tasks from three-day direction and two-step shape: higher scores do not by themselves prove a better model. Read class recall and flat prevalence alongside accuracy. No outbreak labels, warning thresholds or lead-time results are changed here. 2020 exploratory historical replay; not untouched testing.
