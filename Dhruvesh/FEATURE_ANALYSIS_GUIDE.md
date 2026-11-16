# Dhruvesh Feature Analysis Guide

This is the working guide for the independent feature-analysis section. The analysis follows Weikun's methodology and reuses his saved 2020 outputs as a reference. It does not modify Weikun's notebooks or claim a new final model.

## How to run it

From the repository root:

```bash
python3 Dhruvesh/feature_analysis_deep.py
```

The script writes tables and editable SVG charts to:

`Dhruvesh/feature_analysis_outputs/`

## What each analysis cell does

### Cells 1–3: establish the study and feature inventory

These cells load the same feature families used by Weikun and document the scope: 34 candidate features, 585 ZIP codes, 243 forecast dates, three forecast horizons, 60-day rolling windows, and weekly refitting.

Plain-language question: “What information did the models receive?”

### Cell 4: rank individual features and aggregate by group

This reads XGBoost and Random Forest training importance. It creates:

- `top10_features_by_model_plain_english.csv`
- `importance_by_feature_group.csv`
- `figures/01_top_features_random_forest.svg`
- `figures/01_top_features_xgboost.svg`
- `figures/02_group_importance.svg`

Plain-language question: “What did the models use most during training?”

Expected result: recent local case history—especially 7-day average cases, 14-day average cases, and current cases—dominates.

### Cell 5: check forecast-horizon stability

This compares importance across 1-day, 2-day, and 3-day predictions. It records how often each feature appears in the top five.

Plain-language question: “Does the same feature matter for near-term and slightly farther-ahead forecasts?”

Output: `horizon_stability.csv` and `top10_features_by_model_horizon.csv`.

### Cell 6: check monthly stability

This aggregates feature importance by month. It checks whether the model relied on the same signals during different phases of 2020.

Plain-language question: “Did the model use the same clues in spring, summer, and autumn?”

Output: `importance_by_group_and_month.csv` and `top5_features_by_model_month.csv`.

### Cell 7: group ablation

This uses Weikun’s refit results after removing one feature group at a time. A positive MAE change means the model became worse when the group was removed.

Plain-language question: “Does removing this group actually hurt prediction performance?”

Outputs:

- `ablation_summary_clean.csv`
- `ablation_by_horizon_clean.csv`
- `figures/03_group_ablation.svg`
- `figures/04_ablation_by_horizon.svg`

Expected result: removing local case history increases MAE substantially. Pressure and calendar changes are small and uncertain.

### Cell 8: feature-selection consensus

This summarizes the forward, backward, and stepwise searches that came before the current diagnostics.

Plain-language question: “Which features survive different attempts to simplify the model?”

All three methods retained current cases, 7-day average cases, 7-day commuting pressure, and target-weekday indicators. The methods disagree on many other features, which is expected when predictors are correlated.

Output: `feature_selection_consensus.csv`.

### Cell 8b: redundancy audit

This preserves Weikun’s high-correlation checks.

Plain-language question: “Could related features be sharing importance?”

Important correlations include approximately:

- 7-day mean cases vs. 14-day mean cases: 0.98
- 7-day pressure vs. 14-day pressure: 0.99

Output: `high_correlation_pairs_clean.csv`.

This is why it is safer to say “recent local history is important” than to claim one specific rolling feature is uniquely responsible.

### Cell 9: monthly lag relationships

This uses Weikun’s later diagnostic to compare current cases with cases 1 and 7 days earlier across May, August, and November.

Plain-language question: “Does the relationship between past and current cases change during the outbreak?”

Outputs:

- `lag_relationships_clean.csv`
- `figures/05_monthly_lag_relationships.svg`

Expected result: August shows weaker lag relationships, especially for the 7-day lag. This is descriptive and should not be presented as causal proof.

## Recommended presentation slides

### Slide A — What inputs mattered most?

Use the two top-feature SVGs side by side.

Suggested takeaway:

> “Both tree models rely mainly on recent local case history. The 7-day and 14-day averages summarize the current local trend, while commuting pressure is a secondary signal.”

### Slide B — Which feature groups improved forecasting?

Use `03_group_ablation.svg`.

Suggested takeaway:

> “Removing local case history increases prediction error. Removing commuting pressure or calendar controls changes error only slightly in this validation.”

### Optional Slide C — Does feature behavior change over time?

Use `05_monthly_lag_relationships.svg`.

Suggested takeaway:

> “The relationship between earlier and current cases is not constant across months, suggesting that feature usefulness can change during different phases of the outbreak.”

## Numbers ready for slide notes

- Dynamic Panel local-history removal: MAE increases about 23.6%.
- XGBoost local-history removal: MAE increases about 3.5%.
- Random Forest local-history removal: MAE increases about 88.2%.
- Commuting-pressure removal: approximately -0.9%, +0.3%, and -0.3% for Dynamic Panel, XGBoost, and Random Forest.
- Top tree features: 7-day average cases, 14-day average cases, and current cases.
- 7-day and 14-day average case features are highly correlated, approximately 0.98.

## Claims to avoid

- Do not say commuting pressure causes COVID transmission.
- Do not say Random Forest is definitively the best model based only on this validation.
- Do not call the rule-defined events official outbreaks.
- Do not describe feature importance as causal influence.
- Do not call this period an untouched final test.
