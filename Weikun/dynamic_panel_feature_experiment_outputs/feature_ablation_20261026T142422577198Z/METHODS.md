# Methods and reporting guide

Primary comparison window is 30 days; 60 days is sensitivity. All specifications use the same fixed NJ cohort, validation origins, direct horizons 1/2/3 and weekly refitting. Model variants and eight planned comparisons were specified before this run. This is a feature-ablation experiment, not a final test or a causal study.

`delta_MAE_baseline_minus_candidate > 0` means the candidate improves prediction. Daily loss first averages over all common regions (and over horizons for the overall comparison). A two-sided HAC mean-loss test uses Bartlett bandwidth 14, with 7/28 sensitivity. All 64 planned p-values are Holm-adjusted together. The 95% moving-date-block bootstrap intervals are pointwise, not simultaneous; they resample saved forecast errors, not model fits. Every region/horizon shares the same sampled dates. Approximation quality depends on temporal dependence and stability; COVID regime shifts and repeatedly inspected validation data limit confirmatory interpretation. No per-row independent t-test is used.

Coefficient SEs cluster by region and training date using CR1 and an asymptotic normal reference, with about 30 or 60 date clusters. They are exploratory conditional linear-model calculations. Dynamic FE OLS lagged-outcome bias, endogeneity, short windows and specification selection are NOT corrected. Invalid cluster variances or rank deficiency yield unavailable SE/p-values, not fabricated significance. Repeated refits overlap: do not average coefficient p-values or treat refits as independent evidence. Use coefficient stability descriptively. A small coefficient p-value is not proof of forecast improvement or causal transmission.

Acceleration is C(t)-2C(t-1)+C(t-2); jerk additionally involves C(t-3). With C(t) and C(t-1) already included, these expand the effective lag basis, not independent epidemiological measurements. Velocity is omitted because it is exactly redundant with the basic model. Mean and sum of the same window are not both included. Static population/density coefficients are not identified separately from full region fixed effects.

Sargan/Hansen and Arellano-Bond AR(2) are not applicable: no GMM estimator/instruments are fitted here. Residual lag correlations are descriptive and not a substitute for those tests. Moran, PR-AUC and lead time are deferred until appropriate spatial weights and outbreak definitions exist. In-sample R-squared is not used to select features.

The outcome is retrospectively recorded onset rows, not all infections. Unknown onset records and unvalidated ZIP/ZCTA mapping remain upstream limitations. A favorable validation result is a candidate for further temporal validation, not final independent proof. Earlier 2022-2023 test results have already been inspected. Use a new untouched period or a prespecified nested temporal assessment for stronger final performance claims.

Reference methods: statsmodels two-way cluster covariance, HAC covariance and multiple-testing documentation. Implementations here use numpy/pandas and Python math; no statsmodels dependency is required.

- https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_cluster_2groups.html
- https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_hac.html
- https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html
