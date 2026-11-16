from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd

dest = Path(__file__).resolve().parent
root = dest.parents[1]
run = root / "random_forest_trajectory_outputs/frozen_rf_2020_test_2021_2023"
m = pd.read_csv(run / "metrics.csv")
events = pd.read_csv(run / "event_detection.csv", dtype={"zip": str}, parse_dates=["event_date"])
alerts = pd.read_csv(run / "warnings.csv", dtype={"zip": str}, parse_dates=["forecast_origin", "matched_event_date"])
navy, teal, bg, muted = "#15334F", "#00847E", "#EDF5FA", "#506981"
plt.rcParams.update({"font.family":"Arial","font.size":12,"text.color":navy,"axes.labelcolor":navy,"xtick.color":navy,"ytick.color":navy})
def canvas(size=(9, 3.1)):
    fig, ax = plt.subplots(figsize=size, facecolor=bg)
    ax.set_facecolor(bg)
    ax.spines[:].set_visible(False)
    ax.tick_params(length=0)
    ax.set_axisbelow(True)
    return fig, ax
def save(fig, name):
    fig.tight_layout(pad=1.1)
    fig.savefig(dest / f"{name}.png", dpi=210)
    plt.close(fig)

years = m.iloc[1:4].copy()
with np.load(run / "risk_scores.npz") as z:
    dates = pd.DatetimeIndex(z["forecast_origins"])
    eligible, scores, ids = z["eligible"], z["risk_score"], z["zip"]
    years["eligible"] = [int(eligible[:, dates.year == y].sum()) for y in (2021, 2022, 2023)]
years["false_alerts"] = years.warnings - years.correct_warnings
years["false_per_1000"] = 1000 * years.false_alerts / years.eligible
fig, ax = canvas()
x = np.arange(3)
for col, label, color, offset in [("event_recall","Event detection",navy,-.18),("warning_precision","Warning precision",teal,.18)]:
    bars = ax.bar(x+offset, years[col], .32, color=color, label=label)
    ax.bar_label(bars, labels=[f"{v:.1%}" for v in years[col]], padding=4)
ax.set(xticks=x, xticklabels=years.period, ylim=(0, 1.03))
ax.yaxis.set_major_formatter(PercentFormatter(1))
ax.grid(axis="y", color="#C8DCE3")
ax.legend(loc="upper center", bbox_to_anchor=(.5,1.18), ncol=2, frameon=False)
save(fig, "frozen_rf_yearly_detection")

events["year"] = events.event_date.dt.year
counts = pd.crosstab(events.year, events.lead_days.fillna(0)).reindex(index=[2021,2022,2023],columns=[0,1,2,3],fill_value=0)
assert counts.sum(axis=1).tolist() == years.events.tolist()
fig, ax = canvas((9,3.0))
left = np.zeros(3)
for lead, label, color in [(0,"Missed","#A9BFCD"),(1,"1 day",navy),(2,"2 days",teal),(3,"3 days","#5F748A")]:
    share = counts[lead]/counts.sum(axis=1)
    ax.barh(x, share, left=left, color=color, label=label, height=.48)
    for i, v in enumerate(share):
        if v >= .065:
            ax.text(left[i]+v/2,i,f"{v:.1%}",ha="center",va="center",color="white" if lead else navy,weight="bold")
    left += share.to_numpy()
ax.set(yticks=x,yticklabels=counts.index,xlim=(0,1))
ax.invert_yaxis()
ax.xaxis.set_major_formatter(PercentFormatter(1))
ax.legend(loc="upper center",bbox_to_anchor=(.5,1.2),frameon=False,ncol=4)
save(fig,"frozen_rf_lead_distribution")

with np.load(run / "predictions.npz") as z:
    assert np.array_equal(ids,z["zip"])
    np.testing.assert_array_equal(dates.to_numpy(dtype="datetime64[D]"),z["forecast_origins"].astype("datetime64[D]"))
    pred, actual = z["raw_predictions"], z["actual_cases"]
# Same ZIP and calendar year. Require a lead of 2 days and a missed event
# with all three eligible scores at or below the fixed warning threshold.
lookup = {pd.Timestamp(d): i for i,d in enumerate(dates)}
success = alerts.loc[alerts.true_warning & alerts.lead_days.eq(2) & alerts.matched_event_date.dt.year.eq(2022)]
misses = events.loc[~events.detected & events.year.eq(2022)]
example = None
for win in success.itertuples(index=False):
    z = np.flatnonzero(ids==win.zip)[0]
    for miss in misses.loc[misses.zip.eq(win.zip)].itertuples(index=False):
        k = lookup[miss.event_date]
        prior = np.arange(k-3,k)
        if eligible[z,prior].all() and (scores[z,prior] <= 0).all():
            example = (z,win,miss)
            break
    if example is not None:
        break
assert example is not None
z, win, miss = example
fig, axs = plt.subplots(1,2,figsize=(9.2,3.15),sharey=True,facecolor=bg)
for ax, title, origin, confirmed in zip(
    axs, ["Alert issued 2 days before confirmation","Missed event"], 
    [win.forecast_origin,miss.event_date-pd.Timedelta(days=2)],
    [win.matched_event_date,miss.event_date]):
    k = lookup[origin]
    ax.set_facecolor(bg)
    ax.spines[:].set_visible(False)
    ax.tick_params(length=0)
    ax.set_axisbelow(True)
    ax.grid(axis="y",color="#C8DCE3")
    ax.plot(np.arange(-3,4),actual[z,k-4:k+3,0],marker="o",color=navy,label="Actual")
    ax.plot([1,2,3],pred[z,k],marker="o",ls="--",color=teal,label="Forecast")
    ax.axvline(0,color=muted,lw=1,ls=":")
    ax.axvline((confirmed-origin).days,color="#BB533A",lw=1)
    ax.set(xticks=np.arange(-3,4),xlabel="Day relative to forecast origin",title=title)
    ax.text(.02,.96,f"{origin:%b %d} origin · score {scores[z,k]:+.3f}",transform=ax.transAxes,va="top",fontsize=10)
axs[0].set_ylabel("Recorded cases")
axs[0].set_ylim(bottom=0)
handles, labels = axs[0].get_legend_handles_labels()
from matplotlib.lines import Line2D
handles.append(Line2D([0],[0],color="#BB533A"))
fig.legend(handles,labels+["Event confirmed"],loc="upper center",frameon=False,ncol=3)
fig.subplots_adjust(left=.076,right=.98,bottom=.20,top=.72,wspace=.20)
fig.savefig(dest/"frozen_rf_zip_examples.png",dpi=210)
plt.close(fig)
extra = dict(years=years.to_dict("records"), lead_counts=counts.values.tolist(),
             zip=str(ids[z]), detected_date=str(win.matched_event_date.date()), missed_date=str(miss.event_date.date()),
             missed_max_score=float(scores[z,lookup[miss.event_date]-3:lookup[miss.event_date]].max()))
(dest/"frozen_rf_slide_metrics.json").write_text(json.dumps(extra,indent=2),encoding="utf8")
