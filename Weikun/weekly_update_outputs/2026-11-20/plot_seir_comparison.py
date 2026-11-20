"""Create SEIR/RF comparison figures using matched saved prediction archives."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

dest = Path(__file__).resolve().parent
root = dest.parents[1]
seir = root / "seir_outputs/frozen_2020_test_2021_2023"
rf = root / "random_forest_trajectory_outputs/frozen_rf_2020_test_2021_2023"
figures = dest / "figures"
figures.mkdir(exist_ok=True)
navy, teal, bg, grid = "#15334F", "#00847E", "#EDF5FA", "#C5D8E0"
plt.rcParams.update({"font.family":"Arial","font.size":12,"text.color":navy,
                     "axes.labelcolor":navy,"xtick.color":navy,"ytick.color":navy})
metrics = {}
archives = {}
events = {}
warnings = {}
for name, folder in [("Random Forest",rf),("SEIR",seir)]:
    m = pd.read_csv(folder/"metrics.csv")
    m.insert(0,"model",name)
    metrics[name] = m
    with np.load(folder/"predictions.npz",allow_pickle=False) as data:
        archives[name] = {key:data[key] for key in data.files}
    events[name] = pd.read_csv(folder/"event_detection.csv",parse_dates=["event_date"])
    warnings[name] = pd.read_csv(folder/"warnings.csv",parse_dates=["forecast_origin"])
combined = pd.concat(metrics.values(),ignore_index=True)
combined.to_csv(dest/"SEIR_RF_comparison.csv",index=False)
dates = pd.DatetimeIndex(archives["SEIR"]["forecast_origins"])
np.testing.assert_array_equal(archives["SEIR"]["actual_cases"],archives["Random Forest"]["actual_cases"])
actual = archives["SEIR"]["actual_cases"]
def style(ax):
    ax.set_facecolor(bg)
    ax.spines[:].set_visible(False)
    ax.tick_params(length=0)
    ax.set_axisbelow(True)
    ax.grid(axis="y",color=grid,linewidth=.7)
def save(fig,name):
    if name == "yearly_detection_precision":
        fig.tight_layout(pad=1.2, rect=(0,0,1,.86))
    else:
        fig.tight_layout(pad=1.2)
    fig.savefig(figures/f"{name}.png",dpi=210,facecolor=bg)
    plt.close(fig)
def subplots(n=1,size=(9.2,3.25)):
    fig,axes=plt.subplots(1,n,figsize=size,facecolor=bg)
    for ax in np.atleast_1d(axes):
        style(ax)
    return fig,axes
palette={"Random Forest":navy,"SEIR":teal}
years=["2021","2022","2023"]
fig,axes=subplots(2,(9.2,3.35))
for ax,col,title in zip(axes,["event_recall","warning_precision"],["Event detection","Warning precision"]):
    for name,offset in [("Random Forest",-.18),("SEIR",.18)]:
        values=metrics[name].set_index("period").loc[years,col]
        bars=ax.bar(np.arange(3)+offset,values,.32,color=palette[name],label=name)
        ax.bar_label(bars,labels=[f"{v:.1%}" for v in values],padding=3,fontsize=10)
    ax.set(xticks=np.arange(3),xticklabels=years,ylim=(0,1.05),title=title)
    ax.yaxis.set_major_formatter(PercentFormatter(1))
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, fontsize=11)
save(fig,"yearly_detection_precision")

exposure=[]
with np.load(seir/"risk_scores.npz") as risk:
    for name in metrics:
        for period in ["2021–2023 overall"]+years:
            mask=np.ones(len(dates),bool) if "overall" in period else dates.year==int(period)
            row=metrics[name].set_index("period").loc[period]
            eligible=int(risk["eligible"][:,mask].sum())
            false=int(row.warnings-row.correct_warnings)
            exposure.append(dict(model=name,period=period,eligible_zip_days=eligible,
                                 false_warnings=false,false_per_1000=false*1000/eligible))
exposure=pd.DataFrame(exposure)
exposure.to_csv(dest/"warning_burden.csv",index=False)
lead=[]
fig,ax=subplots(size=(9.2,3.4))
for k,name in enumerate(metrics):
    e=events[name]
    values=[int((~e.detected).sum())]+[int(e.lead_days.eq(h).sum()) for h in [1,2,3]]
    assert sum(values)==4891
    left=0.
    for value,label,color in zip(values,["Missed","1 day","2 days","3 days"],["#A6BBC8",navy,teal,"#698D9E"]):
        share=value/4891
        ax.barh(k,share,left=left,height=.45,color=color,label=label if k==0 else None)
        if share>.05:
            ax.text(left+share/2,k,f"{share:.1%}",ha="center",va="center",color=navy if label=="Missed" else "white",fontweight="bold")
        lead.append(dict(model=name,category=label,count=value,share=share))
        left+=share
ax.set(yticks=[0,1],yticklabels=list(metrics),xlim=(0,1))
ax.invert_yaxis()
ax.xaxis.set_major_formatter(PercentFormatter(1))
ax.legend(loc="upper center",bbox_to_anchor=(.5,1.19),ncol=4,frameon=False)
save(fig,"lead_distribution")
pd.DataFrame(lead).to_csv(dest/"lead_distribution.csv",index=False)

horizon=[]
for name,a in archives.items():
    error=np.maximum(a["raw_predictions"],0)-actual
    for h in range(3):
        horizon.append(dict(model=name,horizon=h+1,MAE=float(np.abs(error[:,:,h]).mean()),
                            RMSE=float(np.sqrt(np.square(error[:,:,h]).mean())),
                            bias=float(error[:,:,h].mean())))
horizon=pd.DataFrame(horizon)
horizon.to_csv(dest/"horizon_errors.csv",index=False)
fig,axes=subplots(2,(9.2,3.3))
for ax,measure in zip(axes,["MAE","RMSE"]):
    for name in metrics:
        vals=horizon[horizon.model.eq(name)]
        ax.plot(vals.horizon,vals[measure],"o-",color=palette[name],label=name,lw=2)
    ax.set(xticks=[1,2,3],xlabel="Days ahead",ylabel="Cases per ZIP-day",title=measure)
axes[0].legend(frameon=False)
save(fig,"forecast_errors")

fig,ax=subplots(size=(9.2,3.4))
for name,a in archives.items():
    target_dates=dates+pd.Timedelta(days=3)
    forecast=pd.Series(a["raw_predictions"][:,:,2].sum(axis=0),index=target_dates).rolling(7).mean()
    ax.plot(forecast.loc["2021-11-15":"2022-03-19"],color=palette[name],label=f"{name} Day 3",lw=1.9)
truth=pd.Series(actual[:,:,2].sum(axis=0),index=target_dates).rolling(7).mean()
ax.plot(truth.loc["2021-11-15":"2022-03-19"],color="#B65B3B",label="Actual",lw=2)
ax.set(ylabel="Recorded cases per day")
ax.set_xticks(pd.to_datetime(["2021-12-01","2022-01-01","2022-02-01","2022-03-01"]),["Dec 1","Jan 1","Feb 1","Mar 1"])
ax.legend(loc="upper right",frameon=False,fontsize=10)
save(fig,"omicron_paths")

fig,ax=subplots(size=(9.2,3.2))
for name in metrics:
    row=metrics[name].iloc[0]
    vals=[row[f"moran_day_{h}"] for h in [1,2,3]]
    ax.plot([1,2,3],vals,"o-",color=palette[name],label=name,lw=2)
    for h,v in enumerate(vals):
        ax.text(h+1,v+.001,f"{v:.3f}",ha="center",color=palette[name],fontsize=11)
ax.set(xticks=[1,2,3],xlabel="Days ahead",ylabel="Mean residual Moran’s I",ylim=(0,.041))
ax.legend(frameon=False)
save(fig,"residual_moran")
params=pd.read_csv(seir/"parameters_2020.csv")
fig,ax=subplots(size=(9.2,3.1))
ax.hist(params.beta,bins=np.linspace(0,.25,26),color=teal,edgecolor=bg)
ax.set(xlabel="Fitted transmission parameter β per day",ylabel="ZIP count")
save(fig,"transmission_parameters")
# Compare pre-specified duration scenarios using the same evaluation.
sensitivity=[]
for label,folder in [("Latent 2d / infectious 4d",root/"seir_outputs/frozen_2020_sensitivity_L2_D4"),
                     ("Latent 3d / infectious 5d",seir),
                     ("Latent 5d / infectious 7d",root/"seir_outputs/frozen_2020_sensitivity_L5_D7")]:
    row=pd.read_csv(folder/"metrics.csv").iloc[0].to_dict()
    row["assumption"]=label
    sensitivity.append(row)
pd.DataFrame(sensitivity).to_csv(dest/"duration_sensitivity.csv",index=False)
metadata=dict(beta_zero=int(params.beta.eq(0).sum()),
              no_training_state=int(params.status.ne("fitted").sum()),
              beta_median=float(params.beta.median()),
              overall=combined[combined.period.str.contains("overall")].to_dict("records"),
              yearly=combined[combined.period.isin(years)].to_dict("records"),
              variants=combined[combined.period.isin(["Delta","Early Omicron (emergence through BA.1)"])].to_dict("records"),
              exposure=exposure.to_dict("records"),lead=lead,sensitivity=sensitivity,
              horizon=horizon.to_dict("records"))
(dest/"slide_data.json").write_text(json.dumps(metadata,indent=2),encoding="utf8")
print(combined[combined.period.str.contains("overall")].to_string(index=False))
