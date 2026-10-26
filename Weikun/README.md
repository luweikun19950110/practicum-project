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

