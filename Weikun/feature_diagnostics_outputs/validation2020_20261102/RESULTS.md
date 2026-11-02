# NJ feature diagnostics: 2020 validation

Main full-feature models remain unchanged. Positive delta means removing the group increases error, so keeping it helps. All comparisons share 585 ZIPs, 243 daily forecast dates, three horizons, 60-day windows and weekly refits.

           model         drop_group  FULL_MAE  DROP_MAE  delta_MAE_DROP_minus_FULL  relative_increase_pct  ci95_low  ci95_high       p_Holm  p_HAC28_Holm_sensitivity
Dynamic Panel FE local_case_history  0.774283  0.956653                   0.182370              23.553383  0.092043   0.288168 4.971981e-05                  0.057218
Dynamic Panel FE commuting_pressure  0.774283  0.767056                  -0.007227              -0.933342 -0.027461   0.010094 1.000000e+00                  1.000000
Dynamic Panel FE           calendar  0.774283  0.778660                   0.004377               0.565338 -0.004488   0.015547 1.000000e+00                  1.000000
         XGBoost local_case_history  0.754299  0.780394                   0.026095               3.459554  0.015151   0.036881 7.137201e-08                  0.003731
         XGBoost commuting_pressure  0.754299  0.756246                   0.001947               0.258157 -0.000759   0.004819 7.297067e-01                  0.871619
         XGBoost           calendar  0.754299  0.756705                   0.002405               0.318900 -0.002897   0.008597 1.000000e+00                  1.000000
   Random Forest local_case_history  0.751885  1.415063                   0.663178              88.202006  0.277334   1.120811 6.030210e-04                  0.168191
   Random Forest commuting_pressure  0.751885  0.749545                  -0.002340              -0.311237 -0.006722   0.001597 9.484925e-01                  1.000000
   Random Forest           calendar  0.751885  0.748764                  -0.003122              -0.415206 -0.007348   0.000154 7.282867e-01                  0.335002

## Sensitivity finding

Local-history removal raises MAE for all models. Primary Holm-adjusted HAC7 p-values are small for all three, but HAC28 Holm sensitivity p-values are 0.0572 (DP), 0.00373 (XGBoost), and 0.1682 (RF). Only XGBoost remains below 0.05 under both choices. Pressure and calendar pointwise intervals cross zero for all models. Do not equate descriptive importance or coefficient sign stability with robust predictive significance.

## Interpretation limits
- Loss-difference p-values address average predictive differences, not causal effects or individual coefficient significance.
- Bootstrap intervals are pointwise, while primary HAC p-values use Holm correction over nine planned contrasts. They need not agree near a cutoff.
- Daily aggregation preserves cross-ZIP dependence; overlapping paths/refits cause serial dependence. HAC lags 7 and 28 and 14-day date blocks are exploratory sensitivity choices.
- This validation period was inspected previously. These diagnostics do not constitute untouched final testing.
- Feature groups overlap in information. Local-history removal retains pressure derived from other ZIP case histories and retains ZIP identity.
- Calendar combines weekday and month. Some month dummies are constant within a 60-day window and cannot be separately estimated in FE.
- Tree split importance is training-based and biased by correlated predictors/split opportunities. XGBoost gain and RF impurity rankings are different quantities; normalized values cannot be compared directly across model types.
- DP repeated coefficient fits overlap heavily and can have dynamic-panel bias. Coefficient ranges and sign shares are descriptive, not confidence intervals or causal estimates.
- A small p-value does not imply a large useful improvement. A large p-value does not establish no effect.
- No model or feature selection is made automatically; pressure remains in the main specification.