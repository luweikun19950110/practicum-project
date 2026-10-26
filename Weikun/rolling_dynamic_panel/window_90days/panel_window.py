"""Rolling-window dynamic panel helpers (FE OLS)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

TRAIN_DAYS = 90
TEST_DAYS = round(TRAIN_DAYS * 0.3 / 0.7)  # 39
STEP_DAYS = TRAIN_DAYS
BLOCK_DAYS = TRAIN_DAYS + TEST_DAYS

HORIZON_FILES = {
    1: "supervised_horizon_1_next_day.csv.gz",
    2: "supervised_horizon_2.csv.gz",
    3: "supervised_horizon_3.csv.gz",
}

# Time-varying predictors. Static size/job levels are omitted; ZIP FE absorbs them.
NUMERIC_FEATURES = [
    "cases_today",
    "cases_lag_1",
    "cases_lag_7",
    "cases_lag_14",
    "cases_sum_7d",
    "cases_mean_7d",
    "case_std_7d",
    "cases_sum_14d",
    "cases_mean_14d",
    "case_std_14d",
    "week_over_week_change",
    "case_velocity",
    "case_acceleration",
    "case_jerk",
    "days_since_last_observed_case",
    "case_rate_today_per_100k",
    "case_rate_7d_per_100k",
    "case_rate_14d_per_100k",
    "nj_covid_pressure_7d",
    "nj_covid_pressure_14d",
]

CATEGORY_FEATURES = ["day_of_week", "month"]


def resolve_supervised_dir(start: Path | None = None) -> Path:
    start = Path.cwd() if start is None else Path(start)
    candidates = [
        start / "supervised_horizon_outputs",
        start / "Weikun" / "supervised_horizon_outputs",
        start.parent / "supervised_horizon_outputs",
        start.parent.parent / "supervised_horizon_outputs",
    ]
    for path in candidates:
        if (path / HORIZON_FILES[1]).is_file():
            return path.resolve()
    raise FileNotFoundError("Could not find supervised_horizon_outputs.")


def load_horizon(supervised_dir: Path, horizon: int) -> pd.DataFrame:
    path = supervised_dir / HORIZON_FILES[horizon]
    frame = pd.read_csv(path, dtype={"zip": "string"}, parse_dates=["date"])
    needed = ["zip", "date", "target_cases"] + NUMERIC_FEATURES + CATEGORY_FEATURES
    missing = [c for c in needed if c not in frame.columns]
    if missing:
        raise KeyError(f"Horizon {horizon} missing columns: {missing}")
    frame = frame.loc[:, needed].sort_values(["date", "zip"]).reset_index(drop=True)
    frame["target_date"] = frame["date"] + pd.Timedelta(days=horizon)
    return frame


def ordered_dates(panel: pd.DataFrame) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(sorted(panel["date"].unique()))


def window_bounds(dates: pd.DatetimeIndex, window_id: int) -> dict:
    start = window_id * STEP_DAYS
    train_end = start + TRAIN_DAYS
    test_end = train_end + TEST_DAYS
    if test_end > len(dates):
        raise ValueError(f"Window {window_id} does not fit in the calendar.")
    train_dates = dates[start:train_end]
    test_dates = dates[train_end:test_end]
    return {
        "window_id": window_id,
        "train_start": train_dates[0],
        "train_end": train_dates[-1],
        "test_start": test_dates[0],
        "test_end": test_dates[-1],
        "train_dates": train_dates,
        "test_dates": test_dates,
    }


def split_window(panel: pd.DataFrame, bounds: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_end = bounds["train_end"]
    train = panel.loc[
        panel["date"].isin(bounds["train_dates"]) & (panel["target_date"] <= train_end)
    ].copy()
    test = panel.loc[panel["date"].isin(bounds["test_dates"])].copy()
    if train.empty or test.empty:
        raise ValueError("Train or test split is empty for this window.")
    if train["target_date"].max() > train_end:
        raise AssertionError("Train labels leaked past the train end.")
    if test["date"].min() < bounds["test_start"]:
        raise AssertionError("Test dates start too early.")
    return train, test


def make_design(frame: pd.DataFrame, columns: pd.Index | None = None) -> pd.DataFrame:
    cats = frame.loc[:, ["zip"] + CATEGORY_FEATURES].astype(str)
    dummies = pd.get_dummies(cats, drop_first=True, dtype=float)
    x = pd.concat([frame.loc[:, NUMERIC_FEATURES].astype(float), dummies], axis=1)
    x.insert(0, "intercept", 1.0)
    if columns is not None:
        x = x.reindex(columns=columns, fill_value=0.0)
    return x


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, horizon: int, window_id: int) -> dict:
    x_train = make_design(train)
    y_train = train["target_cases"].to_numpy(dtype=float)
    beta, _, rank, _ = np.linalg.lstsq(x_train.to_numpy(dtype=float), y_train, rcond=None)
    if rank < x_train.shape[1]:
        # Collinearity can appear in short windows; keep the fit but flag it.
        rank_deficient = True
    else:
        rank_deficient = False

    x_test = make_design(test, columns=x_train.columns)
    pred_raw = x_test.to_numpy(dtype=float) @ beta
    pred = np.clip(pred_raw, a_min=0.0, a_max=None)

    predictions = test.loc[:, ["zip", "date", "target_date", "cases_today", "target_cases"]].copy()
    predictions = predictions.rename(columns={"target_cases": "actual_cases", "cases_today": "persistence_prediction"})
    predictions["panel_prediction_raw"] = pred_raw
    predictions["panel_prediction"] = pred
    predictions["horizon_days"] = horizon
    predictions["window_id"] = window_id

    coefficients = pd.DataFrame({"term": x_train.columns, "coefficient": beta})
    coefficients["horizon_days"] = horizon
    coefficients["window_id"] = window_id
    coefficients["is_fixed_effect"] = coefficients["term"].str.startswith("zip_")

    return {
        "predictions": predictions,
        "coefficients": coefficients,
        "rank_deficient": rank_deficient,
        "n_features": int(x_train.shape[1]),
    }


def score_predictions(predictions: pd.DataFrame) -> dict:
    actual = predictions["actual_cases"].to_numpy(dtype=float)
    panel = predictions["panel_prediction"].to_numpy(dtype=float)
    persistence = predictions["persistence_prediction"].to_numpy(dtype=float)

    def pack(name: str, pred: np.ndarray) -> dict:
        err = pred - actual
        mae = float(np.mean(np.abs(err)))
        rmse = float(np.sqrt(np.mean(err**2)))
        mean_error = float(np.mean(err))
        return {
            "model": name,
            "MAE": mae,
            "RMSE": rmse,
            "mean_error": mean_error,
        }

    panel_scores = pack("Dynamic panel FE OLS", panel)
    base_scores = pack("Persistence: future = cases_today", persistence)
    skill = (
        np.nan
        if base_scores["MAE"] == 0
        else 1.0 - panel_scores["MAE"] / base_scores["MAE"]
    )
    return {
        "panel": panel_scores,
        "persistence": base_scores,
        "skill_vs_persistence": float(skill),
    }


def run_window(
    horizons: dict[int, pd.DataFrame],
    dates: pd.DatetimeIndex,
    window_id: int,
) -> dict:
    bounds = window_bounds(dates, window_id)
    metric_rows = []
    coef_parts = []
    pred_parts = []
    identity = {
        "window_id": window_id,
        "train_start": bounds["train_start"].date().isoformat(),
        "train_end": bounds["train_end"].date().isoformat(),
        "test_start": bounds["test_start"].date().isoformat(),
        "test_end": bounds["test_end"].date().isoformat(),
    }

    for horizon, panel in horizons.items():
        train, test = split_window(panel, bounds)
        fit = fit_predict(train, test, horizon=horizon, window_id=window_id)
        scores = score_predictions(fit["predictions"])
        metric_rows.append(
            {
                **identity,
                "horizon_days": horizon,
                "train_rows": len(train),
                "test_rows": len(test),
                "n_zips_train": int(train["zip"].nunique()),
                "n_zips_test": int(test["zip"].nunique()),
                "n_design_columns": fit["n_features"],
                "rank_deficient": fit["rank_deficient"],
                "model_MAE": scores["panel"]["MAE"],
                "model_RMSE": scores["panel"]["RMSE"],
                "model_mean_error": scores["panel"]["mean_error"],
                "persistence_MAE": scores["persistence"]["MAE"],
                "persistence_RMSE": scores["persistence"]["RMSE"],
                "skill_vs_persistence": scores["skill_vs_persistence"],
            }
        )
        coef_parts.append(fit["coefficients"])
        pred_parts.append(fit["predictions"])

    return {
        "identity": identity,
        "metrics": pd.DataFrame(metric_rows),
        "coefficients": pd.concat(coef_parts, ignore_index=True),
        "predictions": pd.concat(pred_parts, ignore_index=True),
    }


def top_non_fe_coefficients(coefficients: pd.DataFrame, horizon: int, n: int = 10) -> pd.DataFrame:
    part = coefficients.loc[
        coefficients["horizon_days"].eq(horizon) & ~coefficients["is_fixed_effect"]
    ].copy()
    part["abs_coefficient"] = part["coefficient"].abs()
    return part.sort_values("abs_coefficient", ascending=False).head(n).reset_index(drop=True)
