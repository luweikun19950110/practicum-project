import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
data=pd.read_csv("Weikun/random_forest_trajectory_outputs/frozen_rf_2020_test_2021/metrics.csv")
x=np.arange(3)
plt.rcParams.update({"font.family":"Arial","font.size":12,"text.color":"#15334f","axes.labelcolor":"#15334f","xtick.color":"#15334f","ytick.color":"#15334f"})
fig,ax=plt.subplots(figsize=(9,2.8),facecolor="#edf5fa")
ax.set_facecolor("#edf5fa")
for field,offset,color,label in [("event_recall",-.17,"#15334f","Event detection"),("warning_precision",.17,"#008980","Warning precision")]:
    bars=ax.bar(x+offset,100*data[field],.30,color=color,label=label,zorder=3)
    ax.bar_label(bars,fmt="%.1f%%",padding=3,fontsize=11,color="#15334f")
ax.set_xticks(x,["2021 overall","Delta window","Omicron emergence"])
ax.set_ylim(0,106)
ax.set_yticks([0,25,50,75,100],[f"{i}%" for i in [0,25,50,75,100]])
ax.grid(axis="y",color="#c1d4db",linewidth=.7)
ax.tick_params(length=0)
ax.spines[:].set_visible(False)
ax.legend(loc="upper center",bbox_to_anchor=(.5,1.15),ncol=2,frameon=False)
fig.subplots_adjust(left=.075,right=.99,top=.83,bottom=.14)
fig.savefig(Path("Weikun/weekly_update_outputs/2026-11-14")/"2021_warning_rates.png",dpi=230)
