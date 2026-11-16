from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

here = Path(__file__).resolve().parent
root = here.parents[1]
archive = root / "random_forest_trajectory_outputs/frozen_rf_2020_test_2021_2023/predictions.npz"
with np.load(archive, allow_pickle=False) as saved:
    dates = pd.DatetimeIndex(saved["forecast_origins"])
    actual = saved["actual_cases"].sum(axis=0)
    forecast = np.maximum(saved["raw_predictions"], 0).sum(axis=0)
start = pd.Timestamp("2022-01-01")
mask = (dates >= start) & (dates < start + pd.Timedelta(days=28))
change = actual[mask, 2] - actual[mask, 0]
estimated = forecast[mask, 2] - forecast[mask, 0]
decline = change < 0
hits = int((decline & (estimated < 0)).sum())
predicted = int((estimated < 0).sum())
count = int(decline.sum())
mae = float(np.abs(change[decline] - estimated[decline]).mean())
rapid = change <= -0.20 * actual[mask, 0]
rapid_count = int(rapid.sum())
rapid_hits = int((rapid & (estimated < 0)).sum())
rapid_magnitude_hits = int((rapid & (estimated <= -0.20 * forecast[mask, 0])).sum())
metrics = dict(hits=hits, predicted=predicted, declines=count, mae=mae,
               rapid_count=rapid_count, rapid_hits=rapid_hits, rapid_magnitude_hits=rapid_magnitude_hits)
print(json.dumps(metrics))
target = dates + pd.Timedelta(days=3)
observed = pd.Series(actual[:, 2], index=target).rolling(7).mean()
estimate = pd.Series(forecast[:, 2], index=target).rolling(7).mean()
plt.rcParams.update({"font.family": "Arial", "font.size": 11, "text.color": "#15334f"})
fig, ax = plt.subplots(figsize=(6.4, 3.55), facecolor="#EDF5FA")
ax.set_facecolor("#EDF5FA")
ax.plot(observed.loc["2021-11-14":"2022-03-12"], color="#15334F", lw=2, label="Actual")
ax.plot(estimate.loc["2021-11-14":"2022-03-12"], color="#00847E", lw=2, label="Day 3 forecast")
ax.axvspan(start, start + pd.Timedelta(days=27), color="#DBEBED", zorder=0)
for stamp, label, align in [("2021-11-19", "Booster eligibility\nexpanded (Nov 19)", "left"),
                             ("2022-03-07", "NJ school mask\nmandate ends (Mar 7)", "right")]:
    t = pd.Timestamp(stamp)
    ax.axvline(t, color="#8196A7", lw=.9, ls="--")
    ax.text(t, 4950, label, ha=align, va="top", fontsize=9)
ax.set_ylim(0, 5150)
ax.set_ylabel("Recorded cases per day")
ax.set_xticks(pd.to_datetime(["2021-12-01", "2022-01-01", "2022-02-01", "2022-03-01"]), ["Dec 1", "Jan 1", "Feb 1", "Mar 1"])
ax.spines[:].set_visible(False)
ax.tick_params(length=0, colors="#15334F")
ax.grid(axis="y", color="#BFD1DA", linewidth=.7)
ax.legend(loc="upper center", bbox_to_anchor=(.5,1.15), ncol=2, frameon=False)
fig.tight_layout()
fig.savefig(here / "Omicron_Postpeak_Decline.png", dpi=220)
