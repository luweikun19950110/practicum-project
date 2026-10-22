# NJ-only feature plan

## Study scope

Forecast NJ regions only. Build the commuting-pressure network using eligible NJ origins AND NJ destinations. Keep all eligible NJ origins when later selecting a smaller set of prediction destinations. Remove NY region rows and NJ-NY cross-state predictors from this version. Existing NJ-NY commuting features and normalized weights cannot simply be filtered and called NJ-only measures: recompute the denominator on the specified NJ network.

The current daily case scaffold contains 598 reference identifiers by 1,461 calendar days (873,678 records). Of these, 596 have positive included onset records. The final modeling cohort may be smaller after geographic and population validation. ZIP is the source identifier; do not silently rename it ZCTA without a validated mapping.

## Outcome and timing

C(i,t) is the recorded-onset count in the NJ daily panel after exact full-row deduplication. Per the user's confirmed rule, absent ZIP/date groups are zero within the agreed data coverage. A source row without illness onset date is still excluded from onset-date aggregation, not assigned an arbitrary date or zero. Approximately 60.65% of original rows lack onset, so this is a recorded-onset target, not a claim to all infections. The infection-episode unit still needs confirmation. Do not sum numrecs.

Targets: C(i,t+h), h=1,...,14. Targets and future observed trajectories are labels, not input features. A future target's calendar categories are known in advance. Confirm report-date/availability semantics before claiming onset data were observable at the forecast date.

## Feature groups

A. Historical counts and calendar: cases_today, lags 1/7/14, forecast-origin weekday/month, target weekday/month.

B. Local trends: trailing 7/14-day totals and rates, week-over-week change, optional rolling means, velocity, acceleration, jerk, rolling standard deviation and days since a positive record. Rolling totals versus means are exact rescalings; do not include both by default. Jerk is a third-order difference. No centered/future-looking windows.

C. Regional and NJ-network attributes: population, land area, density, NJ-network employment scales, NJ external incoming/outgoing volumes, within-region jobs, and NJ-network external commuting shares. These counts/shares describe the represented NJ network, not total employment with all out-of-state connections. Population and commuting inputs are static 2021-vintage estimates. Age and income are excluded.

D. NJ commuting-weighted COVID pressure: 7-day and 14-day trailing cumulative rates weighted by NJ-only normalized inbound connections. Route weights are intermediate data, not additional origin-destination rows in the final panel. Include source-weight coverage as a diagnostic. The pressure is a proxy for connected regional activity, not an infection probability or an estimate of infected commuters.

## Removed from this version

- NY region outcomes and NY-origin case-rate inputs.
- Cross-state inflow/outflow counts and shares as model predictors.
- Original NJ-NY inbound/outbound weights as the NJ-only normalization.
- Full NJ-NY pressure and NJ partial-contribution pressure under the old NJ-NY denominator.

## Remaining work

1. Confirm the counting unit, geography mapping and eligible NJ cohort. Preserve the user's zero-record rule within confirmed source coverage.
2. Filter both endpoints to NJ, recalculate all labeled NJ-network counts/shares and weights, and validate weight sums.
3. Join population, generate historical case features and compute the two pressure windows without expanding every link by every day.
4. Build 1–14-day labels, split chronologically and remove training/validation origins whose targets cross split boundaries. Fit preprocessing/feature selection only on training data and choose settings on validation data.
5. Compare models using the same outcomes/splits and with versus without commuting pressure. Static regional covariates are absorbed by full region fixed effects in a fixed-effects Dynamic Panel model.
6. Derive forecast trajectories and outbreak warnings. PR-AUC and lead time evaluate outbreak outputs; residual Moran's I diagnoses geographic structure in count forecast residuals. MAE/RMSE can supplement count diagnostics.
7. Stage Two tests whether other respiratory diseases follow COVID-derived regional signals. Align dates, geography and outcome units. The current data support NJ-to-NJ analysis; NJ-to-NY validation requires adequate NY outcomes.

Status: this is the revised candidate feature specification. It does not claim that the existing NJ-NY files or the new real-data feature panel have already been rebuilt. The final input feature subset is chosen during chronological model validation.
