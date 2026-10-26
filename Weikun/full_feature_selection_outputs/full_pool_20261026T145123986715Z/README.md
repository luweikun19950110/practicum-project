# Full candidate pool and grouped feature screening

Common cohort: 585 regions. Validation only, horizons 1/2/3, weekly refits. No test evaluated. FULL is the complete usable FE representation; metadata, exact duplicates and static FE-absorbed columns are audited separately.

Start with validation_ranking.csv and group_selection_evidence.csv. Positive FULL-minus-candidate delta favors the smaller model. Group removal is assessed one group at a time: do not assume multiple individually removable groups can all be deleted together without refitting. No final feature set is automatically selected.

P-values use paired DATE-level loss differences with HAC bandwidth 14 and Holm adjustment across this run. CIs use 2,000 14-day date-block resamples of fixed saved forecasts. They are exploratory and pointwise. Coefficient p-values are approximate clustered FE OLS calculations, not causal, and dynamic FE bias remains uncorrected.

Calendar rank filtering uses training data only. A month absent from a training window has no identified effect; its coefficient is omitted for that refit. The month effect may therefore be unavailable at the start of a new month. No-prior-case gaps are censored at available panel history and explicitly flagged. Undefined local rates are handled through a fixed valid-population cohort, never imputed as observed zeros.

Next: choose a parsimonious candidate using MAE/RMSE, uncertainty, and horizon stability; jointly refit the chosen combination; check 60-day sensitivity. Do not select only by coefficient p-values. Earlier test results have already been inspected.
