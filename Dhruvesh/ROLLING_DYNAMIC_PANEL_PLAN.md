# Rolling dynamic panel plan

Short training windows walk through the real NJ onset panel so the model can adapt as COVID conditions change. This is **not** LightGBM. The learner is a **dynamic panel FE OLS** in the same spirit as Weikun’s `06_dynamic_panel_demo.ipynb`.

Code and outputs live under `Weikun/rolling_dynamic_panel/`. This note is the design map.

## Window math (60-day first)

| Piece | Length | Role |
|---|---|---|
| Train | 60 days | 70% of the block |
| Test | 26 days | \(60 \times 0.3 / 0.7\), rounded |
| Block | 86 days | train + test |
| Step | 60 days | next train starts when the previous train ends |

Example:

- Window 0: train days 0–59, test days 60–85
- Window 1: train days 60–119, test days 120–145

Incomplete tail blocks (not enough days for 60+26) are skipped.

Inside every window, fit **three** models on the same train days:

- horizon 1 → cases on \(t+1\)
- horizon 2 → cases on \(t+2\)
- horizon 3 → cases on \(t+3\)

## Data

Null-free supervised copies from `Weikun/supervised_horizon_outputs/`:

- `supervised_horizon_1_next_day.csv.gz`
- `supervised_horizon_2.csv.gz`
- `supervised_horizon_3.csv.gz`

One row = one ZIP × one forecast-origin date. Last column = `target_cases`. Rolling logic owns train/test; those files have no split column.

## Model

Per window and horizon:

- **y** = `target_cases`
- **X** = time-varying predictors (calendar, recent cases, rates, pressure, local dynamics). Static population and job levels are omitted; ZIP fixed effects absorb them.
- **ZIP fixed effects** via dummies (`drop_first=True`)
- Fit with `numpy.linalg.lstsq` on train rows only
- Train labels must also fall on or before the last train day (no label leak into the test block)
- Test design matrix is aligned to the train columns
- Predictions clipped at 0
- Persistence baseline: use `cases_today` as the guess for every horizon

## Metrics glossary

| Metric | Meaning |
|---|---|
| MAE | average absolute error |
| RMSE | root mean squared error (penalizes large misses) |
| mean_error | predicted − actual (sign shows bias) |
| persistence_MAE / RMSE | same scores for the naive baseline |
| skill | \(1 - \mathrm{MAE}_{model} / \mathrm{MAE}_{persistence}\) (positive means the panel model beats persistence) |

## Outputs (60-day)

`Weikun/rolling_dynamic_panel/window_60days/outputs/`

| File | Contents |
|---|---|
| `window_metrics.csv` | one row per window × horizon |
| `feature_coefficients.csv` | non-FE coefficients per window × horizon |
| `predictions_test.csv.gz` | test-day predictions (grows as more windows run) |
| `aggregate_metrics.csv` | filled after the full roll (later phase) |

## Plots and gaps

Predictions exist only on each window’s **test** days. Charts should keep the actual series continuous and overlay predictions only on scored segments, so gaps read as “not scored,” not as data errors.

## Build phases

1. Docs (this file) + first window only  
2. Roll all complete 60-day windows  
3. Aggregate tables  
4. Gap-aware plots  
5. Later: clone for 90- and 120-day windows  

## Current status

Phases 0–4 are done for the **60-day** setup in `Weikun/rolling_dynamic_panel/window_60days/`.

Also done:

- **90-day** — `Weikun/rolling_dynamic_panel/window_90days/` (train 90 / test 39 / step 90, 15 windows)
- **120-day** — `Weikun/rolling_dynamic_panel/window_120days/` (train 120 / test 51 / step 120, 11 windows)
