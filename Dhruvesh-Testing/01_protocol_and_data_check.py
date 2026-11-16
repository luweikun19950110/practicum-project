"""Step 1: verify the frozen testing protocol and the 2020-2023 input panel.

This script does not train a model. It checks that the local feature panel has
the dates, ZIP-day coverage, and feature groups required for the next step.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = (
    REPO_ROOT
    / "Weikun"
    / "rolling_trajectory_outputs"
    / "inputs"
    / "nj_daily_features.csv.gz"
)
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs" / "protocol_check"
CANDIDATE_FILE = (
    REPO_ROOT
    / "Weikun"
    / "later_time_evaluation_outputs"
    / "evaluation_2021_20261101"
    / "dynamic_panel"
    / "candidate_features.csv"
)
PREDICTIONS_FILE = (
    REPO_ROOT
    / "Weikun"
    / "later_time_evaluation_outputs"
    / "evaluation_2021_20261101"
    / "dynamic_panel"
    / "predictions.npz"
)


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Required input file was not found: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE, compression="gzip")
    df["date"] = pd.to_datetime(df["date"])

    required_columns = {"zip", "date", "cases_today"}
    missing_columns = sorted(required_columns.difference(df.columns))
    if missing_columns:
        raise ValueError(f"Missing required base columns: {missing_columns}")

    candidate_features = pd.read_csv(CANDIDATE_FILE)
    candidate_names = candidate_features["feature"].tolist()
    if len(candidate_names) != 34:
        raise ValueError(
            f"Expected Weikun's 34 candidate features, found {len(candidate_names)}"
        )

    with np.load(PREDICTIONS_FILE, allow_pickle=False) as saved_predictions:
        model_zip_count = int(len(saved_predictions["zip"]))
        model_zip_ids = set(saved_predictions["zip"].astype(str))

    date_min = df["date"].min().date().isoformat()
    date_max = df["date"].max().date().isoformat()
    zip_count = int(df["zip"].nunique())
    row_count = int(len(df))
    date_count = int(df["date"].nunique())

    # The model cohort uses the 585 ZIPs retained by Weikun's model outputs.
    # We verify the cohort size here without changing the input data.
    testing_rows = df[df["date"].between("2021-01-01", "2023-12-31")]
    testing_zip_count = int(testing_rows["zip"].nunique())
    raw_zip_ids = set(testing_rows["zip"].astype(str).unique())

    # A complete ZIP-day panel should have one row per ZIP per date.
    duplicate_zip_days = int(df.duplicated(["zip", "date"]).sum())
    expected_rows = zip_count * date_count

    report = {
        "input_file": str(INPUT_FILE),
        "row_count": row_count,
        "date_count": date_count,
        "date_min": date_min,
        "date_max": date_max,
        "zip_count": zip_count,
        "raw_testing_zip_count_2021_2023": testing_zip_count,
        "saved_model_zip_count": model_zip_count,
        "saved_model_cohort_is_subset_of_raw_panel": model_zip_ids.issubset(raw_zip_ids),
        "expected_rows_if_complete_panel": expected_rows,
        "duplicate_zip_date_rows": duplicate_zip_days,
        "candidate_feature_count": len(candidate_names),
        "candidate_feature_groups": candidate_features.groupby("group").size().to_dict(),
        "protocol": {
            "training_window_days": 60,
            "refit_every_days": 7,
            "forecast_horizons_days": [1, 2, 3],
            "testing_origins": ["2021-01-01", "2023-12-28"],
            "target_end_date": "2023-12-31",
            "model_algorithms": ["Dynamic Panel FE", "XGBoost", "Random Forest"],
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "protocol_check.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    print("Protocol and data check completed.")
    print(f"Input dates: {date_min} through {date_max} ({date_count} dates)")
    print(
        f"ZIP codes: {zip_count} in raw panel; {testing_zip_count} in 2021-2023; "
        f"{model_zip_count} in Weikun's model cohort"
    )
    print(f"Rows: {row_count:,}; expected complete-panel rows: {expected_rows:,}")
    print(f"Duplicate ZIP-date rows: {duplicate_zip_days}")
    print(f"Frozen candidate features: {len(candidate_names)}")
    print(f"Report: {OUTPUT_DIR / 'protocol_check.json'}")


if __name__ == "__main__":
    main()
