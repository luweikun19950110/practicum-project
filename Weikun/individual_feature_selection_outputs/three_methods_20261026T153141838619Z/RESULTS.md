# Backward, Forward and Stepwise feature selection

Common 585 regions; 30-day windows, weekly refits, horizons 1/2/3. All methods use the same candidate pool, forced weekday controls and ZIP FE. A numeric variable is one selection unit; month encoding is one categorical unit. Initial FULL: 34 columns.

## Shared rule

Choose the candidate with the lowest January-June 2021 mean MAE across horizons. Accept an addition/deletion only if relative MAE improves at least 0.1% over the current specification. Alphabetical tie break. Refit after each accepted change. RMSE is recorded, not optimized. This is a heuristic predictive selection rule, not a coefficient p-value stepwise procedure.

BACKWARD starts FULL and removes. FORWARD starts with weekday/ZIP controls and adds. STEPWISE starts with controls, adds, then repeatedly checks deletions before trying another addition.

## Mean metrics

| Period | Method | Columns | MAE | RMSE |
|---|---|---:|---:|---:|
| later_validation | BACKWARD | 21 | 1.178472 | 2.018709 |
| later_validation | FORWARD | 9 | 1.171625 | 2.013175 |
| later_validation | FULL | 34 | 1.180819 | 2.023986 |
| later_validation | STEPWISE | 9 | 1.171625 | 2.013175 |
| selection | BACKWARD | 21 | 1.059605 | 1.808737 |
| selection | FORWARD | 9 | 1.060438 | 1.810525 |
| selection | FULL | 34 | 1.066634 | 1.812614 |
| selection | STEPWISE | 9 | 1.060438 | 1.810525 |

Lists are frozen before July-December validation scoring. Later outcomes may enter subsequent rolling parameter refits; membership never changes. Earlier work already examined 2021, so this is exploratory temporal assessment, not an untouched final test. No 2022-2023 test scores are generated.

All search p-values are exploratory: HAC on date-level paired losses, Holm across examined search trials. Adaptive selection invalidates a confirmatory interpretation; correction does not repair search bias. Method comparisons adjust 12 pairwise tests across both periods. Pointwise 14-day bootstrap intervals resample fixed forecast errors, not the entire selection pipeline. Do not choose a definitive final method from later-validation ranking without acknowledging this additional selection.

Start with method_comparison_summary.csv, feature_inclusion_comparison.csv and selection_paths.csv. selected_features_by_method.json contains exact lists. Rank logs distinguish inactive training calendar/constant columns from feature removal. Static population/density/commuting summaries remain tree-model candidates.
