# Weikun Feature Analysis Notes

Updated 2026-11-05 from repository commit `3348de6` on `main`.

This note records my understanding of Weikun's current work. It is a reference for the Dhruvesh analysis and presentation work. Weikun's files were not modified.

## Executive summary

Weikun built an NJ-only COVID forecasting pipeline. The pipeline cleans recorded illness-onset records by ZIP and date, constructs a daily region panel, adds local case-history and commuting-pressure features, and evaluates short-horizon forecasts with rolling retraining.

The strongest and most consistent predictive signal is recent local case history, especially the 7-day and 14-day rolling case means. Commuting pressure is included in the main specification, but the current ablation results do not show a stable, large standalone improvement from pressure. This should be presented as an exploratory predictive finding, not as evidence that commuting causes infections or that pressure is useless.

The work is substantial but still exploratory. The repository explicitly cautions that the historical validation period has already been inspected, ZIP-to-ZCTA correspondence is not fully validated, the outcome is a recorded-onset count rather than a confirmed infection count, and there is no untouched final test claim in these analyses.

## Data and outcome construction

- Scope: NJ-to-NJ forecasting in the current Weikun pipeline. NY outcomes and cross-state predictors were removed from this version.
- Source panel: 598 reference ZIP identifiers across 1,461 calendar days from 2020-01-01 through 2023-12-31.
- Built feature panel: 873,678 region-day rows and 54 columns.
- Outcome: `cases_today`, defined as recorded illness-onset records after exact full-row deduplication.
- Records without an illness-onset date are excluded from onset aggregation. They are not assigned to an arbitrary date.
- Missing ZIP/date groups are zero-filled only under the confirmed source-coverage rule. This is not a claim that zero means no infections or complete surveillance.
- The model-ready cohort is smaller: 585 common regions for the main rolling comparisons. The feature panel has 590 regions with valid population-based pressure coverage.
- Important upstream limitations: counting-unit and infection-episode definitions still require confirmation, source reporting availability is not simulated, and ZIP-to-ZCTA mapping remains an audit item.

## Feature groups

### 1. Local case history

- Current daily cases: `cases_today`.
- Lags: 1-day, 7-day, and 14-day case counts.
- Rolling levels: 7-day and 14-day totals or means.
- Population-adjusted case rates for the current day and 7-day/14-day windows.

### 2. Local case dynamics

- Week-over-week change.
- Velocity, acceleration, and jerk, which are successive differences in daily counts.
- 7-day and 14-day case variability.
- Days since the last positive observed case for sparse regions.

These are derived only from trailing information available at the forecast origin. They are not independent epidemiological measurements; several are mathematically related to the lagged case history.

### 3. Regional and commuting features

- Population, land area, and population density.
- NJ-network resident and workplace job totals.
- External inbound/outbound commuting volumes and shares within the represented NJ network.
- Normalized inbound commuting weights.

### 4. Commuting-weighted COVID pressure

- `nj_covid_pressure_7d` and `nj_covid_pressure_14d` combine origin-region case rates with inbound commuting weights into a destination-region pressure signal.
- Pressure v2 uses eligible NJ origins with valid population and renormalizes inbound weights once over valid origins.
- Pressure is a proxy for connected regional activity. It is not an infection probability and not an estimate of infected commuters.

### 5. Calendar controls

- Forecast-origin weekday/month and target-day weekday/month indicators.
- These capture calendar regularity and known calendar conditions for each forecast horizon.

## Modeling and evaluation protocol

- Main model family: Dynamic Panel FE.
- Comparison models: XGBoost and Random Forest.
- Main forecast horizons: 1, 2, and 3 days ahead.
- Rolling training window: commonly 60 calendar days, with weekly parameter refits and daily predictor updates.
- Main 2020 rolling comparison: 585 regions, 243 forecast origins from 2020-04-30 through 2020-12-28, and 142,155 three-day region paths.
- Main metric: trajectory MAE across the three forecast days. RMSE, bias, slope error, direction agreement, and shape agreement are supplementary.
- Warning analyses add event definitions, fixed calibration thresholds, a 7-day cooldown, and event matching. Warning precision and recall depend on the chosen threshold and event definition.
- The repository also compares 30/60/90/180-day windows and later periods, but those results are exploratory and should not be treated as one universal best window.

## Main feature-analysis findings

### Training importance

For both tree models, the top training-importance features are dominated by local recent history:

1. 7-day mean cases
2. 14-day mean cases
3. Current cases
4. Recent lagged cases

Commuting pressure appears lower in the tree training-importance rankings. Importance values are model-specific and cannot be compared directly between XGBoost and Random Forest. Correlated features can share importance.

### Group ablation in 2020 validation

The group-removal experiment compares the full model with versions that remove local history, commuting pressure, or calendar features.

- Removing local history increases MAE substantially: about 23.6% for Dynamic Panel, 3.5% for XGBoost, and 88.2% for Random Forest.
- Removing commuting pressure changes MAE only slightly: about -0.9% for Dynamic Panel, +0.3% for XGBoost, and -0.3% for Random Forest. The intervals cross zero.
- Removing calendar features also produces small mixed changes with intervals crossing zero.
- The local-history result is the clearest feature-group finding. Pressure and calendar should be described as retained exploratory inputs, not proven contributors.

### Feature-selection experiments

Using a 0.1% relative MAE improvement rule on an early-2021 selection period:

- Forward and Stepwise selection retained a compact 9-column specification: current cases, 7-day mean cases, 7-day commuting pressure, target weekday controls, and ZIP fixed effects.
- Backward selection retained a broader 21-column specification, including additional lags, rates, variability, acceleration/jerk, both pressure windows, and sparse-history information.
- Later-validation results favored the compact Forward/Stepwise specification over the full 34-column specification, but the search was adaptive and repeatedly inspected. These results are exploratory, not final confirmation.
- The required-pressure run retained 7-day pressure in all three selection methods. This is a modeling constraint/selection result, not proof that pressure improves every period.

### Model comparison

In the matched 2020 rolling comparison using the full candidate feature set:

- Dynamic Panel FE trajectory MAE: 0.7743
- XGBoost trajectory MAE: 0.7543
- Random Forest trajectory MAE: 0.7519

Random Forest and XGBoost are slightly better on overall trajectory MAE in this 2020 development period, while Dynamic Panel remains an interpretable benchmark. The difference is small and does not establish a final model winner.

## What we should use for Dhruvesh's independent analysis

The cleanest presentation-oriented analysis is a three-part feature story:

1. **Local history dominates:** show that recent case levels, especially 7-day and 14-day rolling means, are the most important predictive inputs.
2. **Pressure adds a connected-region hypothesis:** show the pressure definition and report that its incremental validation effect is small and uncertain in the current ablation.
3. **Keep claims exploratory:** compare feature importance with group ablation, explain that they measure different things, and state that correlations and overlapping rolling refits limit causal interpretation.

Recommended presentation visuals:

- A horizontal bar chart of the top 8–10 tree features, labeled in plain English.
- A compact three-row group-ablation chart showing the MAE change after removing local history, pressure, or calendar features for each model.
- A small methodology diagram showing `case history + commuting pressure + calendar -> forecast`.

Do not claim that commuting pressure causes transmission, that Random Forest is definitively the best model, or that the current validation is an untouched final test.

## Primary files reviewed

- `Weikun/README.md`
- `Weikun/07_clean_real_nj_covid.ipynb`
- `Weikun/08_NJ_only_candidate_feature_list.ipynb`
- `Weikun/09_build_nj_daily_features.ipynb`
- `Weikun/10_dynamic_panel_nj_cases.ipynb`
- `Weikun/14_full_feature_selection.ipynb`
- `Weikun/15_individual_stepwise_foward_backward_selection.ipynb`
- `Weikun/17_pressure_contribution_and_benchmarks.ipynb`
- `Weikun/32_2021_model_comparison.ipynb`
- `Weikun/33_feature_diagnostics_2020.ipynb`
- `Weikun/34_three_model_complementarity.ipynb`
- `Weikun/feature_diagnostics_outputs/validation2020_20261102/`
- `Weikun/individual_feature_selection_outputs/three_methods_20261026T153141838619Z/`
- `Weikun/model_prediction_comparison_outputs/comparison_20261101/`
- `Weikun/rolling_trajectory_outputs/rolling60_weekly_development_20261027/`
- `Weikun/xgboost_trajectory_outputs/xgb60_weekly_development_20261027/`
- `Weikun/random_forest_trajectory_outputs/rf60_weekly_development_20261027/`

## Presentation-to-notebook map

The current presentation is `/Users/dhruvesh/Desktop/Fall 2026/Analytics/11:10/11_10 presentation.pptx`. The following map identifies the code that produced the major slide results.

| Slides | Topic | Notebook | Main output files/folder |
|---|---|---|---|
| 1-3 | Data cleaning, candidate features, rolling forecast protocol | `07_clean_real_nj_covid.ipynb`, `09_build_nj_daily_features.ipynb`, `10_prepare_supervised_horizons.ipynb` | Prepared panel and supervised-horizon inputs |
| 4-5 | Daily case prediction and model comparison | `21_fixed60_full_feature_trajectory.ipynb`, `22_trajectory_benchmark_overall.ipynb`, `24_rolling60_trajectory.ipynb`, `25_xgboost_rolling_trajectory.ipynb`, `26_random_forest_rolling_trajectory.ipynb` | `fixed60_trajectory_outputs/`, `trajectory_benchmark_outputs/`, `rolling_trajectory_outputs/`, `xgboost_trajectory_outputs/`, `random_forest_trajectory_outputs/` |
| 6-8 | Three-day trajectory and direction accuracy | `22_trajectory_benchmark_overall.ipynb` plus model notebooks 24-26 | `overall_trajectory_scorecard.csv`, direction/confusion and path-diagnostic outputs |
| 9 | Residual spatial clustering / Moran's I | `24_rolling60_trajectory.ipynb`, `25_xgboost_rolling_trajectory.ipynb`, `26_random_forest_rolling_trajectory.ipynb` | `residual_moran/` folders under the three model output folders |
| 10-16 | Outbreak definition, warning scores, AP, precision, recall, and lead time | `27_nj_outbreak_task.ipynb` | `outbreak_task_outputs/case_surge_v1_20261101/` and `warning_metrics.csv` |
| 17 | Combining model warnings | `34_three_model_complementarity.ipynb`, `36_pairwise_warning_complementarity.ipynb` | `mentor_followup_outputs/2026-11-04/pair_warning_complementarity/` |
| 18 | Combined-model warning lead time | `38_combined_warning_lead_time.ipynb` | `mentor_followup_outputs/2026-11-04/combined_warning_lead/combined_warning_metrics_3_vs_7.csv` |
| 19-20 | Feature-group ablation and tree-model importance | `33_feature_diagnostics_2020.ipynb` | `feature_diagnostics_outputs/validation2020_20261102/` |
| 21 | Monthly lag relationships and lag diagnostics | `39_lag_structure_diagnostics.ipynb` | `mentor_followup_outputs/2026-11-04/lag_analysis/` |

## Exact files for tomorrow's feature-analysis work

Start with these three notebooks and their outputs:

1. `Weikun/33_feature_diagnostics_2020.ipynb`
   - `group_ablation_summary.csv`
   - `group_ablation_by_horizon.csv`
   - `training_importance_summary.csv`
   - `training_split_gain.csv` and model-specific importance files, if needed
   - Feature-analysis figures already generated in the same output folder

2. `Weikun/39_lag_structure_diagnostics.ipynb`
   - `monthly_lag_relationships.csv`
   - `paired_comparisons.csv`
   - `figures/lag_relationships.png`
   - `figures/lag_prediction_comparison.png`

3. `Weikun/27_nj_outbreak_task.ipynb`
   - Use only if the feature-analysis slide needs to connect features to outbreak warnings.
   - `warning_metrics.csv` contains the presentation's warning metrics.
   - `task_definition.json` records the exact event, threshold, cooldown, and matching rules.

## Planned Dhruvesh workflow

Tomorrow, work only in the `Dhruvesh` folder and preserve Weikun's files as read-only reference material.

1. Reuse the same 2020 validation cohort and feature definitions so results remain comparable.
2. Create a new analysis script/notebook for Dhruvesh's independent feature analysis.
3. Start with two visuals: a top-feature ranking and a group-ablation comparison.
4. Add the monthly lag visual only if it supports a clear story and fits the presentation time.
5. Save generated tables, figures, and a short results summary under `Dhruvesh/`.
6. Build the PowerPoint slides from the saved figures and tables, not from manually copied numbers.

The core story for the slides should remain:

> Recent local case history provides the strongest predictive signal. Commuting pressure is a meaningful connected-region feature, but its additional predictive contribution is small and uncertain in this validation. Feature importance and ablation answer different questions, so both should be shown with careful, non-causal language.
