# Results summary (honest read)

Last updated: 2026-11-01

## Rolling dynamic panel (main forecasting result)

Short-horizon **case counts** with rolling FE OLS, scored vs persistence (“future = today”).

| Train window | Model MAE (day-ahead) | Persistence MAE | Share of windows beating persistence |
|---|---|---|---|
| 60 days | 0.73 | 0.78 | 52% |
| 90 days | 0.68 | 0.72 | 53% |
| 120 days | 0.67 | 0.71 | 64% |

**Meaning:** the model is a bit better than persistence, more often with longer training. The lift is **modest**, not a breakthrough. This is still a legitimate forecasting baseline for the mentor story.

Code/outputs: `Weikun/rolling_dynamic_panel/window_{60,90,120}days/`

## 7-day change-bin logistic (threat experiment)

Classifies relative move by day t+7 into bins; base &lt; 10 forced to `flat`.

| Model | Accuracy | Macro-F1 |
|---|---|---|
| Logistic (balanced) | 0.85 | 0.12 |
| Always predict `flat` | ~1.00 | 0.12 |

About **98%** of labels are `flat` (quiet ZIP-days + softening rule). Extreme up/down bins are rare.

**Meaning:** accuracy is misleading. The classifier does **not** clearly beat “everything is flat.” Treat this as an early experiment; an active-ZIP filter (e.g. only base ≥ 10 for learning non-flat classes) is the next fix if we continue this track.

Code/outputs: `Dhruvesh/change_bin_7d_logistic.ipynb`, `Dhruvesh/change_bin_7d_outputs/`

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
