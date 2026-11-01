# Three-day trajectory: change and acceleration diagnostics

No refitting, feature changes or target changes. Trajectory MAE remains the primary metric. All scores are per-ZIP paths, not changes in the summed state curve.

            measure      MAE     RMSE  mean_bias  strict_sign_agreement  actual_zero_share  observations        unit
daily_change_pooled 0.794910 1.469735   0.163383               0.307326           0.658578         32760   cases/day
day1_to_day2_change 0.792406 1.463628   0.154097               0.302381           0.655128         16380   cases/day
day2_to_day3_change 0.797413 1.475816   0.172668               0.312271           0.662027         16380   cases/day
       acceleration 1.367774 2.475866   0.018572               0.299939           0.558852         16380 cases/day^2

Change MAE averages two absolute change errors within each path, then all paths. Acceleration MAE averages one absolute second-difference error per path. Bias is predicted minus actual. Units use one-day spacing; these describe changes in DAILY NEW cases. Sign agreement uses exact zeros and is sensitive to class imbalance and small predicted changes. The zero share is the accuracy of an always-zero sign reference, not an alternative fitted model.

These diagnostics assess numerical changes, not clinical outbreak detection. Second differences can amplify daily-count noise. Subgroups overlap and do not form a partition. Intervals are exploratory and conditional on the existing historical replay. No p-value is calculated because no paired competing-model hypothesis is being tested.
