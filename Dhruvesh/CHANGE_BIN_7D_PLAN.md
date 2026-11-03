# 7-day change-bin logistic plan

## Goal
Classify how large the case move is by day `t+7`, relative to today — not the exact count.

Notebook: `Dhruvesh/change_bin_7d_logistic.ipynb`  
Outputs: `Dhruvesh/change_bin_7d_outputs/`

## Target rule
Relative change:

`r = (cases_{t+7} - cases_t) / cases_t`

Softening: if `cases_t < 10` (or `cases_t == 0`) → label `flat`.

Bins when base ≥ 10:

| Label | Range of r |
|---|---|
| `down_300p` | ≤ −3.0 |
| `down_100p` | (−3.0, −1.0] |
| `down_50p` | (−1.0, −0.5] |
| `down_10p` | (−0.5, −0.1) |
| `flat` | [−0.1, +0.1] |
| `up_50p` | (+0.1, +0.5] |
| `up_100p` | (+0.5, +1.0] |
| `up_300p` | (+1.0, +3.0] |
| `up_300p_plus` | > +3.0 |

## Predictors
- `case_velocity`, `case_acceleration`, `case_jerk`
- last 3 three-day slopes: `slope_3d`, `slope_3d_lag1`, `slope_3d_lag2`
- `avg_slope_10d` (mean of overlapping 3-day slopes; magnitude, not angle)
- `population`, `population_density_per_sq_km`

Not used as predictors in v1: raw `cases_today` (only gates the label), slope angles.

## Model
Multinomial logistic regression (`sklearn`), `class_weight="balanced"`.

### Evaluation (preferred for slides)
Rolling windows matching the mentor-style check:
- train **60 days**
- test **next 26 days**
- step forward **7 days**
- leakage guard: train rows only if `date + 7 <= train_end`

Script: `Dhruvesh/change_bin_7d_rolling.py`  
Outputs: `Dhruvesh/change_bin_7d_outputs/rolling_60_26_step7/`

### Older one-shot split (kept for reference)
Chronological ~2/3–1/3 in `change_bin_7d_logistic.ipynb` (not the primary slide result anymore).

## Phases
1. Load data, build slopes/target, print distributions, save `label_rules.json` — done
2. One-shot chronological fit in notebook — done (legacy)
3. Rolling 60/26/step-7 evaluation + aggregate metrics — done
4. Slide assets from rolling aggregates — done
