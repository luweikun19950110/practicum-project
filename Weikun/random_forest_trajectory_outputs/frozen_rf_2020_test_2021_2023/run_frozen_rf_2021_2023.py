"""Evaluate the frozen December 2020 Random Forest from 2021 through 2023."""
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
from warning_2021_analysis import event_labels, warning_events

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
dates = pd.date_range("2020-10-25", "2023-12-31")
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
test_dates = pd.date_range("2021-01-01", "2023-12-28")
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
assert np.isfinite(pred).all() and pred.shape == (585, 1092, 3)
prior = dev.parent / "frozen_rf_2020_test_2021"
with np.load(prior / "predictions.npz", allow_pickle=False) as previous:
    np.testing.assert_array_equal(ids, previous["zip"])
    np.testing.assert_array_equal(test_dates[:362].to_numpy(), previous["forecast_origins"])
    np.testing.assert_array_equal(actual[:, :362], previous["actual_cases"])
    np.testing.assert_allclose(pred[:, :362], previous["raw_predictions"], rtol=0, atol=1e-10)
previous_protocol = json.loads((prior / "protocol.json").read_text(encoding="utf-8"))
assert checkpoint_hashes == previous_protocol["checkpoint_sha256"]
print("Frozen checkpoints and historical predictions verified.", flush=True)
np.savez_compressed(out / "predictions.npz", raw_predictions=pred, actual_cases=actual,
                    zip=ids, forecast_origins=test_dates.to_numpy(), horizons=horizons)

truth_dates = pd.date_range("2020-01-01", "2023-12-31")
history = pd.read_csv(source, usecols=["zip", "date", "cases_today"],
                      dtype={"zip": str}, parse_dates=["date"])
history = history.pivot(index="zip", columns="date", values="cases_today").reindex(index=ids, columns=truth_dates).to_numpy(float)
assert np.isfinite(history).all()
origin_days = test_dates.to_numpy(dtype="datetime64[D]")
all_days = truth_dates.to_numpy(dtype="datetime64[D]")
test_pos = truth_dates.get_indexer(test_dates)
labels = [event_labels(row) for row in history]
onset = np.stack([row["onset"] for row in labels])
active = np.stack([row["active"] for row in labels])
valid = np.stack([row["valid"] for row in labels])
old_labels = pd.read_csv(root / "outbreak_task_outputs/case_surge_v1_20261101/daily_event_labels_2020.csv.gz",
                         dtype={"zip": str}, parse_dates=["date"])
for key, values in [("onset", onset), ("active", active)]:
    old = old_labels.pivot(index="zip", columns="date", values=key).reindex(index=ids, columns=truth_dates[:366])
    assert not old.isna().any().any()
    np.testing.assert_array_equal(old.to_numpy(bool), values[:, :366])
eligible = ~active[:, test_pos] & valid[:, test_pos]
future = np.stack([onset[:, test_pos + h] for h in horizons], axis=-1).any(axis=-1)
risk = np.empty(eligible.shape)
clipped = np.maximum(pred, 0)
for j, k in enumerate(test_pos):
    seq = np.concatenate([history[:, k-32:k+1], clipped[:, j]], axis=1)
    means = np.full_like(seq, np.nan)
    means[:, 2:] = (seq[:, 2:] + seq[:, 1:-1] + seq[:, :-2]) / 3
    margins = []
    for d in range(seq.shape[1]-4, seq.shape[1]):
        baseline = means[:, d-30:d-2]
        assert baseline.shape[1] == 28
        sd = baseline.std(axis=1, ddof=1)
        scale = np.maximum(sd, 1)
        margins.append(np.minimum((means[:, d] - baseline.mean(axis=1) - 2*sd) / scale,
                                  (seq[:, d-2:d+1].sum(axis=1)-5+1e-9) / (3*scale)))
    margins = np.stack(margins, axis=1)
    risk[:, j] = np.maximum.reduce([np.minimum(margins[:, h-1], margins[:, h]) for h in horizons])
assert np.isfinite(risk).all()
with np.load(prior / "warning_evaluation/random_forest_risk_scores.npz", allow_pickle=False) as old_risk:
    np.testing.assert_array_equal(eligible[:, :362], old_risk["eligible"])
    np.testing.assert_array_equal(future[:, :362], old_risk["truth"])
    np.testing.assert_allclose(risk[:, :362], old_risk["risk_score"], rtol=0, atol=1e-10)
threshold = previous_protocol["warning_threshold"]
assert threshold == 0
overall, alarms, events = warning_events(risk, eligible, onset, origin_days, all_days, threshold)
for table in (alarms, events):
    table["zip"] = ids[table.pop("region_index").to_numpy(int)]
event_leads = alarms.loc[alarms.true_warning].set_index(["zip", "matched_event_date"]).lead_days
events["lead_days"] = pd.MultiIndex.from_frame(events[["zip", "event_date"]]).map(event_leads)
assert events.lead_days.notna().equals(events.detected)
alarms.to_csv(out / "warnings.csv", index=False)
events.to_csv(out / "event_detection.csv", index=False)
np.savez_compressed(out / "risk_scores.npz", zip=ids, forecast_origins=origin_days,
                    risk_score=risk, eligible=eligible, truth=future)

residual = clipped - actual
weights_file = dev / "residual_moran/spatial_weights_knn8.csv"
weights = pd.read_csv(weights_file, dtype={"origin_zip": str, "neighbor_zip": str})
zip_index = pd.Index(ids)
i = zip_index.get_indexer(weights.origin_zip)
j = zip_index.get_indexer(weights.neighbor_zip)
assert (i >= 0).all() and (j >= 0).all() and (i != j).all()
w = sparse.csr_matrix((weights.weight, (i, j)), shape=(len(ids), len(ids)))
np.testing.assert_allclose(np.asarray(w.sum(axis=1)), 1)
centered = (residual - residual.mean(axis=0)).reshape(len(ids), -1)
den = np.square(centered).sum(axis=0)
num = (centered * (w @ centered)).sum(axis=0)
moran = (len(ids) / w.sum() * np.divide(num, den, out=np.full_like(den, np.nan), where=den > 1e-20)).reshape(-1, 3)
vec = centered[:, 0]
np.testing.assert_allclose(moran[0, 0], (len(ids) / w.sum()) * (vec @ w.toarray() @ vec) / (vec @ vec))
pd.DataFrame(moran, index=test_dates, columns=["day_1", "day_2", "day_3"]).to_csv(out / "residual_moran_by_origin.csv", index_label="forecast_origin")
periods = {
    "2021–2023 overall": ("2021-01-01", "2023-12-31"),
    **{str(year): (f"{year}-01-01", f"{year}-12-31") for year in (2021, 2022, 2023)},
    "Delta": ("2021-07-01", "2021-09-27"),
    "Early Omicron (emergence through BA.1)": ("2021-12-01", "2022-03-19"),
    "Omicron BA.1 predominance (sensitivity)": ("2021-12-19", "2022-03-19"),
}
rows = []
for period, (start, end) in periods.items():
    mask = (test_dates >= start) & (test_dates <= end)
    y = future[:, mask][eligible[:, mask]]
    scores = risk[:, mask][eligible[:, mask]]
    a = alarms.loc[alarms.forecast_origin.between(start, end)]
    e = events.loc[events.event_date.between(start, end)]
    rows.append(dict(period=period, start=start, end=end, origins=int(mask.sum()),
                     events=len(e), detected=int(e.detected.sum()), event_recall=e.detected.mean(),
                     warnings=len(a), correct_warnings=int(a.true_warning.sum()), warning_precision=a.true_warning.mean(),
                     average_precision=average_precision_score(y, scores), positive_origin_share=y.mean(),
                     mean_lead_days=e.lead_days.mean(), median_lead_days=e.lead_days.median(),
                     trajectory_mae=np.abs(residual[:, mask]).mean(), trajectory_rmse=np.sqrt(np.square(residual[:, mask]).mean()),
                     **{f"moran_day_{h}": np.nanmean(moran[mask, h-1]) for h in horizons},
                     **{f"moran_valid_day_{h}": int(np.isfinite(moran[mask, h-1]).sum()) for h in horizons}))
summary = pd.DataFrame(rows)
assert summary.iloc[0].detected == summary.iloc[0].correct_warnings == overall["detected_events"]
for metric in ["events", "detected", "warnings", "correct_warnings", "origins"]:
    assert summary.iloc[0][metric] == summary.iloc[1:4][metric].sum()
summary.to_csv(out / "metrics.csv", index=False)
protocol = dict(previous_protocol, test_origins=["2021-01-01", "2023-12-28"], test_targets_end="2023-12-31",
                saved_prediction_max_abs_difference=max_error, periods=periods,
                year_boundary="Continuous forecasts and 7-day warning cooldown across internal year ends. Group recall/lead by confirmation date and precision/AP by origin.",
                pooled_AP="Computed from all eligible ZIP-origin scores, not an average of yearly AP.",
                moran="Mean daily global I by horizon on clipped prediction minus actual. Original symmetric-union row-standardized geographic KNN8 weights. Descriptive, no significance claims.",
                omicron_source="https://www.cdc.gov/mmwr/volumes/71/wr/mm7134a3.htm",
                limitations="Retrospective onset data availability assumption. Variant windows are calendar context; no ZIP-level lineage labels.")
(out / "protocol.json").write_text(json.dumps(protocol, indent=2), encoding="utf-8")
print(summary.to_string(index=False), flush=True)
