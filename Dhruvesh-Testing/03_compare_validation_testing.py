"""Step 3: compare Weikun's 2020 validation with Dhruvesh's 2021-2023 testing.

This script does not retrain models. It combines the saved trajectory summaries
using the same metrics and labels the periods clearly.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DH_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = DH_ROOT / "outputs" / "comparisons"

VALIDATION_RUNS = {
    "Dynamic Panel FE": REPO_ROOT / "Weikun" / "rolling_trajectory_outputs" / "rolling60_weekly_development_20261027" / "trajectory_scores_by_period.csv",
    "XGBoost": REPO_ROOT / "Weikun" / "xgboost_trajectory_outputs" / "xgb60_weekly_development_20261027" / "trajectory_scores_by_period.csv",
    "Random Forest": REPO_ROOT / "Weikun" / "random_forest_trajectory_outputs" / "rf60_weekly_development_20261027" / "trajectory_scores_by_period.csv",
}

TESTING_RUNS = {
    "Dynamic Panel FE": DH_ROOT / "outputs" / "model_runs_2021_2023" / "dynamic_panel" / "trajectory_scores_by_period.csv",
    "XGBoost": DH_ROOT / "outputs" / "model_runs_2021_2023" / "xgboost" / "trajectory_scores_by_period.csv",
    "Random Forest": DH_ROOT / "outputs" / "model_runs_2021_2023" / "random_forest" / "trajectory_scores_by_period.csv",
}


def load_period(path: Path, model: str, period_label: str) -> pd.DataFrame:
    data = pd.read_csv(path)
    row = data.loc[(data["scope"] == "overall") & (data["period"] == "all")].copy()
    if len(row) != 1:
        raise ValueError(f"Expected one overall row in {path}, found {len(row)}")
    row.insert(0, "period_label", period_label)
    row.insert(0, "model", model)
    return row


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for model, path in VALIDATION_RUNS.items():
        rows.append(load_period(path, model, "2020 validation"))
    for model, path in TESTING_RUNS.items():
        rows.append(load_period(path, model, "2021-2023 testing"))

    comparison = pd.concat(rows, ignore_index=True)
    columns = [
        "period_label",
        "model",
        "forecast_origins",
        "regions",
        "paths",
        "RMSE",
        "trajectory_MAE",
        "mean_bias",
        "direction_agreement",
        "two_step_shape_agreement",
        "change_MAE",
        "acceleration_MAE",
    ]
    comparison = comparison[columns].sort_values(["period_label", "model"])
    comparison.to_csv(OUTPUT_DIR / "validation_vs_testing_overall.csv", index=False)

    # Easier-to-read long format for charts and presentation tables.
    metric_columns = ["trajectory_MAE", "RMSE", "direction_agreement", "two_step_shape_agreement"]
    long = comparison.melt(
        id_vars=["period_label", "model"],
        value_vars=metric_columns,
        var_name="metric",
        value_name="value",
    )
    long.to_csv(OUTPUT_DIR / "validation_vs_testing_metrics_long.csv", index=False)

    # A compact visual: one panel per metric, validation versus testing.
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    colors = {"Dynamic Panel FE": "#64748b", "XGBoost": "#2563eb", "Random Forest": "#087f78"}
    titles = {
        "trajectory_MAE": "Trajectory MAE (lower is better)",
        "RMSE": "RMSE (lower is better)",
        "direction_agreement": "Endpoint direction agreement",
        "two_step_shape_agreement": "Two-step shape agreement",
    }
    for ax, metric in zip(axes.flat, metric_columns):
        plot_data = comparison.pivot(index="period_label", columns="model", values=metric)
        plot_data = plot_data.reindex(["2020 validation", "2021-2023 testing"])
        plot_data.plot(
            kind="bar",
            ax=ax,
            color=[colors[c] for c in ["Dynamic Panel FE", "XGBoost", "Random Forest"]],
            legend=False,
        )
        ax.set_title(titles[metric])
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.grid(axis="y", alpha=0.25)
        ax.set_axisbelow(True)
        ax.tick_params(axis="x", rotation=0)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.955), ncol=3, frameon=False)
    fig.suptitle("Validation versus later testing", y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.89])
    fig.savefig(OUTPUT_DIR / "validation_vs_testing_metrics.png", dpi=200)
    plt.close(fig)

    print(comparison.to_string(index=False))
    print(f"\nSaved comparison files to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
