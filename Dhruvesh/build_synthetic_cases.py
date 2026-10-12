"""Synthetic 2021 daily cases for NJ and NYC ZCTAs.

Outputs:
  temporary/nj_cases_2021.csv
  temporary/nyc_cases_2021.csv

Columns: zipcode, date, cases

The ZCTAs are the home areas in commute_outputs/nj_inbound_weights_2021.csv.
Population is the 2021 ACS table in Data/Census. Counts are fake. The shape
of the year follows the Northeast pattern of 2021: a January wave, a quiet
summer, a late-summer wave, and a December rise.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "temporary"
WEIGHTS = ROOT / "commute_outputs" / "nj_inbound_weights_2021.csv"
POPULATION = ROOT / "Data" / "Census" / "njny_zcta_population_density_2021.csv"
SEED = 42
DATES = pd.date_range("2021-01-01", "2021-12-31", freq="D")


def yearly_rate(day: np.ndarray, lead: float, winter_scale: float, omicron_scale: float) -> np.ndarray:
    """Expected cases per 100,000 people. `lead` pulls the waves earlier."""
    d = day + lead
    winter = 85 * winter_scale * np.exp(-0.5 * ((d - 18) / 28) ** 2)
    delta = 32 * np.exp(-0.5 * ((d - 250) / 18) ** 2)
    omicron = 160 * omicron_scale * np.exp(-0.5 * ((d - 375) / 16) ** 2)
    return 3.5 + winter + delta + omicron


def smooth_shock(rng: np.random.Generator, n: int, t: int, carry: float, scale: float) -> np.ndarray:
    shock = np.zeros((n, t))
    noise = rng.normal(0, scale, size=(n, t))
    for i in range(1, t):
        shock[:, i] = carry * shock[:, i - 1] + noise[:, i]
    return shock


def base_rates(zips: list[str], population: pd.Series, rng: np.random.Generator, lead: float, winter_scale: float, omicron_scale: float) -> pd.DataFrame:
    day = np.arange(len(DATES))
    phase = rng.integers(-7, 8, size=len(zips))
    susceptibility = rng.lognormal(mean=0.0, sigma=0.25, size=len(zips))
    region = smooth_shock(rng, 1, len(DATES), carry=0.92, scale=0.05)[0]
    local = smooth_shock(rng, len(zips), len(DATES), carry=0.8, scale=0.12)
    dow = np.where(DATES.dayofweek >= 5, 0.72, np.where(DATES.dayofweek == 0, 0.9, 1.0))
    rates = []
    for i, zipcode in enumerate(zips):
        curve = yearly_rate(day - phase[i], lead, winter_scale, omicron_scale)
        rates.append(curve * susceptibility[i] * np.exp(region + local[i]) * dow)
    frame = pd.DataFrame(np.vstack(rates), index=zips, columns=DATES)
    frame.index.name = "zipcode"
    return frame


def couple_nj(nj_rates: pd.DataFrame, nyc_rates: pd.DataFrame, weights: pd.DataFrame) -> pd.DataFrame:
    """Blend each NJ workplace toward the home areas that send it workers."""
    origins = list(nj_rates.index) + list(nyc_rates.index)
    origin_index = {zipcode: i for i, zipcode in enumerate(origins)}
    dests = list(nj_rates.index)
    dest_index = {zipcode: i for i, zipcode in enumerate(dests)}
    rows, cols, vals = [], [], []
    for origin, dest, weight in weights[["origin_zcta", "destination_zcta", "inbound_weight"]].itertuples(index=False):
        rows.append(dest_index[dest])
        cols.append(origin_index[origin])
        vals.append(float(weight))
    matrix = sparse.csr_matrix((vals, (rows, cols)), shape=(len(dests), len(origins)))
    origin_rates = np.vstack([nj_rates.to_numpy(), nyc_rates.to_numpy()])
    lagged = np.roll(origin_rates, 5, axis=1)
    lagged[:, :5] = origin_rates[:, :5]
    mixed = 0.75 * nj_rates.to_numpy() + 0.25 * (matrix @ lagged)
    return pd.DataFrame(mixed, index=nj_rates.index, columns=nj_rates.columns)


def draw_cases(rates: pd.DataFrame, population: pd.Series, rng: np.random.Generator) -> pd.DataFrame:
    pop = population.reindex(rates.index).astype(float).to_numpy()
    mu = rates.to_numpy() * (pop[:, None] / 100_000)
    mu = np.clip(mu, 0, None)
    # Gamma-Poisson: more ups and downs than a plain Poisson with the same mean.
    lam = rng.gamma(shape=4.0, scale=mu / 4.0)
    counts = rng.poisson(lam)
    frame = pd.DataFrame(counts, index=rates.index, columns=rates.columns)
    long = frame.stack().rename("cases").reset_index()
    long.columns = ["zipcode", "date", "cases"]
    long["date"] = pd.to_datetime(long["date"]).dt.strftime("%Y-%m-%d")
    return long.sort_values(["zipcode", "date"]).reset_index(drop=True)


def main() -> None:
    rng = np.random.default_rng(SEED)
    weights = pd.read_csv(WEIGHTS, dtype={"origin_zcta": str, "destination_zcta": str})
    population = pd.read_csv(POPULATION, dtype={"zcta": str}).set_index("zcta")["population"]
    nj_zips = sorted(weights.loc[weights.origin_state.eq("NJ"), "origin_zcta"].unique())
    nyc_zips = sorted(weights.loc[weights.origin_state.eq("NY"), "origin_zcta"].unique())

    nj_rates = base_rates(nj_zips, population, rng, lead=0, winter_scale=1.0, omicron_scale=1.0)
    nyc_rates = base_rates(nyc_zips, population, rng, lead=7, winter_scale=1.25, omicron_scale=1.3)
    nj_rates = couple_nj(nj_rates, nyc_rates, weights)

    nj_cases = draw_cases(nj_rates, population, rng)
    nyc_cases = draw_cases(nyc_rates, population, rng)
    OUT.mkdir(exist_ok=True)
    nj_path = OUT / "nj_cases_2021.csv"
    nyc_path = OUT / "nyc_cases_2021.csv"
    nj_cases.to_csv(nj_path, index=False)
    nyc_cases.to_csv(nyc_path, index=False)
    print(f"NJ  {nj_cases.zipcode.nunique()} zips  {len(nj_cases):,} rows  mean cases {nj_cases.cases.mean():.2f}")
    print(f"NYC {nyc_cases.zipcode.nunique()} zips  {len(nyc_cases):,} rows  mean cases {nyc_cases.cases.mean():.2f}")
    print("Saved", nj_path)
    print("Saved", nyc_path)


if __name__ == "__main__":
    main()
