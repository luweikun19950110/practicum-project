# NJ workplace inbound weights

This is the commute piece of the training table: for each New Jersey workplace and each date, a pressure score built from where its outside workers live.

The finished training row will be:

| zipcode | date | pressure |
|---|---|---|
| NJ workplace ZCTA | the day | sum of (inbound weight × that home area's cases that day) |

Weights do not depend on the date. Cases do. So the system is two stages.

1. `build_nj_inbound_weights.py` turns Census job files into weights. Run this when the LODES year changes.
2. `pressure_from_cases()` joins those weights to a case file. Run this when the case file changes, without rebuilding the weights.

The step-by-step notebook is `nj_inbound_weights.ipynb`. Run it from the project root.

## What the plan asked for

- Destinations are New Jersey only. That is the workplace people commute into.
- Origins are other New Jersey ZCTAs, plus New York City. Not the rest of New York State, and not Pennsylvania or anywhere else.
- `S000` is the job count. Summed to a ZCTA pair, it is the jobs on that home-to-work link.
- Same home and work ZCTA is excluded from the weights.
- For each workplace, weight = jobs on that link / all outside jobs into that workplace.
- Later, pressure = sum of weight × cases that day. This waits on a case file.

## Where files go

```
Dhruvesh/Data/LODES/
  nj_od_main_JT00_2021.csv.gz    home and work both in New Jersey
  nj_od_aux_JT00_2021.csv.gz     work in New Jersey, home in another state
  nj_xwalk.csv.gz                New Jersey block → ZCTA
  ny_xwalk.csv.gz                New York block → ZCTA

Dhruvesh/Data/cases/cases.csv    later: zipcode, date, cases
                                 zipcode here is the HOME area
```

The OD files are census blocks, not ZIP codes. A block id is 15 digits: state (2) + county (3) + tract + block. State `34` is New Jersey. State `36` is New York. The crosswalks are what turn a block into a ZCTA. Both are required, because New York City homes are not in the New Jersey crosswalk.

`nj_od_main` never contains a cross-state commute. `nj_od_aux` contains every state that sends workers into New Jersey. New York City is not labeled. It is filtered by the first five digits of the home block:

| County | Code |
|---|---|
| Bronx | 36005 |
| Brooklyn | 36047 |
| Manhattan | 36061 |
| Queens | 36081 |
| Staten Island | 36085 |

New York main and New York aux files are not used. Those jobs have a workplace in New York. This table only keeps New Jersey workplaces.

Another LODES year: download `nj_od_main_JT00_YEAR.csv.gz` and `nj_od_aux_JT00_YEAR.csv.gz` from https://lehd.ces.census.gov/data/lodes/LODES8/nj/od/ into `Data/LODES`, change `YEAR` at the top of `build_nj_inbound_weights.py`, and run the script. The crosswalks are not yearly files.

A different case year does not need a new LODES build. Keep the 2021 weights and point `pressure_from_cases()` at the new case file.

## How the code follows the plan

`block_lookup()` stacks the two crosswalks into one map from block id to ZCTA. If the same block appeared twice, the script stops.

`nj_internal_flows()` reads `nj_od_main`. It keeps a row only when the home block and the work block both start with `34`. That is the New Jersey to New Jersey piece.

`nyc_to_nj_flows()` reads `nj_od_aux`. It keeps a row only when the work block starts with `34` and the home block starts with one of the five New York City county codes. Everyone else in that file is dropped.

Both functions call `_accumulate()`, which:

- reads the file in chunks of 250,000 rows
- applies that keep rule
- maps both blocks to ZCTAs
- drops a row if either end is not a real 5-digit ZCTA (`00000` and `99999` count as missing)
- adds `S000` for rows that share the same home state, home ZCTA, and work ZCTA

`build_flows()` stacks the two results and renames `S000` to `commute_jobs`. It marks `same_zcta` when the home ZCTA equals the work ZCTA. Those rows stay in the flow file so the audit can still see them.

`build_weights()` drops `same_zcta` rows. This is the hashmap step: group by workplace ZCTA, sum outside jobs, divide each link by that sum. The name of the column is `inbound_weight`. The script checks that the weights for every workplace sum to 1, and stops if they do not.

`pressure_from_cases()` is the last step and is not run by `main()`. It expects columns `zipcode`, `date`, and `cases`. It joins on home ZCTA, multiplies weight by cases, and sums to the workplace and date. If any home area that feeds that workplace has no case row that day, `pressure` is left blank. `pressure_observed` is the sum over homes that did match, and `weight_coverage` is the share of outside jobs those homes account for. Filling a missing home with zero would treat that place as having no cases.

## What the 2021 run produced

| Piece | Result |
|---|---|
| New Jersey → New Jersey jobs | 3,439,824 |
| New York City → New Jersey jobs | 123,507 |
| Outside links, after dropping same-ZCTA | 212,347 |
| New Jersey workplaces | 590 |
| Home links inside New Jersey | 181,436 |
| Home links from New York City | 30,911 |

Saved in `commute_outputs/`:

- `nj_inbound_flows_2021.csv` — every home → New Jersey work link, including same-ZCTA
- `nj_inbound_weights_2021.csv` — outside links plus `inbound_weight`
- `nj_inbound_audit_2021.csv` — raw rows, kept rows, and unmapped rows for each source file

## How to rerun

From the project root:

```bash
python Dhruvesh/build_nj_inbound_weights.py
```

Or open `Dhruvesh/nj_inbound_weights.ipynb` and run the cells from the top. The notebook expects the project folder as the working directory.

When `Dhruvesh/Data/cases/cases.csv` exists:

```python
import pandas as pd
from build_nj_inbound_weights import pressure_from_cases

weights = pd.read_csv("Dhruvesh/commute_outputs/nj_inbound_weights_2021.csv", dtype={"origin_zcta": str, "destination_zcta": str})
cases = pd.read_csv("Dhruvesh/Data/cases/cases.csv")
pressure = pressure_from_cases(weights, cases)
```

`pressure` has `zipcode`, `date`, `pressure`, `pressure_observed`, and `weight_coverage`. Join `zipcode` and `date` onto the training panel. The training zip code is the workplace.
