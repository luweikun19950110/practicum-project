"""Dhruvesh feature-analysis companion to Weikun's diagnostics.

This script intentionally reuses Weikun's saved, verified outputs instead of
refitting the models. Each numbered section is written like a notebook cell:
the comment explains what the section does in plain language, and the outputs
are saved for later presentation work.
"""

from pathlib import Path
import json
import textwrap
from html import escape

import numpy as np
import pandas as pd


# CELL 1 — Set paths and create a clean output folder.
# In simple terms: this tells the analysis where Weikun's results live and
# where Dhruvesh's new tables and figures should be saved.
ROOT = Path(__file__).resolve().parents[1]
WEIKUN = ROOT / "Weikun"
OUT = ROOT / "Dhruvesh" / "feature_analysis_outputs"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "figures").mkdir(exist_ok=True)

DIAG = WEIKUN / "feature_diagnostics_outputs" / "validation2020_20261102"
LAG = WEIKUN / "mentor_followup_outputs" / "2026-11-04" / "lag_analysis"
SEL = WEIKUN / "individual_feature_selection_outputs" / "three_methods_20261026T153141838619Z"


# CELL 2 — Load the feature definitions and the already-computed diagnostics.
# In simple terms: we are not inventing a new feature list; we are reading the
# same 34 engineered features and the same 2020 validation results.
protocol = json.loads((DIAG / "protocol.json").read_text())
families = protocol["families"]
feature_to_group = {feature: group for group, features in families.items() for feature in features}

importance = pd.read_csv(DIAG / "training_importance_summary.csv")
importance_h = pd.read_csv(DIAG / "training_importance_by_horizon.csv")
importance_m = pd.read_csv(DIAG / "training_importance_by_month.csv")
ablation = pd.read_csv(DIAG / "group_ablation_summary.csv")
ablation_h = pd.read_csv(DIAG / "group_ablation_by_horizon.csv")
correlations = pd.read_csv(DIAG / "high_correlation_pairs.csv")
selection = pd.read_csv(SEL / "feature_inclusion_comparison.csv")
lag = pd.read_csv(LAG / "monthly_lag_relationships.csv")


# CELL 3 — Make a feature inventory table.
# In simple terms: this counts how many features belong to each conceptual
# group, which helps explain the model inputs before discussing importance.
inventory = (
    pd.DataFrame(
        [(group, feature) for group, features in families.items() for feature in features],
        columns=["feature_group", "feature"],
    )
    .assign(feature_count=lambda d: d.groupby("feature_group")["feature"].transform("size"))
)
inventory.drop_duplicates("feature_group").sort_values("feature_group").to_csv(
    OUT / "feature_inventory.csv", index=False
)


# CELL 4 — Rank individual features and aggregate importance by group.
# In simple terms: tree importance asks what the model used most often. We also
# add importance within groups so a group with many correlated variables is not
# judged only by one column.
importance["feature_group"] = importance["feature"].map(feature_to_group).fillna("identity")
importance.to_csv(OUT / "feature_importance_clean.csv", index=False)

top10 = (
    importance.sort_values(["model", "mean"], ascending=[True, False])
    .groupby("model", as_index=False, group_keys=False)
    .head(10)
)
top10.to_csv(OUT / "top10_features_by_model.csv", index=False)

group_importance = (
    importance.groupby(["model", "feature_group"], as_index=False)["mean"].sum()
    .rename(columns={"mean": "total_normalized_importance"})
)
group_importance["share_of_model_importance"] = group_importance.groupby("model")[
    "total_normalized_importance"
].transform(lambda s: s / s.sum())
group_importance.to_csv(OUT / "importance_by_feature_group.csv", index=False)


# CELL 5 — Measure whether importance is stable across forecast horizons.
# In simple terms: a feature that ranks highly for Day 1, Day 2, and Day 3 is a
# more consistent story than a feature that matters only at one horizon.
importance_h["feature_group"] = importance_h["feature"].map(feature_to_group).fillna("identity")
importance_h["rank"] = importance_h.groupby(["model", "horizon"])[
    "normalized_training_importance"
].rank(method="min", ascending=False)
top_by_horizon = importance_h[importance_h["rank"] <= 10].copy()
top_by_horizon.to_csv(OUT / "top10_features_by_model_horizon.csv", index=False)

stability = (
    importance_h.assign(is_top5=importance_h["rank"] <= 5)
    .groupby(["model", "feature"], as_index=False)
    .agg(
        top5_horizons=("is_top5", "sum"),
        mean_horizon_importance=("normalized_training_importance", "mean"),
    )
)
stability["feature_group"] = stability["feature"].map(feature_to_group).fillna("identity")
stability.sort_values(["model", "top5_horizons", "mean_horizon_importance"], ascending=[True, False, False]).to_csv(
    OUT / "horizon_stability.csv", index=False
)


# CELL 6 — Compare importance over months.
# In simple terms: this checks whether the model relied on the same signals in
# April, summer, and autumn, rather than assuming feature behavior was constant.
importance_m["feature_group"] = importance_m["feature"].map(feature_to_group).fillna("identity")
monthly_group = (
    importance_m.groupby(["model", "month", "feature_group"], as_index=False)[
        "normalized_training_importance"
    ]
    .sum()
    .rename(columns={"normalized_training_importance": "group_importance"})
)
monthly_group.to_csv(OUT / "importance_by_group_and_month.csv", index=False)

monthly_top = (
    importance_m.sort_values(["model", "month", "normalized_training_importance"], ascending=[True, True, False])
    .groupby(["model", "month"], as_index=False, group_keys=False)
    .head(5)
)
monthly_top.to_csv(OUT / "top5_features_by_model_month.csv", index=False)


# CELL 7 — Examine ablation by model and forecast horizon.
# In simple terms: remove one group, refit, and see how much the error changes.
# Positive delta means that removing the group made predictions worse, so the
# group helped. A confidence interval crossing zero means the change is uncertain.
ablation["feature_group"] = ablation["drop_group"]
ablation["interpretation"] = np.where(
    ablation["relative_increase_pct"] > 0,
    "removing group increased error",
    "removing group did not increase error",
)
ablation.to_csv(OUT / "ablation_summary_clean.csv", index=False)
ablation_h["feature_group"] = ablation_h["drop_group"]
ablation_h.to_csv(OUT / "ablation_by_horizon_clean.csv", index=False)


# CELL 8 — Summarize feature-selection consensus.
# In simple terms: forward, backward, and stepwise selection are separate ways
# to search for a smaller model. Agreement is useful; disagreement shows that
# correlated features can substitute for one another.
methods = ["BACKWARD", "FORWARD", "STEPWISE"]
selection["selected_count"] = selection[methods].fillna(False).astype(bool).sum(axis=1)
selection["selection_consensus"] = np.select(
    [selection["selected_count"] == 3, selection["selected_count"] == 2, selection["selected_count"] == 1],
    ["all three methods", "two methods", "one method"],
    default="not selected",
)
selection["feature_group"] = selection["feature"].map(feature_to_group).fillna("identity")
selection.sort_values(["selected_count", "feature_group", "feature"], ascending=[False, True, True]).to_csv(
    OUT / "feature_selection_consensus.csv", index=False
)


# CELL 8b — Make the redundancy audit presentation-friendly.
# In simple terms: highly correlated features can split importance across one
# another, so a single feature's rank should not be interpreted in isolation.
label_map = {
    "cases_today": "Current cases",
    "cases_mean_7d": "7-day average cases",
    "cases_mean_14d": "14-day average cases",
    "cases_lag_1": "Cases 1 day earlier",
    "cases_lag_7": "Cases 7 days earlier",
    "cases_lag_14": "Cases 14 days earlier",
    "nj_covid_pressure_7d": "7-day commuting pressure",
    "nj_covid_pressure_14d": "14-day commuting pressure",
    "case_rate_7d_per_100k": "7-day case rate",
    "case_rate_14d_per_100k": "14-day case rate",
    "case_std_7d": "7-day variability",
    "case_std_14d": "14-day variability",
}
correlations["feature_a_plain"] = correlations["feature_a"].map(label_map).fillna(correlations["feature_a"])
correlations["feature_b_plain"] = correlations["feature_b"].map(label_map).fillna(correlations["feature_b"])
correlations.to_csv(OUT / "high_correlation_pairs_clean.csv", index=False)


# CELL 9 — Preserve the lag relationship results in presentation-friendly form.
# In simple terms: this is a descriptive check of whether earlier cases are
# associated with current cases differently in May, August, and November.
month_names = {4: "April", 5: "May", 8: "August", 11: "November"}
lag["month_name"] = lag["month"].map(month_names).fillna(lag["month"].astype(str))
lag["ci_includes_zero"] = (lag["ci95_low"] <= 0) & (lag["ci95_high"] >= 0)
lag.to_csv(OUT / "lag_relationships_clean.csv", index=False)


# CELL 10 — Create presentation-ready tables with plain-English labels.
# In simple terms: these are the numbers we can copy into slide notes without
# making the audience decode variable names.
label_map = {
    "cases_today": "Current cases",
    "cases_mean_7d": "7-day average cases",
    "cases_mean_14d": "14-day average cases",
    "cases_lag_1": "Cases 1 day earlier",
    "cases_lag_7": "Cases 7 days earlier",
    "cases_lag_14": "Cases 14 days earlier",
    "nj_covid_pressure_7d": "7-day commuting pressure",
    "nj_covid_pressure_14d": "14-day commuting pressure",
    "case_rate_7d_per_100k": "7-day case rate",
    "case_rate_14d_per_100k": "14-day case rate",
    "case_std_7d": "7-day variability",
    "case_std_14d": "14-day variability",
}
top10["plain_feature"] = top10["feature"].map(label_map).fillna(top10["feature"])
top10.to_csv(OUT / "top10_features_by_model_plain_english.csv", index=False)


# CELL 11-15 — Create presentation-ready SVG charts.
# In simple terms: the runtime does not include a plotting package, so these
# charts are written as editable SVG files. PowerPoint can insert SVG directly,
# and the figures remain sharp when resized.
def svg_start(width, height, title, subtitle=""):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="white"/>',
            f'<text x="40" y="34" font-family="Arial" font-size="20" font-weight="700" fill="#0f172a">{escape(title)}</text>',
            f'<text x="40" y="56" font-family="Arial" font-size="12" fill="#475569">{escape(subtitle)}</text>']

def svg_end(lines):
    lines.append('</svg>')
    return '\n'.join(lines)

def hbar_svg(rows, path, title, subtitle, width=1100, row_height=30, color="#2563eb", max_label=220):
    height = 90 + row_height * len(rows)
    lines = svg_start(width, height, title, subtitle)
    chart_x, chart_w = max_label + 40, width - max_label - 100
    max_value = max(float(v) for _, v in rows) or 1
    for i, (label, value) in enumerate(rows):
        y = 88 + i * row_height
        bar_w = chart_w * float(value) / max_value
        lines += [f'<text x="{chart_x-12}" y="{y+16}" text-anchor="end" font-family="Arial" font-size="12" fill="#334155">{escape(str(label))}</text>',
                  f'<rect x="{chart_x}" y="{y}" width="{bar_w:.1f}" height="18" rx="3" fill="{color}"/>',
                  f'<text x="{chart_x+bar_w+8:.1f}" y="{y+14}" font-family="Arial" font-size="11" fill="#334155">{float(value):.3f}</text>']
    Path(path).write_text(svg_end(lines), encoding="utf-8")

tree = top10[top10["model"].isin(["Random Forest", "XGBoost"])].copy()
for model, d in tree.groupby("model"):
    d = d.sort_values("mean", ascending=False).head(10)
    hbar_svg(list(zip(d["plain_feature"], d["mean"])), OUT / "figures" / f"01_top_features_{model.lower().replace(' ', '_')}.svg", f"Top features used by {model}", "Mean normalized training importance", color="#0f766e" if model == "Random Forest" else "#2563eb")

group_rows = []
for model, d in group_importance.groupby("model"):
    for _, row in d.sort_values("share_of_model_importance", ascending=False).iterrows():
        group_rows.append((f"{model}: {row['feature_group'].replace('_', ' ')}", row["share_of_model_importance"]))
hbar_svg(group_rows, OUT / "figures/02_group_importance.svg", "Importance aggregated by feature group", "Normalized training importance summed within each group", color="#475569")

ab_rows = []
for _, row in ablation.sort_values(["model", "relative_increase_pct"], ascending=[True, False]).iterrows():
    ab_rows.append((f"{row['model'].replace(' FE','')}: remove {row['drop_group'].replace('_',' ')}", row["relative_increase_pct"]))
hbar_svg(ab_rows, OUT / "figures/03_group_ablation.svg", "What happens when a feature group is removed?", "Positive values mean MAE increased after removal; zero means no change", color="#b91c1c")

ab_h_rows = []
for _, row in ablation_h.sort_values(["model", "horizon", "drop_group"]).iterrows():
    ab_h_rows.append((f"{row['model'].replace(' FE','')[:3]} H{int(row['horizon'])} {row['drop_group'].replace('_',' ')[:6]}", row["delta_MAE_DROP_minus_FULL"]))
hbar_svg(ab_h_rows, OUT / "figures/04_ablation_by_horizon.svg", "Ablation effect by model and forecast horizon", "Positive values mean removing the group worsened MAE", color="#7c3aed")

lag_rows = []
for _, row in lag.sort_values(["month", "lag"]).iterrows():
    lag_rows.append((f"{row['month_name']} — lag {int(row['lag'])} days", row["within_zip_slope"]))
hbar_svg(lag_rows, OUT / "figures/05_monthly_lag_relationships.svg", "Monthly lag relationships", "Within-ZIP slopes; confidence intervals are in lag_relationships_clean.csv", color="#0f766e")

# CELL 15b — Create compact, nearly square versions for PowerPoint.
# In simple terms: these versions are narrower and taller so they can sit in a
# centered card or a two-column layout without looking stretched.
for model, d in tree.groupby("model"):
    d = d.sort_values("mean", ascending=False).head(10)
    hbar_svg(
        list(zip(d["plain_feature"], d["mean"])),
        OUT / "figures" / f"01_top_features_{model.lower().replace(' ', '_')}_compact.svg",
        f"Top features: {model}",
        "Mean normalized training importance",
        width=760,
        row_height=44,
        max_label=245,
        color="#0f766e" if model == "Random Forest" else "#2563eb",
    )
hbar_svg(
    ab_rows,
    OUT / "figures/03_group_ablation_compact.svg",
    "Feature-group ablation",
    "Positive = prediction error increased after removal",
    width=760,
    row_height=48,
    max_label=285,
    color="#b91c1c",
)
hbar_svg(
    lag_rows,
    OUT / "figures/05_monthly_lag_relationships_compact.svg",
    "Monthly lag relationships",
    "Descriptive within-ZIP slopes",
    width=760,
    row_height=58,
    max_label=245,
    color="#0f766e",
)


# CELL 16 — Write a concise results memo for slide development.
# In simple terms: this converts the calculations into defensible presentation
# language and records the limitations alongside the numbers.
rf_top = top10[top10["model"] == "Random Forest"].sort_values("mean", ascending=False).head(5)
xgb_top = top10[top10["model"] == "XGBoost"].sort_values("mean", ascending=False).head(5)
local_ab = ablation[ablation["drop_group"] == "local_case_history"].set_index("model")
pressure_ab = ablation[ablation["drop_group"] == "commuting_pressure"].set_index("model")
consensus = selection[selection["selected_count"] == 3]["feature"].map(label_map).fillna(selection[selection["selected_count"] == 3]["feature"]).tolist()

memo = f"""# Dhruvesh Deep Feature Analysis Results

Generated from Weikun's saved 2020 validation diagnostics. No Weikun files were modified and no model was refit by this script.

## What was analyzed

- 34 candidate engineered features across 585 ZIP codes.
- 243 forecast dates, three horizons, 60-day rolling windows, weekly refits.
- Tree-model training importance, group ablation, horizon stability, monthly stability, feature-selection consensus, correlation, and lag relationships.

## Main numbers

### Top tree-model features

Random Forest top five: {', '.join(rf_top['plain_feature'].tolist())}.

XGBoost top five: {', '.join(xgb_top['plain_feature'].tolist())}.

### Group ablation

Removing local case history changed MAE by approximately {local_ab.loc['Dynamic Panel FE','relative_increase_pct']:.1f}% for Dynamic Panel FE, {local_ab.loc['XGBoost','relative_increase_pct']:.1f}% for XGBoost, and {local_ab.loc['Random Forest','relative_increase_pct']:.1f}% for Random Forest.

Removing commuting pressure changed MAE by approximately {pressure_ab.loc['Dynamic Panel FE','relative_increase_pct']:.1f}%, {pressure_ab.loc['XGBoost','relative_increase_pct']:.1f}%, and {pressure_ab.loc['Random Forest','relative_increase_pct']:.1f}%, respectively. These small effects have uncertainty intervals crossing zero.

### Interpretation

Recent local case history is the clearest predictive signal. The tree importance results and ablation results agree on that broad conclusion, but they measure different things. Importance describes how a model used variables during training; ablation measures the change in forecast error after removing a group.

Commuting pressure remains a plausible connected-region feature, but this validation does not show a large incremental predictive gain after local case history is already present. This is not a causal conclusion about commuting or disease transmission.

### Selection and redundancy

Forward, backward, and stepwise selection all retained: {', '.join(consensus) if consensus else 'no single feature across all three methods'}. The raw feature audit also shows very high correlation between the 7-day and 14-day case means (about 0.98), and between the 7-day and 14-day pressure variables (about 0.99). This is why model importance can be shared across related features.

Monthly lag results should be described as associations. The August lag relationships are weaker than May/November in the current diagnostic, but the analysis is exploratory and does not establish a formal between-month causal or significance claim.

## Presentation-ready figures

1. `figures/01_top_features_random_forest.svg` and `01_top_features_xgboost.svg` — use for the top-feature slide.
2. `figures/02_group_importance.svg` — use to show importance aggregated by conceptual group.
3. `figures/03_group_ablation.svg` — strongest slide for predictive contribution.
4. `figures/04_ablation_by_horizon.svg` — optional deeper slide or backup visual.
5. `figures/05_monthly_lag_relationships.svg` — use for time-varying feature behavior.

Supporting tables: `feature_selection_consensus.csv`, `high_correlation_pairs_clean.csv`, `horizon_stability.csv`, and `importance_by_group_and_month.csv`.

## Important limitation

These are exploratory 2020 validation diagnostics from a previously inspected period. They are not an untouched final test and do not establish causal effects.
"""
(OUT / "RESULTS_SUMMARY.md").write_text(textwrap.dedent(memo), encoding="utf-8")

print(f"Generated feature-analysis outputs in: {OUT}")
print(f"Generated {len(list((OUT / 'figures').glob('*.svg')))} presentation-ready SVG figures")
