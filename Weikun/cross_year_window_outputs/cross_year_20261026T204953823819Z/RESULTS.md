# Cross-year rolling-window backtest

Frozen 9-column primary and 21-column sensitivity specifications, both retaining 7-day Pressure. 585 regions, weekly refits, horizons 1/2/3. Windows share all forecast origins and target values. This is exploratory backtesting; no untouched-test claim.

2020 is partial-year historical replay; 2021 was used for feature selection. Use 2022 and 2023 rows to inspect subsequent temporal stability. Calendar quarters describe time variation, not formally labeled epidemic waves. Lower error is better; do not pick a universal window from one year alone.

## Yearly mean horizon scores

period_type period  window                      model      MAE     RMSE     bias  MAE_rank_within_period_model
       year   2020      30 BACKWARD_REQUIRED_PRESSURE 0.911641 1.587169 0.059143                           4.0
       year   2020      30  COMPACT_REQUIRED_PRESSURE 0.906201 1.586529 0.057436                           4.0
       year   2020      60 BACKWARD_REQUIRED_PRESSURE 0.896967 1.566411 0.048926                           2.0
       year   2020      60  COMPACT_REQUIRED_PRESSURE 0.899570 1.571089 0.073445                           2.0
       year   2020      90 BACKWARD_REQUIRED_PRESSURE 0.891841 1.567501 0.038916                           1.0
       year   2020      90  COMPACT_REQUIRED_PRESSURE 0.895828 1.574306 0.066701                           1.0
       year   2020     180 BACKWARD_REQUIRED_PRESSURE 0.900475 1.570336 0.037984                           3.0
       year   2020     180  COMPACT_REQUIRED_PRESSURE 0.900357 1.587846 0.026044                           3.0
       year   2021      30 BACKWARD_REQUIRED_PRESSURE 1.113424 1.913639 0.047154                           4.0
       year   2021      30  COMPACT_REQUIRED_PRESSURE 1.110343 1.911249 0.042955                           4.0
       year   2021      60 BACKWARD_REQUIRED_PRESSURE 1.097193 1.887246 0.055206                           2.0
       year   2021      60  COMPACT_REQUIRED_PRESSURE 1.097699 1.890472 0.048716                           3.0
       year   2021      90 BACKWARD_REQUIRED_PRESSURE 1.098205 1.887745 0.050916                           3.0
       year   2021      90  COMPACT_REQUIRED_PRESSURE 1.095387 1.891737 0.042252                           1.0
       year   2021     180 BACKWARD_REQUIRED_PRESSURE 1.096085 1.885188 0.036083                           1.0
       year   2021     180  COMPACT_REQUIRED_PRESSURE 1.095608 1.894122 0.020503                           2.0
       year   2022      30 BACKWARD_REQUIRED_PRESSURE 0.954790 1.589780 0.151595                           4.0
       year   2022      30  COMPACT_REQUIRED_PRESSURE 0.944761 1.566251 0.155672                           4.0
       year   2022      60 BACKWARD_REQUIRED_PRESSURE 0.936935 1.515951 0.156566                           3.0
       year   2022      60  COMPACT_REQUIRED_PRESSURE 0.928584 1.519463 0.146624                           3.0
       year   2022      90 BACKWARD_REQUIRED_PRESSURE 0.924372 1.482798 0.130627                           2.0
       year   2022      90  COMPACT_REQUIRED_PRESSURE 0.926233 1.507204 0.137531                           2.0
       year   2022     180 BACKWARD_REQUIRED_PRESSURE 0.899664 1.436483 0.107100                           1.0
       year   2022     180  COMPACT_REQUIRED_PRESSURE 0.908578 1.469973 0.124757                           1.0
       year   2023      30 BACKWARD_REQUIRED_PRESSURE 0.187353 0.463304 0.027357                           3.0
       year   2023      30  COMPACT_REQUIRED_PRESSURE 0.187187 0.462973 0.028761                           2.0
       year   2023      60 BACKWARD_REQUIRED_PRESSURE 0.185099 0.459843 0.023865                           1.0
       year   2023      60  COMPACT_REQUIRED_PRESSURE 0.186091 0.462486 0.026857                           1.0
       year   2023      90 BACKWARD_REQUIRED_PRESSURE 0.186455 0.460181 0.025023                           2.0
       year   2023      90  COMPACT_REQUIRED_PRESSURE 0.188285 0.463517 0.028412                           3.0
       year   2023     180 BACKWARD_REQUIRED_PRESSURE 0.191719 0.465153 0.035773                           4.0
       year   2023     180  COMPACT_REQUIRED_PRESSURE 0.197043 0.470718 0.042629                           4.0
