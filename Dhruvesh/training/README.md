# Training panel (no demographics)

2021 only. Synthetic cases. Commute weights from LODES. No population, income, age, or SVI columns.

Rebuild from the project root:

```bash
python Dhruvesh/training/build_training_panel.py
```

## Inputs

| File | What it is |
|---|---|
| `Dhruvesh/commute_outputs/nj_inbound_weights_2021.csv` | Home ZCTA → New Jersey workplace, with `inbound_weight` |
| `Dhruvesh/temporary/nj_cases_2021.csv` | 598 New Jersey ZCTAs, every day of 2021, `cases` |
| `Dhruvesh/temporary/nyc_cases_2021.csv` | 198 New York City ZCTAs, every day of 2021, `cases` |

Home areas in the weight file are exactly those New Jersey and New York City ZCTAs. Same-ZCTA commutes are already absent from the weight file.

## Phase 1 — destination pressure

For one workplace `z` on day `d`:

```
pressure(z, d) = Σ over homes h of  inbound_weight(h → z) × cases(h, d)
```

`cases(h, d)` comes from the New Jersey file when `h` is in New Jersey, and from the New York City file when `h` is in New York City.

The script does this by month so it does not build the full link-day table. That table would be 212,347 links × 365 days, about 77 million rows. The saved result is one row per workplace per day.

`weight_coverage` is the sum of the weights that found a case row. In this 2021 build it is 1 for every workplace-day, so every home that feeds the workplace had a case count.

Saved as `destination_pressure_2021.csv`:

| Column | Meaning |
|---|---|
| `destination_zcta` | New Jersey workplace |
| `date` | Day |
| `pressure` | Sum of weight × home cases |
| `weight_coverage` | 1 when every inbound home had a case row |

215,350 rows = 590 workplaces × 365 days.

## Phase 2 — New Jersey local series

Take only `nj_cases_2021.csv`. Sort by ZIP code and date. `day_of_week` is Monday = 0 through Sunday = 6. Inside each ZIP code:

```
velocity     = daily_cases today − daily_cases yesterday
acceleration = velocity today − velocity yesterday
jerk         = acceleration today − acceleration yesterday
```

The first day of each ZIP code has no velocity. The second has no acceleration. The third has no jerk. Those cells stay blank in this file so the differences are visible. The training file drops them.

Saved as `nj_cases_derivatives_2021.csv`:

| Column | Meaning |
|---|---|
| `zipcode` | New Jersey ZCTA |
| `date` | Day |
| `day_of_week` | Monday = 0 through Sunday = 6 |
| `daily_cases` | Cases in that ZCTA that day |
| `velocity` | Day-to-day change in cases |
| `acceleration` | Day-to-day change in velocity |
| `jerk` | Day-to-day change in acceleration |

218,270 rows = 598 ZCTAs × 365 days. Eight of these ZCTAs are homes in the weight file but never workplaces, so they have no pressure.

## Phase 3 — final training table

Inner join of Phase 2 onto Phase 1:

```
zipcode = destination_zcta
date    = date
```

An inner join keeps the 590 workplaces. The 8 New Jersey ZCTAs that are only homes drop out. New York City does not appear as its own row. New York City cases enter only through `pressure`.

Saved as `training_panel_2021.csv`:

| Column | Meaning |
|---|---|
| `zipcode` | New Jersey workplace ZCTA |
| `date` | Day |
| `day_of_week` | Monday = 0 through Sunday = 6 |
| `daily_cases` | Cases in that workplace ZCTA |
| `velocity` | Change in `daily_cases` |
| `acceleration` | Change in `velocity` |
| `jerk` | Change in `acceleration` |
| `pressure` | Inbound commute pressure that day |
| `weight_coverage` | 1 in this build |

213,580 rows = 590 workplaces × 362 days. The first three days of 2021 are removed because `velocity`, `acceleration`, or `jerk` is blank there. No column in this file has a blank cell.

## 7-day forecast

`forecast_7day.py` and `forecast_7day.ipynb` train seven LightGBM models on this panel. Each model predicts one future day of `daily_cases`.

The row date is the day you already know. Lag 0 is that day. Features are `day_of_week`, cases lags 0–6, velocity lags 0–5, acceleration lags 0–4, jerk lags 0–3, and pressure lags 0–6 (30 columns). Targets are `target_day_1` through `target_day_7`.

Rows missing a lag or a future day are dropped. Training uses dates before `TEST_START` (1 December 2021). Testing uses December dates that still have all 7 future days inside the file, so the last scored day is 24 December.

To point this at a new panel, change `DATA_PATH` and `TEST_START` at the top of `forecast_7day.py`.

```bash
python Dhruvesh/training/forecast_7day.py
```

Outputs:

- `forecast_outputs/predictions_test.csv` — actual and predicted cases for each horizon, plus the persistence baseline
- `forecast_outputs/metrics_test.csv` — MAE, RMSE, and mean error (predicted minus actual) by horizon
- `forecast_outputs/feature_importance.csv` — LightGBM gain for every feature and horizon

## What is not in this folder

- Demographics, population, income, age, SVI
- The 77-million-row link-day table
- Real case counts. Replace `temporary/nj_cases_2021.csv` and `temporary/nyc_cases_2021.csv`, then rerun the script. The weight file stays until the LODES year changes.
