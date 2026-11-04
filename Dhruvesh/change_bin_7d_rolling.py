"""Rolling-window evaluation for the 7-day change-bin logistic experiment.

Protocol (mentor-style rolling check):
  - train: 60 days
  - test:  next 26 days
  - step:  7 days (slide the whole block forward)
  - aggregate metrics across windows

Label leakage guard:
  train rows keep only dates where date + HORIZON <= train_end
  (label uses cases 7 days ahead).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "Weikun" / "supervised_horizon_outputs" / "supervised_horizon_1_next_day.csv.gz"
OUTPUT = HERE / "change_bin_7d_outputs" / "rolling_60_26_step7"
OUTPUT.mkdir(parents=True, exist_ok=True)

HORIZON = 7
BASE_MIN = 10
TRAIN_DAYS = 60
TEST_DAYS = 26
STEP_DAYS = 7

LABEL_ORDER = [
    "down_300p",
    "down_100p",
    "down_50p",
    "down_10p",
    "flat",
    "up_50p",
    "up_100p",
    "up_300p",
    "up_300p_plus",
]

FEATURE_COLUMNS = [
    "case_velocity",
    "case_acceleration",
    "case_jerk",
    "slope_3d",
    "slope_3d_lag1",
    "slope_3d_lag2",
    "avg_slope_10d",
    "population",
    "population_density_per_sq_km",
]


def assign_change_label(cases_today: float, cases_tplus7: float, base_min: int = BASE_MIN):
    if pd.isna(cases_today) or pd.isna(cases_tplus7):
        return np.nan
    if cases_today < base_min:
        return "flat"
    r = (cases_tplus7 - cases_today) / cases_today
    if r <= -3.0:
        return "down_300p"
    if r <= -1.0:
        return "down_100p"
    if r <= -0.5:
        return "down_50p"
    if r < -0.1:
        return "down_10p"
    if r <= 0.1:
        return "flat"
    if r <= 0.5:
        return "up_50p"
    if r <= 1.0:
        return "up_100p"
    if r <= 3.0:
        return "up_300p"
    return "up_300p_plus"


def build_model_frame(path: Path) -> pd.DataFrame:
    need = [
        "zip",
        "date",
        "cases_today",
        "case_velocity",
        "case_acceleration",
        "case_jerk",
        "population",
        "population_density_per_sq_km",
    ]
    panel = pd.read_csv(path, dtype={"zip": "string"}, parse_dates=["date"], usecols=need)
    panel = panel.sort_values(["zip", "date"]).reset_index(drop=True)

    g = panel.groupby("zip", sort=False)["cases_today"]
    panel["slope_3d"] = (g.shift(0) - g.shift(2)) / 2.0
    panel["slope_3d_lag1"] = panel.groupby("zip", sort=False)["slope_3d"].shift(1)
    panel["slope_3d_lag2"] = panel.groupby("zip", sort=False)["slope_3d"].shift(2)
    panel["avg_slope_10d"] = panel.groupby("zip", sort=False)["slope_3d"].transform(
        lambda s: s.rolling(8, min_periods=8).mean()
    )
    panel["cases_tplus7"] = g.shift(-HORIZON)
    panel["rel_change_7d"] = np.where(
        panel["cases_today"] > 0,
        (panel["cases_tplus7"] - panel["cases_today"]) / panel["cases_today"],
        np.nan,
    )
    panel["label"] = [
        assign_change_label(a, b) for a, b in zip(panel.cases_today, panel.cases_tplus7)
    ]
    panel["target_date"] = panel["date"] + pd.Timedelta(days=HORIZON)

    model_df = panel.dropna(subset=FEATURE_COLUMNS + ["label", "cases_tplus7", "target_date"]).copy()
    model_df["label"] = model_df["label"].astype(str)
    return model_df


def iter_windows(dates: pd.DatetimeIndex):
    n = len(dates)
    block = TRAIN_DAYS + TEST_DAYS
    window_id = 0
    start = 0
    while start + block <= n:
        train_dates = dates[start : start + TRAIN_DAYS]
        test_dates = dates[start + TRAIN_DAYS : start + block]
        yield {
            "window_id": window_id,
            "train_start": train_dates[0],
            "train_end": train_dates[-1],
            "test_start": test_dates[0],
            "test_end": test_dates[-1],
            "train_dates": train_dates,
            "test_dates": test_dates,
        }
        window_id += 1
        start += STEP_DAYS


def fit_score_window(model_df: pd.DataFrame, bounds: dict) -> dict | None:
    train_end = bounds["train_end"]
    train = model_df.loc[
        model_df["date"].isin(bounds["train_dates"]) & (model_df["target_date"] <= train_end)
    ].copy()
    test = model_df.loc[model_df["date"].isin(bounds["test_dates"])].copy()

    if train.empty or test.empty:
        return None

    y_train = train["label"].astype(str)
    train_classes = [c for c in LABEL_ORDER if c in set(y_train.unique())]
    if len(train_classes) < 2:
        return {
            "window_id": bounds["window_id"],
            "status": "skipped_lt2_classes",
            "train_rows": len(train),
            "test_rows": len(test),
            "n_train_classes": len(train_classes),
            "test_flat_share": float((test["label"] == "flat").mean()),
        }

    pipe = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=2000,
                    solver="lbfgs",
                ),
            ),
        ]
    )
    try:
        pipe.fit(train[FEATURE_COLUMNS], y_train)
    except Exception as exc:  # noqa: BLE001 - keep rolling loop alive
        return {
            "window_id": bounds["window_id"],
            "status": f"fit_failed:{type(exc).__name__}",
            "train_rows": len(train),
            "test_rows": len(test),
            "n_train_classes": len(train_classes),
            "test_flat_share": float((test["label"] == "flat").mean()),
        }

    y_test = test["label"].astype(str)
    pred = pipe.predict(test[FEATURE_COLUMNS])
    baseline = np.full(len(y_test), "flat")

    # Score against full label set so windows are comparable.
    model_acc = accuracy_score(y_test, pred)
    base_acc = accuracy_score(y_test, baseline)
    model_f1 = f1_score(y_test, pred, average="macro", labels=LABEL_ORDER, zero_division=0)
    base_f1 = f1_score(y_test, baseline, average="macro", labels=LABEL_ORDER, zero_division=0)

    return {
        "window_id": bounds["window_id"],
        "status": "ok",
        "train_start": bounds["train_start"],
        "train_end": bounds["train_end"],
        "test_start": bounds["test_start"],
        "test_end": bounds["test_end"],
        "train_rows": len(train),
        "test_rows": len(test),
        "n_train_classes": len(train_classes),
        "test_flat_share": float((y_test == "flat").mean()),
        "model_accuracy": float(model_acc),
        "baseline_accuracy": float(base_acc),
        "model_macro_f1": float(model_f1),
        "baseline_macro_f1": float(base_f1),
        "beat_baseline_acc": bool(model_acc > base_acc),
        "beat_baseline_f1": bool(model_f1 > base_f1),
    }


def main() -> None:
    print("Data:", DATA)
    print("Output:", OUTPUT)
    print(
        f"Protocol: train={TRAIN_DAYS}d, test={TEST_DAYS}d, step={STEP_DAYS}d, "
        f"horizon={HORIZON}d, leakage guard on train labels"
    )

    model_df = build_model_frame(DATA)
    dates = pd.DatetimeIndex(sorted(model_df["date"].unique()))
    print(f"Modeling rows: {len(model_df):,} | unique dates: {len(dates)}")

    rows = []
    for bounds in iter_windows(dates):
        result = fit_score_window(model_df, bounds)
        if result is None:
            continue
        rows.append(result)
        if result["window_id"] % 20 == 0 or result.get("status") != "ok":
            print(
                f"window {result['window_id']:3d} | {result.get('status')} | "
                f"flat={result.get('test_flat_share', float('nan')):.3f} | "
                f"acc={result.get('model_accuracy', float('nan')):.3f}/"
                f"{result.get('baseline_accuracy', float('nan')):.3f} | "
                f"f1={result.get('model_macro_f1', float('nan')):.3f}/"
                f"{result.get('baseline_macro_f1', float('nan')):.3f}"
            )

    per_window = pd.DataFrame(rows)
    per_window.to_csv(OUTPUT / "per_window_metrics.csv", index=False)

    ok = per_window.loc[per_window["status"] == "ok"].copy()
    summary = {
        "protocol": {
            "train_days": TRAIN_DAYS,
            "test_days": TEST_DAYS,
            "step_days": STEP_DAYS,
            "horizon_days": HORIZON,
            "base_min_for_nonflat": BASE_MIN,
            "leakage_guard": "train keeps only rows with target_date <= train_end",
        },
        "n_windows_total": int(len(per_window)),
        "n_windows_ok": int(len(ok)),
        "n_windows_skipped": int((per_window["status"] != "ok").sum()),
        "mean_test_flat_share": float(ok["test_flat_share"].mean()) if len(ok) else None,
        "median_test_flat_share": float(ok["test_flat_share"].median()) if len(ok) else None,
        "mean_model_accuracy": float(ok["model_accuracy"].mean()) if len(ok) else None,
        "mean_baseline_accuracy": float(ok["baseline_accuracy"].mean()) if len(ok) else None,
        "mean_model_macro_f1": float(ok["model_macro_f1"].mean()) if len(ok) else None,
        "mean_baseline_macro_f1": float(ok["baseline_macro_f1"].mean()) if len(ok) else None,
        "median_model_macro_f1": float(ok["model_macro_f1"].median()) if len(ok) else None,
        "median_baseline_macro_f1": float(ok["baseline_macro_f1"].median()) if len(ok) else None,
        "share_windows_beat_baseline_acc": float(ok["beat_baseline_acc"].mean()) if len(ok) else None,
        "share_windows_beat_baseline_f1": float(ok["beat_baseline_f1"].mean()) if len(ok) else None,
    }

    with open(OUTPUT / "aggregate_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    # Also a flat CSV for slides / excel
    pd.DataFrame(
        [
            {"metric": "n_windows_ok", "value": summary["n_windows_ok"]},
            {"metric": "mean_test_flat_share", "value": summary["mean_test_flat_share"]},
            {"metric": "mean_model_accuracy", "value": summary["mean_model_accuracy"]},
            {"metric": "mean_baseline_accuracy", "value": summary["mean_baseline_accuracy"]},
            {"metric": "mean_model_macro_f1", "value": summary["mean_model_macro_f1"]},
            {"metric": "mean_baseline_macro_f1", "value": summary["mean_baseline_macro_f1"]},
            {
                "metric": "share_windows_beat_baseline_acc",
                "value": summary["share_windows_beat_baseline_acc"],
            },
            {
                "metric": "share_windows_beat_baseline_f1",
                "value": summary["share_windows_beat_baseline_f1"],
            },
        ]
    ).to_csv(OUTPUT / "aggregate_summary.csv", index=False)

    print("\n=== Aggregate (OK windows only) ===")
    for k, v in summary.items():
        if k == "protocol":
            continue
        print(f"{k}: {v}")
    print("\nSaved:")
    for p in sorted(OUTPUT.iterdir()):
        print(" -", p.name)


if __name__ == "__main__":
    main()
