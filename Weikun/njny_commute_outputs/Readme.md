# NJ–NY Commuting Data Outputs

This folder contains commuting connections and regional features generated from **2021 U.S. Census LODES data (JT00: all jobs)**.

The study region includes **New Jersey and New York State**, covering four directions: NJ → NJ, NY → NY, NJ → NY, and NY → NJ. Connections involving other states are excluded.

Geographic units are **state × ZCTA**. ZCTA stands for ZIP Code Tabulation Area, a statistical approximation of a postal ZIP area. Job counts describe annual residence–workplace connections, not daily trips or unique commuters.

## 1. njny_commute_zcta_flows_2021.csv

Each row represents a directed connection between a residential region and a workplace region.

| Column | Meaning |
|---|---|
| origin_state | Residential state: NJ or NY |
| origin_zcta | Residential ZCTA |
| destination_state | Workplace state: NJ or NY |
| destination_zcta | Workplace ZCTA |
| commute_jobs | Jobs associated with this connection |
| year | Data year: 2021 |
| job_type | Job category: JT00 |

For example, NJ 07001 → NJ 07002 with 27 jobs means 27 jobs are associated with people living in NJ 07001 and working in NJ 07002. The reverse direction is recorded separately. Within-region connections are retained.

**Project use:** Calculate commuting weights between regions and later combine those weights with disease data to construct commuting-weighted epidemic pressure. Weights and epidemic pressure have not yet been calculated.

## 2. njny_commute_zcta_features_2021.csv

This file summarizes the connection table into one row per state–ZCTA combination. It contains **598 NJ regions and 1,826 NY regions** appearing in the valid commuting records.

| Column | Meaning |
|---|---|
| state | Region’s state |
| zcta | Region identifier |
| resident_jobs_total | Jobs associated with residents of this region working within NJ or NY |
| workplace_jobs_total | Jobs located in this region associated with residents living within NJ or NY |
| inbound_jobs_external | Jobs associated with residents of other regions working here |
| outbound_jobs_external | Jobs associated with this region’s residents working elsewhere |
| internal_jobs | Jobs with residence and workplace in the same state–ZCTA |
| inbound_jobs_cross_state | Jobs associated with residents of the other study state working here |
| outbound_jobs_cross_state | Jobs associated with this region’s residents working in the other study state |
| external_inbound_share | External inbound jobs ÷ workplace jobs total |
| external_outbound_share | External outbound jobs ÷ resident jobs total |
| cross_state_inbound_share | Cross-state inbound jobs ÷ workplace jobs total |
| cross_state_outbound_share | Cross-state outbound jobs ÷ resident jobs total |
| year | Data year: 2021 |
| job_type | Job category: JT00 |

“External” means outside the focal state–ZCTA, within the NJ–NY study region. **Cross-state jobs are already included in external jobs; do not add them again.** Shares are missing when their denominator is zero.

**Project use:** Provide annual regional commuting attributes for modeling. These values do not change daily. Some columns are mathematically dependent, so they should not all be included together in a linear model. Time-invariant attributes are absorbed by regional fixed effects in a fixed-effects Dynamic Panel model.

## 3. njny_commute_processing_audit_2021.csv

This file documents processing for each of the four directions, including original row counts, retained row counts, excluded other-state records, unmatched ZCTA records, and job totals.

The final mapped job totals are:

| Direction | Retained jobs |
|---|---:|
| NJ → NJ | 3,439,824 |
| NY → NY | 7,897,753 |
| NJ → NY | 494,304 |
| NY → NJ | 187,042 |
| Total | 12,018,923 |

Row counts and job counts differ because a Block-to-Block record can represent multiple jobs.

## 4. njny_commute_unmapped_zcta_records_2021.csv

This file preserves **2,299 records** with no valid ZCTA at one or both endpoints. These records are excluded from the connection and feature tables, rather than assigned to an invented region. Their counts and job totals are documented in the audit file.

## Reading and Using the Files

Read ZCTA identifiers as text to preserve leading zeros, such as `07001`. Retain both state and ZCTA as the region key.

These outputs replace the earlier NJ-only outputs for the two-state analysis. **Do not add the old and new datasets together.**

The files do not contain population, population density, daily disease cases, or model predictions. All commuting features are based on the NJ–NY study region and exclude connections with other states.

Source: [U.S. Census LODES](https://lehd.ces.census.gov/data/lodes/LODES8/)
