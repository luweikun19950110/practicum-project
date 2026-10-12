"""Rebuild Weikun's NJ+NY 2021 LODES commute tables from the raw Census files.

Inputs (downloaded into Data/LODES):
  nj/ny_od_main_JT00_2021.csv.gz  home and work in the same state
  nj/ny_od_aux_JT00_2021.csv.gz   home and work in different states
  nj/ny_xwalk.csv.gz              census block -> ZCTA

Outputs (njny_commute_outputs):
  flows, audit, unmapped rows, one-row-per-region features, inbound/outbound weights
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "Data" / "LODES"
OUTPUT = ROOT / "njny_commute_outputs"

STATE_NAMES = {"34": "NJ", "36": "NY"}
# (file state, file type, residence state FIPS, workplace state FIPS)
SPECS = [
    ("nj", "main", "34", "34"),
    ("ny", "main", "36", "36"),
    ("ny", "aux", "34", "36"),  # live NJ, work NY
    ("nj", "aux", "36", "34"),  # live NY, work NJ
]
KEYS = ["origin_state", "origin_zcta", "destination_state", "destination_zcta"]


def load_block_to_zcta() -> pd.Series:
    parts = []
    for state in ["nj", "ny"]:
        path = DATA / f"{state}_xwalk.csv.gz"
        table = pd.read_csv(path, usecols=["tabblk2020", "zcta"], dtype="string")
        parts.append(table)
    xwalk = pd.concat(parts, ignore_index=True)
    if xwalk["tabblk2020"].duplicated().any():
        raise ValueError("Duplicate block IDs in the crosswalk.")
    return xwalk.set_index("tabblk2020")["zcta"]


def valid_zcta(series: pd.Series) -> pd.Series:
    return series.str.fullmatch(r"[0-9]{5}").fillna(False) & ~series.isin(["00000", "99999"])


def build_flows(lookup: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    parts, audits, unmatched = [], [], []
    for file_state, file_type, home_state, work_state in SPECS:
        path = DATA / f"{file_state}_od_{file_type}_JT00_2021.csv.gz"
        raw_rows = selected_rows = raw_jobs = selected_jobs = 0
        candidate_rows = unmapped_jobs = unmapped_rows = 0
        for chunk in pd.read_csv(
            path,
            usecols=["h_geocode", "w_geocode", "S000"],
            dtype={"h_geocode": "string", "w_geocode": "string"},
            chunksize=250_000,
        ):
            raw_rows += len(chunk)
            raw_jobs += int(chunk["S000"].sum())
            keep = chunk["h_geocode"].str[:2].eq(home_state) & chunk["w_geocode"].str[:2].eq(work_state)
            if file_type == "main" and not keep.all():
                raise ValueError(f"Unexpected state in {path.name}")
            subset = chunk.loc[keep].copy()
            if subset.empty:
                continue
            candidate_rows += len(subset)
            subset["origin_state"] = STATE_NAMES[home_state]
            subset["destination_state"] = STATE_NAMES[work_state]
            subset["origin_zcta"] = subset["h_geocode"].map(lookup)
            subset["destination_zcta"] = subset["w_geocode"].map(lookup)
            mapped = valid_zcta(subset["origin_zcta"]) & valid_zcta(subset["destination_zcta"])
            if not mapped.all():
                rejected = subset.loc[~mapped].copy()
                rejected["source_file"] = path.name
                unmatched.append(rejected)
                unmapped_rows += len(rejected)
                unmapped_jobs += int(rejected["S000"].sum())
            subset = subset.loc[mapped]
            selected_rows += len(subset)
            selected_jobs += int(subset["S000"].sum())
            parts.append(subset.groupby(KEYS, as_index=False)["S000"].sum())
        audits.append(
            {
                "source_file": path.name,
                "direction": f"{STATE_NAMES[home_state]}->{STATE_NAMES[work_state]}",
                "raw_rows": raw_rows,
                "selected_rows": selected_rows,
                "excluded_other_state_rows": raw_rows - candidate_rows,
                "unmapped_zcta_rows": unmapped_rows,
                "unmapped_zcta_jobs": unmapped_jobs,
                "raw_jobs": raw_jobs,
                "selected_jobs": selected_jobs,
            }
        )
        print(f"Finished {path.name}: selected {selected_rows:,} rows, {selected_jobs:,} jobs")

    flows = (
        pd.concat(parts, ignore_index=True)
        .groupby(KEYS, as_index=False)["S000"]
        .sum()
        .rename(columns={"S000": "commute_jobs"})
    )
    flows["year"] = 2021
    flows["job_type"] = "JT00"
    audit = pd.DataFrame(audits)
    if int(flows["commute_jobs"].sum()) != int(audit["selected_jobs"].sum()):
        raise ValueError("Job totals do not match the audit.")
    unmatched_df = pd.concat(unmatched, ignore_index=True) if unmatched else pd.DataFrame()
    return flows, audit, unmatched_df


def totals(table: pd.DataFrame, columns: list[str], name: str) -> pd.Series:
    result = table.groupby(columns)["commute_jobs"].sum().rename(name)
    result.index.names = ["state", "zcta"]
    return result


def build_features(flows: pd.DataFrame) -> pd.DataFrame:
    home = ["origin_state", "origin_zcta"]
    work = ["destination_state", "destination_zcta"]
    same = flows["origin_state"].eq(flows["destination_state"]) & flows["origin_zcta"].eq(flows["destination_zcta"])
    cross = flows["origin_state"].ne(flows["destination_state"])
    metrics = [
        totals(flows, home, "resident_jobs_total"),
        totals(flows, work, "workplace_jobs_total"),
        totals(flows.loc[~same], work, "inbound_jobs_external"),
        totals(flows.loc[~same], home, "outbound_jobs_external"),
        totals(flows.loc[same], home, "internal_jobs"),
        totals(flows.loc[cross], work, "inbound_jobs_cross_state"),
        totals(flows.loc[cross], home, "outbound_jobs_cross_state"),
    ]
    features = pd.concat(metrics, axis=1).fillna(0).astype("int64")
    features["external_inbound_share"] = features["inbound_jobs_external"] / features["workplace_jobs_total"].where(
        features["workplace_jobs_total"].gt(0)
    )
    features["external_outbound_share"] = features["outbound_jobs_external"] / features["resident_jobs_total"].where(
        features["resident_jobs_total"].gt(0)
    )
    features["cross_state_inbound_share"] = features["inbound_jobs_cross_state"] / features["workplace_jobs_total"].where(
        features["workplace_jobs_total"].gt(0)
    )
    features["cross_state_outbound_share"] = features["outbound_jobs_cross_state"] / features["resident_jobs_total"].where(
        features["resident_jobs_total"].gt(0)
    )
    if not (features["internal_jobs"] + features["inbound_jobs_external"]).eq(features["workplace_jobs_total"]).all():
        raise ValueError("Workplace jobs do not split into internal + external.")
    features = features.reset_index()
    features["year"] = 2021
    features["job_type"] = "JT00"
    return features


def build_weights(flows: pd.DataFrame) -> pd.DataFrame:
    same = flows["origin_state"].eq(flows["destination_state"]) & flows["origin_zcta"].eq(flows["destination_zcta"])
    weights = flows.loc[~same].copy()
    inbound_total = weights.groupby(["destination_state", "destination_zcta"])["commute_jobs"].transform("sum")
    outbound_total = weights.groupby(["origin_state", "origin_zcta"])["commute_jobs"].transform("sum")
    weights["inbound_weight"] = weights["commute_jobs"] / inbound_total
    weights["outbound_weight"] = weights["commute_jobs"] / outbound_total
    inbound_check = weights.groupby(["destination_state", "destination_zcta"])["inbound_weight"].sum()
    outbound_check = weights.groupby(["origin_state", "origin_zcta"])["outbound_weight"].sum()
    if not inbound_check.sub(1).abs().le(1e-8).all() or not outbound_check.sub(1).abs().le(1e-8).all():
        raise ValueError("Weights do not sum to 1.")
    return weights


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    lookup = load_block_to_zcta()
    flows, audit, unmatched = build_flows(lookup)
    features = build_features(flows)
    weights = build_weights(flows)

    flows.to_csv(OUTPUT / "njny_commute_zcta_flows_2021.csv", index=False)
    audit.to_csv(OUTPUT / "njny_commute_processing_audit_2021.csv", index=False)
    features.to_csv(OUTPUT / "njny_commute_zcta_features_2021.csv", index=False)
    weights.to_csv(OUTPUT / "njny_commute_zcta_weights_2021.csv", index=False)
    if not unmatched.empty:
        unmatched.to_csv(OUTPUT / "njny_commute_unmapped_zcta_records_2021.csv", index=False)

    print(audit.to_string(index=False))
    print("Regions:", features.groupby("state").size().to_dict())
    print("Weight rows:", len(weights))
    print("Saved to:", OUTPUT)


if __name__ == "__main__":
    main()
