# Weikun: NJ COVID forecasting

Notebooks stay in this directory. Generated data and reports belong in the task-specific output folders below, not beside the notebooks.

| Folder | Contents |
|---|---|
| `real_nj_cleaning_outputs` | Cleaned recorded-onset case panel. Canonical input for Notebook 09: `Real NJ COVID Zip.csv`. |
| `nj_daily_feature_outputs` | Complete candidate feature panel `nj_daily_features.csv.gz`, NJ weights, regional features, missingness, previews and build checks. |
| `dynamic_panel_nj_outputs` | Notebook 10 model runs, predictions, metrics and training records, organized by run folder. |
| `population_geography_audit` | Population and geographic correspondence audit. |
| `nj_only_feature_plan` | Candidate feature definitions and planning notes. |
| `njny_commute_outputs` | Earlier NJ/NY route inputs used to rebuild the NJ-only network. |
| `population_outputs` | Earlier population preparation outputs. |
| `regional_attributes_outputs` | Regional attribute input for Notebook 09. |
| `feature_backups` | Previous versions and organization manifests. |

Run notebooks from this Weikun directory. Current chain: 07 (cleaning) → 09 (features) → 10 (baseline). The encrypted source workbook remains at its original external data location.

The feature panel currently uses pressure v2: valid-population NJ origins, fixed renormalized inbound weights. Historical model runs may use the earlier pressure definition; rerun Notebook 10 for a current comparison. This folder reorganization does not retrain models or change data values.

Notebook 07 publishes the canonical case filename inside its cleaning output folder. Notebook 09 reads that location and writes all feature outputs into its own folder. Notebook 10 reads the feature output folder and writes its run folders under dynamic_panel_nj_outputs. Filenames remain unchanged.

Only notebook/readme files should normally appear directly here. Saving locally does not automatically commit or push changes to GitHub. Close and reopen the updated notebooks in Jupyter before running, so an older open tab does not restore the previous paths.

## Training-window comparison

Run 12_compare_dynamic_panel_windows.ipynb for validation-only 30/60/90/180-day comparisons. Results are organized under dynamic_panel_window_comparison_outputs. This step does not generate test forecasts or overwrite prior model runs.


## Feature experiments (Notebook 13)

13_dynamic_panel_feature_experiments.ipynb compares eight feature specifications on the same 590-region validation cohort. Results, exploratory coefficient inference, paired loss tests and report figures are saved in dynamic_panel_feature_experiment_outputs/feature_ablation_20261026T142422577198Z. Start with RESULTS.md and METHODS.md. These are validation-only exploratory results, not GMM or causal inference.


## Full feature pool (Notebook 14)

14_full_feature_selection.ipynb fits the full usable FE feature representation and performs grouped backward screening on a common 585-region valid-population cohort. Output: full_feature_selection_outputs/full_pool_20261026T144421928006Z. These are exploratory 2021 validation results; no final selected set or test evaluation is claimed.



## Individual backward selection (Notebook 15)

15_individual_backward_selection.ipynb starts from the full pool and removes numeric features individually, refitting after every accepted deletion. Months remain one categorical unit; weekday and ZIP FE are retained. Selection uses early 2021 with a declared 0.1% minimum relative MAE improvement, followed by a frozen-feature check in later 2021. Results: individual_feature_selection_outputs/individual_20261026T151801260955Z. Exploratory validation only; no 2022-2023 test evaluation.


### Notebook 15: three-method comparison

Notebook 15 now compares Backward, Forward and Stepwise using identical early-2021 selection conditions and frozen later-2021 feature lists. Results: individual_feature_selection_outputs/three_methods_20261026T152516441253Z. Start with method_comparison_summary.csv, feature_inclusion_comparison.csv and selection_paths.csv. The original backward-only notebook is backed up inside that run folder. All results remain exploratory.


## Frozen feature window sensitivity (Notebook 16)

16_frozen_features_window_sensitivity.ipynb evaluates the fixed Notebook 15 combinations with 60-day windows and compares against the saved 30-day forecasts on identical regions and dates. No new feature selection. Results: individual_feature_selection_outputs/frozen_window_60_20261026T153858733079Z. Start with window_method_comparison_summary.csv. Exploratory validation only; no 2022-2023 test evaluation.


## Pressure contribution and benchmarks (Notebook 17)

17_pressure_contribution_and_benchmarks.ipynb removes only 7-day pressure from the frozen compact FE model, retaining matched 585-region forecasts and 60-day windows. Includes persistence/seasonal-naive benchmarks, horizon/month/region comparisons and exploratory uncertainty. Results: pressure_validation_outputs/pressure_check_20261026T160907020618Z. No feature reselection or 2022-2023 test evaluation.

