"""Build the 2021 training panel from commute weights and synthetic cases.

No demographics. Phases:

  1. Destination pressure: for each NJ workplace and day,
     sum over home ZCTAs of inbound_weight * that home's cases.
  2. NJ local series: daily cases, velocity, acceleration, jerk.
  3. Final table: NJ workplace-days with local series plus pressure.

Run from anywhere:
  python Dhruvesh/training/build_training_panel.py
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TRAINING = Path(__file__).resolve().parent
WEIGHTS = ROOT / "commute_outputs" / "nj_inbound_weights_2021.csv"
NJ_CASES = ROOT / "temporary" / "nj_cases_2021.csv"
NYC_CASES = ROOT / "temporary" / "nyc_cases_2021.csv"


def load_cases() -> pd.DataFrame:
    frames = []
    for path, state in ((NJ_CASES, "NJ"), (NYC_CASES, "NY")):
        frame = pd.read_csv(path, dtype={"zipcode": str})
        frame["zipcode"] = frame["zipcode"].str.zfill(5)
        frame["date"] = pd.to_datetime(frame["date"])
        frame["state"] = state
        frames.append(frame)
    cases = pd.concat(frames, ignore_index=True)
    return cases.groupby(["state", "zipcode", "date"], as_index=False)["cases"].sum()


def destination_pressure(weights: pd.DataFrame, cases: pd.DataFrame) -> pd.DataFrame:
    """Sum weight x origin cases up to each NJ workplace and date.

    The link-day table is not saved. 212,347 links x 365 days is about 77
    million rows. The destination sum is the table the training join needs.
    """
    origin_cases = cases.rename(columns={"zipcode": "origin_zcta", "cases": "origin_cases"})
    parts = []
    for _, day_cases in origin_cases.groupby(origin_cases["date"].dt.to_period("M")):
        linked = weights.merge(day_cases, on="origin_zcta", how="inner")
        linked["link_pressure"] = linked["inbound_weight"] * linked["origin_cases"]
        parts.append(
            linked.groupby(["destination_zcta", "date"], as_index=False).agg(
                pressure=("link_pressure", "sum"),
                weight_coverage=("inbound_weight", "sum"),
            )
        )
    pressure = pd.concat(parts, ignore_index=True)
    return pressure.sort_values(["destination_zcta", "date"]).reset_index(drop=True)


def nj_local_series(cases: pd.DataFrame) -> pd.DataFrame:
    nj = cases.loc[cases["state"].eq("NJ"), ["zipcode", "date", "cases"]].copy()
    nj = nj.sort_values(["zipcode", "date"]).reset_index(drop=True)
    nj = nj.rename(columns={"cases": "daily_cases"})
    grouped = nj.groupby("zipcode", sort=False)["daily_cases"]
    nj["velocity"] = grouped.diff()
    nj["acceleration"] = nj.groupby("zipcode", sort=False)["velocity"].diff()
    nj["jerk"] = nj.groupby("zipcode", sort=False)["acceleration"].diff()
    return nj


def main() -> None:
    TRAINING.mkdir(exist_ok=True)
    weights = pd.read_csv(
        WEIGHTS,
        dtype={"origin_zcta": str, "destination_zcta": str},
    )
    weights["origin_zcta"] = weights["origin_zcta"].str.zfill(5)
    weights["destination_zcta"] = weights["destination_zcta"].str.zfill(5)
    cases = load_cases()

    print("Phase 1: destination pressure")
    pressure = destination_pressure(weights, cases)
    pressure_path = TRAINING / "destination_pressure_2021.csv"
    pressure.to_csv(pressure_path, index=False)
    print(f"  rows {len(pressure):,}  workplaces {pressure.destination_zcta.nunique()}")
    print(f"  weight coverage min/max {pressure.weight_coverage.min():.6f} {pressure.weight_coverage.max():.6f}")

    print("Phase 2: NJ cases with velocity, acceleration, jerk")
    local = nj_local_series(cases)
    local_path = TRAINING / "nj_cases_derivatives_2021.csv"
    local.to_csv(local_path, index=False)
    print(f"  rows {len(local):,}  zips {local.zipcode.nunique()}")

    print("Phase 3: map pressure onto NJ workplace-days")
    final = local.merge(
        pressure,
        left_on=["zipcode", "date"],
        right_on=["destination_zcta", "date"],
        how="inner",
    ).drop(columns=["destination_zcta"])
    final["date"] = final["date"].dt.strftime("%Y-%m-%d")
    final_path = TRAINING / "training_panel_2021.csv"
    final.to_csv(final_path, index=False)
    print(f"  rows {len(final):,}  zips {final.zipcode.nunique()}")
    print(f"  saved {final_path}")


if __name__ == "__main__":
    main()
