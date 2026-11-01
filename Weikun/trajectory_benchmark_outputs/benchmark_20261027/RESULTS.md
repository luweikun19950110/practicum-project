# Three-day trajectory benchmark: overall results

Each path contains day1/day2/day3 predictions issued at one ZIP and one forecast origin. The primary score averages each path's three absolute errors, then averages 16,380 paths. This is mathematically equal to pooled MAE because all paths contain three equally weighted targets. It is not a new improvement relative to Notebook21. No model is refitted or feature changed.

## Scorecard
                         metric    value       unit       role
                 trajectory_MAE 0.981021      cases    primary
                    pooled_RMSE 1.962175      cases  secondary
                 mean_path_RMSE 1.103471      cases  secondary
                      mean_bias 0.672855      cases diagnostic
                      slope_MAE 0.412099  cases/day  secondary
     strict_direction_agreement 0.354335 proportion  secondary
    balanced_direction_accuracy 0.426890 proportion diagnostic
       two_step_shape_agreement 0.151526 proportion  secondary
always_flat_direction_reference 0.655495 proportion diagnostic
     all_zero_actual_path_share 0.526923 proportion diagnostic

## Findings
Trajectory MAE is 0.9810 cases, slope MAE is 0.4121 cases/day. Strict endpoint direction agreement is 35.43%, compared with 65.55% for an always-endpoint-flat reference. Both daily movement signs agree on 15.15% of paths. These results do not demonstrate adequate trend capture in the May decline. Endpoint-flat includes paths that rise then fall back to the starting level; it is not a complete shape category.

## Comparison protocol
Dynamic Panel is the benchmark model; its predicted paths are the benchmark trajectories. Each candidate model must output identical region/order/origin/horizon/target arrays. Compare trajectory MAE primarily, with slope/shape and bias as supporting measures. No per-ZIP score tables are produced. May should not be used to tune features, thresholds or models. The saved run is exploratory historical replay, not an untouched final test.
