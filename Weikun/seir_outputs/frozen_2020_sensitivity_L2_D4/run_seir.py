"""SEIR incidence benchmark with 2020-only fitting and causal state updates."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.optimize import minimize_scalar
from sklearn.metrics import average_precision_score

root = Path(__file__).resolve().parents[2]
out = root / "seir_outputs/frozen_2020_sensitivity_L2_D4"
out.mkdir(parents=True, exist_ok=True)
sys.dont_write_bytecode = True
sys.path.insert(0, str(root / "later_time_evaluation_outputs/evaluation_2021_20261101/support"))
from warning_2021_analysis import event_labels, warning_events

rf_run = root / "random_forest_trajectory_outputs/frozen_rf_2020_test_2021_2023"
dev = root / "random_forest_trajectory_outputs/rf60_weekly_development_20261027"
with np.load(rf_run / "predictions.npz", allow_pickle=False) as rf:
    ids = rf["zip"]
    test_dates = pd.DatetimeIndex(rf["forecast_origins"])
    actual = rf["actual_cases"]
horizons = [1, 2, 3]
source = root / "rolling_trajectory_outputs/inputs/nj_daily_features.csv.gz"
with source.open("rb") as stream:
    input_hash = hashlib.file_digest(stream, "sha256").hexdigest()
assert input_hash == "d18a70fe1b1efa550c0bc3e28edeca576f432996dfc85d67106c70069f79a9e4"
dates = pd.date_range("2020-01-01", "2023-12-31")
frame = pd.read_csv(source, usecols=["zip", "date", "cases_today", "population"],
                    dtype={"zip": str}, parse_dates=["date"])
frame = frame.loc[frame.zip.isin(ids)]
assert not frame.duplicated(["zip", "date"]).any()
counts = frame.pivot(index="zip", columns="date", values="cases_today").reindex(index=ids, columns=dates).to_numpy(float)
population = frame.groupby("zip").population.first().reindex(ids).to_numpy(float)
assert np.isfinite(counts).all() and np.isfinite(population).all() and (population > 0).all()

# Explicit baseline assumptions, fixed before fitting or viewing SEIR test scores.
sigma, gamma = 1/2, 1/4
def reconstruct(observed):
    """Causal incidence-informed state initialization, under unit ascertainment.

    E uses the trailing three-day observed onset mean divided by sigma.
    I and R use the last 60 days of observed inflows and exponential infectious survival.
    These are approximate surveillance states, not identified biological counts.
    """
    smoothed = pd.DataFrame(observed.T).rolling(3, min_periods=1).mean().to_numpy().T
    exposed = smoothed / sigma
    states = np.empty((*observed.shape, 4))
    for t in range(observed.shape[1]):
        lo = max(0, t-59)
        trailing = observed[:, lo:t+1]
        age = np.arange(trailing.shape[1]-1, -1, -1)
        infectious = trailing @ np.exp(-gamma * age)
        removed = trailing.sum(axis=1) - infectious
        susceptible = population - exposed[:, t] - infectious - removed
        if (susceptible < 0).any():
            raise ValueError("Rolling surveillance state exceeds population; revise observation model.")
        states[:, t] = np.column_stack([susceptible, exposed[:, t], infectious, removed])
    np.testing.assert_allclose(states.sum(axis=-1), np.broadcast_to(population[:, None], observed.shape), rtol=1e-12, atol=1e-7)
    return states

def advance(initial, beta, pop, sigma_value=sigma, gamma_value=gamma):
    """RK4 integration, four substeps per day; outputs integrated E-to-I incidence."""
    state = np.concatenate([initial.copy(), np.zeros((*initial.shape[:-1], 1))], axis=-1)
    def derivative(y):
        s, e, i, r, cumulative = np.moveaxis(y, -1, 0)
        infection = beta * s * i / pop
        onset = sigma_value * e
        removal = gamma_value * i
        return np.stack([-infection, infection-onset, onset-removal, removal, onset], axis=-1)
    forecasts = []
    for _ in range(3):
        previous = state[..., 4].copy()
        for _ in range(4):
            k1 = derivative(state)
            k2 = derivative(state + .125*k1)
            k3 = derivative(state + .125*k2)
            k4 = derivative(state + .25*k3)
            state += .25*(k1+2*k2+2*k3+k4)/6
        forecasts.append(state[..., 4] - previous)
    return np.stack(forecasts, axis=-1), state[..., :4]

states = reconstruct(counts)
# Prefix invariance catches accidental use of future observations in state updates.
cutoff = dates.get_loc("2020-12-23")
np.testing.assert_allclose(reconstruct(counts[:, :cutoff+1]), states[:, :cutoff+1], rtol=0, atol=0)
lo = dates.get_loc("2020-10-25")
train_pos = np.arange(lo+14, cutoff-3+1)
assert dates[train_pos[-1]+3] <= pd.Timestamp("2020-12-23")
targets = np.stack([counts[:, train_pos+h] for h in horizons], axis=-1)
betas = np.empty(len(ids))
fit_rows = []
for z, zipcode in enumerate(ids):
    initial = states[z, train_pos]
    def loss(beta):
        prediction, _ = advance(initial, beta, population[z])
        return float(np.square(np.log1p(prediction) - np.log1p(targets[z])).mean())
    if np.all(initial[:, 1:3] == 0):
        beta, success, status = 0., True, "no_exposed_or_infectious_state_in_training"
    else:
        fit = minimize_scalar(loss, bounds=(0, 2), method="bounded", options={"xatol":1e-7})
        candidates = [0., float(fit.x), 2.]
        beta = min(candidates, key=loss)
        success, status = bool(fit.success), "fitted"
    assert success
    betas[z] = beta
    fit_rows.append(dict(zip=zipcode, beta=beta, sigma=sigma, gamma=gamma,
                         objective=loss(beta), status=status, boundary=beta in (0., 2.),
                         latest_target="2020-12-23", training_origins=len(train_pos)))
    if (z+1) % 100 == 0:
        print("Fitted SEIR ZIPs:", z+1, flush=True)
pd.DataFrame(fit_rows).to_csv(out / "parameters_2020.csv", index=False)
np.savez_compressed(out / "frozen_parameters.npz", zip=ids, beta=betas, sigma=sigma, gamma=gamma)
# Numerical stability and mechanistic invariants for nonnegative state/finite incidence.
probe, final_state = advance(states[:, cutoff], betas, population)
assert (probe >= 0).all() and (final_state >= 0).all()
np.testing.assert_allclose(final_state.sum(axis=-1), population, rtol=1e-10)
origins = dates.get_indexer(test_dates)
pred, end_states = advance(states[:, origins], betas[:, None], population[:, None])
assert np.isfinite(pred).all() and (pred >= 0).all() and (end_states >= 0).all()
np.testing.assert_allclose(end_states.sum(axis=-1), np.broadcast_to(population[:, None], (len(ids), len(origins))), rtol=1e-10)
np.testing.assert_array_equal(actual, np.stack([counts[:, origins+h] for h in horizons], axis=-1))
np.savez_compressed(out / "predictions.npz", raw_predictions=pred, actual_cases=actual,
                    zip=ids, forecast_origins=test_dates.to_numpy(), horizons=horizons)
previous_protocol = dict(
    model="SEIR incidence benchmark with daily causal state reconstruction",
    fit_window=["2020-10-25", "2020-12-23"], training_warmup_days=14,
    training_origins=len(train_pos), beta_fit="Per ZIP bounded [0,2], pooled horizon 1/2/3 log1p MSE",
    sigma=sigma, gamma=gamma, latent_period_days=2, infectious_period_days=4,
    parameter_policy="Beta estimated using 2020 targets only. Sigma/gamma are illustrative fixed assumptions, not estimated disease durations. All parameters frozen across testing.",
    observation_model="Unit reporting assumption. Recorded symptom-onset counts approximate E-to-I incidence. I is a stock; forecasts integrate sigma*E per day.",
    state_update="Each origin reconstructs E from trailing 3-day onset mean/sigma; I and R from the last 60 days of inflows and exponential survival; earlier removals reset outside the local forecast. S=N-E-I-R. A deterministic surveillance approximation, not Bayesian filtering.",
    source_sha256=input_hash, warning_threshold=0.,
    limitations="No reporting-delay model, under-ascertainment estimation, vaccination, reinfection, migration, or spatial transmission. Conditional on exact ZIP/ZCTA population mapping. Previously inspected test outcomes mean exploratory retrospective comparison.",
)
print("Prediction archive complete.", flush=True)

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
                periods=periods,
                year_boundary="Continuous forecasts and 7-day warning cooldown across internal year ends. Group recall/lead by confirmation date and precision/AP by origin.",
                pooled_AP="Computed from all eligible ZIP-origin scores, not an average of yearly AP.",
                moran="Mean daily global I by horizon on clipped prediction minus actual. Original symmetric-union row-standardized geographic KNN8 weights. Descriptive, no significance claims.",
                omicron_source="https://www.cdc.gov/mmwr/volumes/71/wr/mm7134a3.htm",
                evaluation_note="Variant windows are calendar context; no ZIP-level lineage labels.")
(out / "protocol.json").write_text(json.dumps(protocol, indent=2), encoding="utf-8")
print(summary.to_string(index=False), flush=True)
