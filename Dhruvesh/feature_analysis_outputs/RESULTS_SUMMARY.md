# Dhruvesh Deep Feature Analysis Results

Generated from Weikun's saved 2020 validation diagnostics. No Weikun files were modified and no model was refit by this script.

## What was analyzed

- 34 candidate engineered features across 585 ZIP codes.
- 243 forecast dates, three horizons, 60-day rolling windows, weekly refits.
- Tree-model training importance, group ablation, horizon stability, monthly stability, feature-selection consensus, correlation, and lag relationships.

## Main numbers

### Top tree-model features

Random Forest top five: 7-day average cases, 14-day average cases, Current cases, 14-day case rate, 7-day commuting pressure.

XGBoost top five: 7-day average cases, 14-day average cases, Current cases, region_id, Cases 1 day earlier.

### Group ablation

Removing local case history changed MAE by approximately 23.6% for Dynamic Panel FE, 3.5% for XGBoost, and 88.2% for Random Forest.

Removing commuting pressure changed MAE by approximately -0.9%, 0.3%, and -0.3%, respectively. These small effects have uncertainty intervals crossing zero.

### Interpretation

Recent local case history is the clearest predictive signal. The tree importance results and ablation results agree on that broad conclusion, but they measure different things. Importance describes how a model used variables during training; ablation measures the change in forecast error after removing a group.

Commuting pressure remains a plausible connected-region feature, but this validation does not show a large incremental predictive gain after local case history is already present. This is not a causal conclusion about commuting or disease transmission.

### Selection and redundancy

Forward, backward, and stepwise selection all retained: Current cases, 7-day average cases, 7-day commuting pressure, target_weekday_2, target_weekday_3, target_weekday_4, target_weekday_5, target_weekday_6, target_weekday_7. The raw feature audit also shows very high correlation between the 7-day and 14-day case means (about 0.98), and between the 7-day and 14-day pressure variables (about 0.99). This is why model importance can be shared across related features.

Monthly lag results should be described as associations. The August lag relationships are weaker than May/November in the current diagnostic, but the analysis is exploratory and does not establish a formal between-month causal or significance claim.

## Presentation-ready figures

1. `figures/01_top_features_random_forest.svg` and `01_top_features_xgboost.svg` — use for the top-feature slide.
2. `figures/02_group_importance.svg` — use to show importance aggregated by conceptual group.
3. `figures/03_group_ablation.svg` — strongest slide for predictive contribution.
4. `figures/04_ablation_by_horizon.svg` — optional deeper slide or backup visual.
5. `figures/05_monthly_lag_relationships.svg` — use for time-varying feature behavior.

Supporting tables: `feature_selection_consensus.csv`, `high_correlation_pairs_clean.csv`, `horizon_stability.csv`, and `importance_by_group_and_month.csv`.

## Important limitation

These are exploratory 2020 validation diagnostics from a previously inspected period. They are not an untouched final test and do not establish causal effects.
