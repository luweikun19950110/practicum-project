"""NJ workplace inbound weights from other NJ ZCTAs and New York City.

Put these files in Dhruvesh/Data/LODES (YEAR is the LODES year, default 2021):

  nj_od_main_JT00_{YEAR}.csv.gz   home and work both in New Jersey
  nj_od_aux_JT00_{YEAR}.csv.gz    work in New Jersey, home in another state
  nj_xwalk.csv.gz                 NJ census block -> ZCTA
  ny_xwalk.csv.gz                 NY census block -> ZCTA

Download a different year from:
  https://lehd.ces.census.gov/data/lodes/LODES8/nj/od/

Change YEAR below and rerun. The crosswalks are not yearly files.

Outputs in Dhruvesh/commute_outputs:
  nj_inbound_flows_{YEAR}.csv     one row per home ZCTA -> NJ work ZCTA
  nj_inbound_weights_{YEAR}.csv   same rows plus inbound_weight
  nj_inbound_audit_{YEAR}.csv

S000 is the job count on a block-to-block link. This script sums it to ZCTA pairs.
Same-ZCTA links are kept in the flow file and dropped before the weights.
"""

from pathlib import Path

import pandas as pd

YEAR = 2021
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "Data" / "LODES"
OUTPUT = ROOT / "commute_outputs"

# New York City counties inside state 36. First 5 digits of the home block.
NYC_COUNTIES = {"36005", "36047", "36061", "36081", "36085"}


def block_lookup() -> pd.Series:
    parts = []
    for state in ("nj", "ny"):
        path = DATA / f"{state}_xwalk.csv.gz"
        table = pd.read_csv(path, usecols=["tabblk2020", "zcta"], dtype="string")
        parts.append(table)
    xwalk = pd.concat(parts, ignore_index=True)
    if xwalk["tabblk2020"].duplicated().any():
        raise ValueError("Duplicate block ids in the crosswalks.")
    return xwalk.set_index("tabblk2020")["zcta"]


def valid_zcta(series: pd.Series) -> pd.Series:
    return series.str.fullmatch(r"[0-9]{5}").fillna(False) & ~series.isin(["00000", "99999"])


def _accumulate(path: Path, keep_mask_fn, lookup: pd.Series, origin_state: str) -> tuple[pd.DataFrame, dict]:
    parts = []
    raw_rows = raw_jobs = kept_rows = kept_jobs = unmapped_rows = unmapped_jobs = 0
    for chunk in pd.read_csv(
        path,
        usecols=["h_geocode", "w_geocode", "S000"],
        dtype={"h_geocode": "string", "w_geocode": "string"},
        chunksize=250_000,
    ):
        raw_rows += len(chunk)
        raw_jobs += int(chunk["S000"].sum())
        subset = chunk.loc[keep_mask_fn(chunk)].copy()
        if subset.empty:
            continue
        subset["origin_zcta"] = subset["h_geocode"].map(lookup)
        subset["destination_zcta"] = subset["w_geocode"].map(lookup)
        mapped = valid_zcta(subset["origin_zcta"]) & valid_zcta(subset["destination_zcta"])
        unmapped_rows += int((~mapped).sum())
        unmapped_jobs += int(subset.loc[~mapped, "S000"].sum())
        subset = subset.loc[mapped]
        kept_rows += len(subset)
        kept_jobs += int(subset["S000"].sum())
        subset["origin_state"] = origin_state
        parts.append(
            subset.groupby(["origin_state", "origin_zcta", "destination_zcta"], as_index=False)["S000"].sum()
        )
    flows = (
        pd.concat(parts, ignore_index=True).groupby(
            ["origin_state", "origin_zcta", "destination_zcta"], as_index=False
        )["S000"].sum()
        if parts
        else pd.DataFrame(columns=["origin_state", "origin_zcta", "destination_zcta", "S000"])
    )
    audit = {
        "source_file": path.name,
        "origin_state": origin_state,
        "raw_rows": raw_rows,
        "raw_jobs": raw_jobs,
        "kept_rows": kept_rows,
        "kept_jobs": kept_jobs,
        "unmapped_rows": unmapped_rows,
        "unmapped_jobs": unmapped_jobs,
    }
    return flows, audit


def nj_internal_flows(lookup: pd.Series) -> tuple[pd.DataFrame, dict]:
    path = DATA / f"nj_od_main_JT00_{YEAR}.csv.gz"

    def keep(chunk: pd.DataFrame) -> pd.Series:
        return chunk["h_geocode"].str[:2].eq("34") & chunk["w_geocode"].str[:2].eq("34")

    return _accumulate(path, keep, lookup, "NJ")


def nyc_to_nj_flows(lookup: pd.Series) -> tuple[pd.DataFrame, dict]:
    path = DATA / f"nj_od_aux_JT00_{YEAR}.csv.gz"

    def keep(chunk: pd.DataFrame) -> pd.Series:
        # Work block is New Jersey. Home block is one of the five NYC counties.
        return chunk["w_geocode"].str[:2].eq("34") & chunk["h_geocode"].str[:5].isin(NYC_COUNTIES)

    return _accumulate(path, keep, lookup, "NY")


def build_flows(lookup: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    nj, nj_audit = nj_internal_flows(lookup)
    nyc, nyc_audit = nyc_to_nj_flows(lookup)
    flows = pd.concat([nj, nyc], ignore_index=True)
    flows = flows.rename(columns={"S000": "commute_jobs"})
    flows["year"] = YEAR
    flows["same_zcta"] = flows["origin_zcta"].eq(flows["destination_zcta"])
    audit = pd.DataFrame([nj_audit, nyc_audit])
    return flows, audit


def build_weights(flows: pd.DataFrame) -> pd.DataFrame:
    outside = flows.loc[~flows["same_zcta"]].copy()
    totals = outside.groupby("destination_zcta")["commute_jobs"].transform("sum")
    outside["inbound_weight"] = outside["commute_jobs"] / totals
    check = outside.groupby("destination_zcta")["inbound_weight"].sum()
    if not check.sub(1).abs().le(1e-8).all():
        raise ValueError("Inbound weights do not sum to 1 for every NJ workplace.")
    return outside.drop(columns=["same_zcta"])


def pressure_from_cases(weights: pd.DataFrame, cases: pd.DataFrame) -> pd.DataFrame:
    """cases columns: zipcode, date, cases.

    pressure = sum over origins of inbound_weight * cases that day.
    If any origin feeding that workplace has no case row that day, pressure
    is left blank. pressure_observed is the sum over origins that did match.
    """
    needed = {"zipcode", "date", "cases"}
    missing = needed - set(cases.columns)
    if missing:
        raise ValueError(f"Cases file is missing columns: {sorted(missing)}")
    daily = cases.copy()
    daily["zipcode"] = daily["zipcode"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(5)
    daily["date"] = pd.to_datetime(daily["date"])
    daily["cases"] = pd.to_numeric(daily["cases"], errors="raise")
    daily = daily.groupby(["zipcode", "date"], as_index=False)["cases"].sum()

    linked = weights.merge(daily, left_on="origin_zcta", right_on="zipcode", how="left")
    linked["weighted_cases"] = linked["inbound_weight"] * linked["cases"]
    known = linked.loc[linked["cases"].notna()]
    coverage = known.groupby(["destination_zcta", "date"])["inbound_weight"].sum().rename("weight_coverage")
    observed = known.groupby(["destination_zcta", "date"])["weighted_cases"].sum().rename("pressure_observed")
    out = pd.concat([observed, coverage], axis=1).reset_index()
    out["pressure"] = out["pressure_observed"].where(out["weight_coverage"].sub(1).abs().le(1e-8))
    out = out.rename(columns={"destination_zcta": "zipcode"})
    return out[["zipcode", "date", "pressure", "pressure_observed", "weight_coverage"]]


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    lookup = block_lookup()
    flows, audit = build_flows(lookup)
    weights = build_weights(flows)
    flows.to_csv(OUTPUT / f"nj_inbound_flows_{YEAR}.csv", index=False)
    weights.to_csv(OUTPUT / f"nj_inbound_weights_{YEAR}.csv", index=False)
    audit.to_csv(OUTPUT / f"nj_inbound_audit_{YEAR}.csv", index=False)
    print(audit.to_string(index=False))
    print("Flow rows:", len(flows), "outside rows:", len(weights))
    print("NJ workplaces:", weights["destination_zcta"].nunique())
    print(weights.groupby("origin_state").size().to_string())
    print("Saved to:", OUTPUT)


if __name__ == "__main__":
    main()
