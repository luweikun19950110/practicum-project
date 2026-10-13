# Dhruvesh

This folder is the New Jersey workplace forecast. `Weikun/` and `Ayaan/` are separate.

Read this file for where things live. The formulas are in the two notes linked below.

## What to open

| Goal | File |
|---|---|
| See the training table | `training/explore_training_panel.ipynb` |
| See the 7-day model, metrics, plots, and feature importance | `training/forecast_7day.ipynb` |
| Read how the training table is built | `training/README.md` |
| Read how the commute weights are built | `COMMUTE_WEIGHTS.md` |

The model reads `training/training_panel_2021.csv`. December scores are in `training/forecast_outputs/`: `predictions_test.csv`, `metrics_test.csv`, and `feature_importance.csv`.

## How the pieces connect

1. `Data/LODES/` is the Census job files. `build_nj_inbound_weights.py` writes `commute_outputs/nj_inbound_weights_2021.csv`.
2. `build_synthetic_cases.py` writes the fake 2021 counts in `temporary/nj_cases_2021.csv` and `temporary/nyc_cases_2021.csv`.
3. `training/build_training_panel.py` joins those and writes `training/training_panel_2021.csv`.
4. `training/forecast_7day.py` trains seven models, one per future day, from that panel.

Run the scripts from the project root.

`njny_commute_outputs/` and `analysis.ipynb` are earlier experiments. The forecast does not read them. `Data/LEHD/` is the older New Jersey-only extract. The weight script uses `Data/LODES/`.
