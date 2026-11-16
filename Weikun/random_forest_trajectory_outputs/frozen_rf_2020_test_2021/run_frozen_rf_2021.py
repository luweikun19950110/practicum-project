"""Replay the saved December 2020 Random Forest estimators on 2021."""
import hashlib
import json
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics import average_precision_score

out = Path(__file__).resolve().parent
root = out.parents[1]
dev = out.parent / "rf60_weekly_development_20261027"
historical = root / "later_time_evaluation_outputs/evaluation_2021_20261101"
sys.dont_write_bytecode = True
sys.path.insert(0, str(historical / "support"))
from random_forest_evaluation import GROUPS
from warning_2021_analysis import analyze_warnings

fit_date = "2020-12-23"
with np.load(dev / "predictions.npz", allow_pickle=False) as archive:
    ids = archive["zip"]
    ref_dates = pd.DatetimeIndex(archive["forecast_origins"])
    validation = ref_dates >= fit_date
    ref = archive["raw_predictions"][:, validation]
    validation_dates = ref_dates[validation]
features = sum(GROUPS.values(), [])
candidate_order = pd.read_csv(dev / "candidate_features.csv")["feature"].tolist()
assert features == candidate_order
numeric = sum([cols for group, cols in GROUPS.items()
               if group not in ("month", "weekday", "sparse_history")], [])
source = root / "rolling_trajectory_outputs/inputs/nj_daily_features.csv.gz"
source_hash = hashlib.file_digest(source.open("rb"), "sha256").hexdigest()
assert source_hash == "d18a70fe1b1efa550c0bc3e28edeca576f432996dfc85d67106c70069f79a9e4"
frame = pd.read_csv(source, usecols=["zip", "date"] + numeric,
                    dtype={"zip": str}, parse_dates=["date"])
dates = pd.date_range("2020-10-25", "2021-12-31")
frame = frame.loc[frame.zip.isin(ids) & frame.date.isin(dates)]
arrays = {col: frame.pivot(index="zip", columns="date", values=col)
          .reindex(index=ids, columns=dates).to_numpy(float) for col in numeric}
counts = arrays["cases_today"]
assert np.isfinite(counts).all()
gap = np.empty_like(counts)
never = np.empty_like(counts)
last = np.full(len(ids), -1)
# Preserve the December fit window's reset and update the state through each origin.
for t in range(len(dates)):
    last = np.where(counts[:, t] > 0, t, last)
    gap[:, t] = np.where(last >= 0, t - last, t + 1)
    never[:, t] = last < 0
arrays["days_since_last_observed_case_censored"] = gap
arrays["no_previous_observed_case"] = never
test_dates = pd.date_range("2021-01-01", "2021-12-28")
origins = validation_dates.append(test_dates)
pos = dates.get_indexer(origins)
horizons = [1, 2, 3]
pred = np.empty((len(ids), len(origins), len(horizons)))
rows = len(ids) * len(origins)
identity = sparse.csr_matrix(
    (np.ones(rows, np.float32), (np.arange(rows), np.repeat(np.arange(len(ids)), len(origins)))),
    shape=(rows, len(ids)),
)
checkpoint_hashes = {}
for i, horizon in enumerate(horizons):
    target = dates + pd.Timedelta(days=horizon)
    for month in range(2, 13):
        arrays[f"target_month_{month}"] = np.broadcast_to(target.month == month, counts.shape)
    for weekday in range(2, 8):
        arrays[f"target_weekday_{weekday}"] = np.broadcast_to(target.dayofweek == weekday - 1, counts.shape)
    x = np.stack([arrays[col][:, pos] for col in features], axis=-1)
    assert np.isfinite(x).all()
    design = sparse.hstack(
        [sparse.csr_matrix(x.reshape(rows, len(features)).astype(np.float32)), identity],
        format="csr",
    )
    checkpoint = dev / f"models/rf_{fit_date}_h{horizon}.joblib"
    with checkpoint.open("rb") as stream:
        checkpoint_hashes[checkpoint.name] = hashlib.file_digest(stream, "sha256").hexdigest()
    model = joblib.load(checkpoint)
    assert model.n_features_in_ == design.shape[1] == 619
    pred[:, :, i] = model.predict(design).reshape(len(ids), len(origins))
np.testing.assert_allclose(pred[:, :len(validation_dates)], ref, rtol=0, atol=1e-10)
max_error = float(np.max(np.abs(pred[:, :len(validation_dates)] - ref)))
n = len(validation_dates)
pred = pred[:, n:]
actual = np.stack([counts[:, pos[n:] + h] for h in horizons], axis=-1)
assert np.isfinite(pred).all() and pred.shape == (585, 362, 3)
np.savez_compressed(out / "predictions.npz", raw_predictions=pred, actual_cases=actual,
                    zip=ids, forecast_origins=test_dates.to_numpy(), horizons=horizons)
warning_out = out / "warning_evaluation"
metrics = analyze_warnings(root, {"Random Forest": out}, warning_out)
warnings = pd.read_csv(warning_out / "random_forest_warnings.csv", parse_dates=["forecast_origin"])
events = pd.read_csv(warning_out / "random_forest_event_detection.csv", parse_dates=["event_date"])
focus = json.loads((historical / "frozen_plan.json").read_text(encoding="utf-8"))["focus_windows"]
periods = {"2021": [str(test_dates[0].date()), "2021-12-31"], **focus}
err = np.maximum(pred, 0) - actual
summary = []
with np.load(warning_out / "random_forest_risk_scores.npz", allow_pickle=False) as risk:
    for period, (start, end) in periods.items():
        mask = (test_dates >= start) & (test_dates <= end)
        eligible = risk["eligible"][:, mask]
        truth = risk["truth"][:, mask][eligible]
        scores = risk["risk_score"][:, mask][eligible]
        w = warnings.loc[warnings.forecast_origin.between(start, end)]
        e = events.loc[events.event_date.between(start, end)]
        summary.append(dict(period=period, start=start, end=end, forecast_origins=int(mask.sum()),
                            event_count=len(e), detected_events=int(e.detected.sum()),
                            event_recall=e.detected.mean(), warning_count=len(w),
                            correct_warnings=int(w.true_warning.sum()),
                            warning_precision=w.true_warning.mean(),
                            average_precision=average_precision_score(truth, scores),
                            positive_origin_share=truth.mean(),
                            mean_lead_days=e.lead_days.mean(), median_lead_days=e.lead_days.median(),
                            trajectory_mae=np.abs(err[:, mask]).mean(),
                            trajectory_rmse=np.sqrt(np.square(err[:, mask]).mean())))
result = pd.DataFrame(summary)
overall = metrics.loc[metrics.scope.eq("overall")].iloc[0]
np.testing.assert_allclose(
    result.iloc[0][["event_recall", "warning_precision", "average_precision", "mean_lead_days"]].to_numpy(float),
    overall[["event_recall", "warning_precision", "AP", "mean_lead_days"]].to_numpy(float),
)
result.to_csv(out / "metrics.csv", index=False)
(out / "protocol.json").write_text(json.dumps(dict(
    fit_date=fit_date, fit_window=["2020-10-25", fit_date], checkpoint_sha256=checkpoint_hashes,
    source_sha256=source_hash, refitting=False, cutoff_for_training_targets=fit_date,
    validation_origins=[str(d.date()) for d in validation_dates],
    saved_prediction_max_abs_difference=max_error, test_origins=["2021-01-01", "2021-12-28"],
    test_targets_end="2021-12-31", warning_threshold=float(overall.threshold),
    feature_update="Observed data through each forecast origin; sparse-history state maintained from fit-window start",
    period_basis="Precision and AP by warning/forecast origin; recall and lead by event-confirmation date",
    limitations="Retrospective onset data availability; prior 2021 exploration; December window covers Omicron emergence",
), indent=2), encoding="utf-8")
print(result.to_string(index=False))
print("Checkpoint validation max abs difference:", max_error)
