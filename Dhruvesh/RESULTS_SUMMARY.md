# Results summary (honest read)

Last updated: 2026-11-02

## Rolling dynamic panel (main forecasting result)

Short-horizon **case counts** with rolling FE OLS, scored vs persistence (“future = today”).

| Train window | Model MAE (day-ahead) | Persistence MAE | Share of windows beating persistence |
|---|---|---|---|
| 60 days | 0.73 | 0.78 | 52% |
| 90 days | 0.68 | 0.72 | 53% |
| 120 days | 0.67 | 0.71 | 64% |

**Meaning:** the model is a bit better than persistence, more often with longer training. The lift is **modest**, not a breakthrough. This is still a legitimate forecasting baseline for the mentor story.

Code/outputs: `Weikun/rolling_dynamic_panel/window_{60,90,120}days/`

## 7-day change-bin logistic (side experiment)

Classifies relative move by day t+7 into % bins; base &lt; 10 forced to `flat`. This is a **side try**, not a replacement for the main rolling panel plan.

### Rolling eval (preferred): train 60d → test 26d → step 7d

| Metric (mean over OK windows) | Slope-based logistic | Always flat |
|---|---|---|
| Accuracy | 0.917 | 0.982 |
| Macro-F1 | 0.138 | 0.110 |

- Windows: **152** scored (36 skipped when train had &lt;2 classes, usually all-flat stretches)
- Mean test flat share ≈ **98.2%**
- Beat always-flat on **accuracy** in only **~3%** of windows
- Beat always-flat on **Macro-F1** in **~74%** of windows (small absolute lift ≈ +0.03)

**Meaning:** accuracy still favors always-flat because most days are flat. On the fairer Macro-F1 score, the side try edges the baseline in most windows, but the lift is modest — not a breakthrough. Keep framing as exploratory.

Code: `Dhruvesh/change_bin_7d_rolling.py`  
Outputs: `Dhruvesh/change_bin_7d_outputs/rolling_60_26_step7/`  
Legacy one-shot split notebook: `Dhruvesh/change_bin_7d_logistic.ipynb`

## Trajectory / slope visuals

Overlapping 3-day slopes, 10-day average slope, and slope **angle** for slides.

**Meaning:** good for showing steepening during waves; usually concurrent with already-high cases, not a strong silent early-outbreak detector. Few historical waves also limit outbreak-classifier training.

Code/outputs: `Dhruvesh/trajectory_slope_exploration.ipynb`, `Dhruvesh/trajectory_slope_outputs/`

## Mentor framing (recommended)

1. Lead with **rolling dynamic panel** counts (60/90/120 vs persistence).  
2. Use **trajectory plots** as the visual / steepness layer.  
3. Call **change-bins** a v2 experiment until class imbalance is addressed.  
4. Be explicit about limits: modest forecast lift, sparse extremes, few big waves.

## Related notes

- Plan: `Dhruvesh/CHANGE_BIN_7D_PLAN.md`  
- Rolling panel design: `Dhruvesh/ROLLING_DYNAMIC_PANEL_PLAN.md`
