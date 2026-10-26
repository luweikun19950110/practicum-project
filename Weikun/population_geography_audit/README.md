# NJ population and geography audit

The eight invalid denominators are all **zero population estimates already present in the original ACS population CSV**. None is a missing population row or a population join-value error. All eight identifiers also appear as ZCTAs in the supplied Gazetteer and LODES block crosswalk.

| Identifier | ACS population estimate | ACS MOE | LODES blocks | Included onset records | External NJ jobs out | NJ destinations |
|---|---:|---:|---:|---:|---:|---:|
| 07703 | 0 | 13 | 38 | 16 | 10 | 9 |
| 07831 | 0 | 13 | 1 | 5 | 24 | 17 |
| 08011 | 0 | 13 | 2 | 4 | 15 | 14 |
| 08073 | 0 | 13 | 7 | 24 | 69 | 44 |
| 08095 | 0 | 13 | 3 | 9 | 19 | 18 |
| 08217 | 0 | 13 | 2 | 6 | 16 | 14 |
| 08245 | 0 | 13 | 2 | 3 | 17 | 14 |
| 08858 | 0 | 13 | 10 | 49 | 32 | 29 |

`B01003_001E` is the population estimate used as the denominator; `B01003_001M` is the margin of error. The value 13 in the MOE field must not be substituted as population. A zero ACS estimate with a nonzero margin of error does not establish that a place has no residents. Positive recorded-onset counts and commuting-job records in the same identifier do not supply a valid population denominator either.

## What this verifies

1. The raw population GEO_ID suffix, NAME identifier and merged ZCTA identifier agree. Merged population equals the original estimate for every audited identifier.
2. The Gazetteer supplies a land-area record for each audited ZCTA; it does not supply population.
3. The LODES crosswalk maps Census blocks to each audited ZCTA in NJ. It does not contain a postal-ZIP correspondence field. Its supplied createdate is 20251202; a 2021 commuting flow year does not mean every geographic input is a 2021 postal correspondence.
4. Consequently, code presence and value transfer are verified, but the residence postal ZIP in the case file is not validated against ZCTA geography by these files. The mapping status must remain unvalidated.

## Consequences and next decisions

The current strict pressure feature is unavailable for 128 destinations linked to these zero-denominator origins, plus eight separate destinations with no external NJ inflow. This explains the 136 excluded pressure-comparison regions. No population values or model files were changed by this audit.

The supplied files cannot repair these eight denominators or establish an authoritative postal ZIP-to-ZCTA correspondence. Do not replace population with MOE, one, workplace jobs, a neighboring area's population or an arbitrary positive value. A compatible alternative population source and a proper postal ZIP–ZCTA correspondence would require additional evidence.

If proceeding using the current sources, a separately labeled sensitivity experiment may restrict origins to valid population denominators, recompute inbound weights over those origins, and retain/report the represented source-weight fraction for every destination. This is a changed pressure definition, not correction of the original complete-source pressure. It must be compared on common regions/dates; destinations with no remaining valid inflow still have undefined pressure.

## Files inspected

- Original ACS: `NJNY_Population 2021.csv.csv`, GEO_ID, NAME, B01003_001E and B01003_001M.
- Gazetteer: `2021_Gaz_zcta_national.txt`, GEOID and ALAND.
- LODES: `nj_xwalk.csv.gz`, tabblk2020, zcta, stusps and locality metadata.
- Existing regional attributes and external route weights under `Weikun`.
- `Real NJ COVID Zip.csv`, only ZIP/date and aggregate onset counts.

All calculations are reproducible with the audit notebook. The audit creates separate aggregate outputs and preserves all input files.
