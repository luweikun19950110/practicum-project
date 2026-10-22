"""Direct 7-day forecast of daily_cases with one LightGBM model per horizon.

The row date is the day you are standing on. Features are that day's weekday,
the last 7 days of cases and pressure (including today), the last 6 velocities,
the last 5 accelerations, and the last 4 jerks. Each model predicts one future
day: target_day_1 is tomorrow, target_day_7 is a week ahead.

Change DATA_PATH and TEST_START when the file or the holdout month changes.
Run from the project root:

  python Dhruvesh/training/forecast_7day.py
"""

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "training" / "training_panel_2021.csv"
OUTPUT_DIR = ROOT / "training" / "forecast_outputs"

# Last month of this file. Rows on or after this date are the test set.
TEST_START = "2021-12-01"
HORIZONS = range(1, 8)
# Lag 0 is today. Shorter windows are the derivatives you can form from 7 case days.
# Feature name -> panel column. "cases" is stored as daily_cases.
LAG_WINDOWS = {
    "cases": ("daily_cases", range(0, 7)),
    "velocity": ("velocity", range(0, 6)),
    "acceleration": ("acceleration", range(0, 5)),
    "jerk": ("jerk", range(0, 4)),
    "pressure": ("pressure", range(0, 7)),
}
SEED = 42


def load_panel(path: Path = DATA_PATH) -> pd.DataFrame:
    panel = pd.read_csv(path, dtype={"zipcode": str}, parse_dates=["date"])
    panel["zipcode"] = panel["zipcode"].str.zfill(5)
    return panel.sort_values(["zipcode", "date"]).reset_index(drop=True)


def build_supervised(panel: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Lag features and the seven forward targets, one row per workplace-day."""
    frame = panel.copy()
    feature_columns = ["day_of_week"]
    for feature_name, (column, lags) in LAG_WINDOWS.items():
        grouped = frame.groupby("zipcode", sort=False)[column]
        for lag in lags:
            name = f"{feature_name}_lag_{lag}"
            frame[name] = frame[column] if lag == 0 else grouped.shift(lag)
            feature_columns.append(name)
    grouped_cases = frame.groupby("zipcode", sort=False)["daily_cases"]
    target_columns = []
    for horizon in HORIZONS:
        name = f"target_day_{horizon}"
        frame[name] = grouped_cases.shift(-horizon)
        target_columns.append(name)

    model_frame = frame.dropna(subset=feature_columns + target_columns).reset_index(drop=True)
    return model_frame, feature_columns, target_columns


def split_by_date(frame: pd.DataFrame, test_start: str = TEST_START) -> tuple[pd.DataFrame, pd.DataFrame]:
    cutoff = pd.Timestamp(test_start)
    train = frame.loc[frame["date"] < cutoff].copy()
    test = frame.loc[frame["date"] >= cutoff].copy()
    if train.empty or test.empty:
        raise ValueError(f"Empty train or test split at {test_start}.")
    return train, test


def fit_models(train: pd.DataFrame, feature_columns: list[str], target_columns: list[str]) -> dict[str, lgb.LGBMRegressor]:
    models = {}
    features = train[feature_columns]
    for target in target_columns:
        model = lgb.LGBMRegressor(
            n_estimators=300,
            learning_rate=0.05,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=SEED,
            verbose=-1,
        )
        model.fit(features, train[target])
        models[target] = model
    return models


def predict_all(models: dict[str, lgb.LGBMRegressor], test: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    """One row per workplace and forecast date, with actual and predicted cases."""
    predictions = test[["zipcode", "date", "daily_cases"]].copy()
    predictions = predictions.rename(columns={"date": "forecast_date", "daily_cases": "cases_today"})
    features = test[feature_columns]
    for horizon in HORIZONS:
        target = f"target_day_{horizon}"
        predictions[f"actual_day_{horizon}"] = test[target].to_numpy()
        raw = models[target].predict(features)
        predictions[f"pred_day_{horizon}"] = np.clip(raw, 0, None)
        # Baseline: every future day equals today's cases.
        predictions[f"persistence_day_{horizon}"] = test["daily_cases"].to_numpy()
    return predictions


def score(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for horizon in HORIZONS:
        actual = predictions[f"actual_day_{horizon}"].to_numpy()
        for name, column in (
            ("LightGBM", f"pred_day_{horizon}"),
            ("Persistence: future day = today", f"persistence_day_{horizon}"),
        ):
            error = predictions[column].to_numpy() - actual
            rows.append(
                {
                    "horizon_days": horizon,
                    "model": name,
                    "MAE": float(np.abs(error).mean()),
                    "RMSE": float(np.sqrt((error ** 2).mean())),
                    "mean_error": float(error.mean()),
                }
            )
    return pd.DataFrame(rows)


def feature_importance(models: dict[str, lgb.LGBMRegressor], feature_columns: list[str]) -> pd.DataFrame:
    """Gain importance from each horizon model. Larger gain means the split reduced more error."""
    rows = []
    for target, model in models.items():
        horizon = int(target.rsplit("_", 1)[-1])
        gain = model.booster_.feature_importance(importance_type="gain")
        for feature, value in zip(feature_columns, gain):
            rows.append({"horizon_days": horizon, "feature": feature, "gain": float(value)})
    return pd.DataFrame(rows)


def main() -> None:
    panel = load_panel()
    frame, feature_columns, target_columns = build_supervised(panel)
    train, test = split_by_date(frame)
    models = fit_models(train, feature_columns, target_columns)
    predictions = predict_all(models, test, feature_columns)
    metrics = score(predictions)

    OUTPUT_DIR.mkdir(exist_ok=True)
    importance = feature_importance(models, feature_columns)
    predictions.to_csv(OUTPUT_DIR / "predictions_test.csv", index=False)
    metrics.to_csv(OUTPUT_DIR / "metrics_test.csv", index=False)
    importance.to_csv(OUTPUT_DIR / "feature_importance.csv", index=False)
    print(f"Features: {len(feature_columns)}")
    print(f"Train rows {len(train):,}   {train.date.min().date()} to {train.date.max().date()}")
    print(f"Test rows  {len(test):,}   {test.date.min().date()} to {test.date.max().date()}")
    print(metrics.round(3).to_string(index=False))
    print("Saved", OUTPUT_DIR)


if __name__ == "__main__":
    main()
