# Residual spatial autocorrelation: rolling60 weekly model

  scope period  horizon  valid_tests  mean_Moran_I  median_Moran_I  raw_p_below_05_share  BH_q_below_05_share  positive_I_and_BH_q_below_05_share
overall    all        1          362      0.020579        0.016071              0.254144             0.174033                            0.165746
overall    all        2          362      0.026847        0.019101              0.303867             0.204420                            0.198895
overall    all        3          362      0.031789        0.022705              0.323204             0.234807                            0.232044

Moran I is computed separately for each origin and horizon. A positive value suggests clustering of similarly signed forecast errors under the chosen geographic weights. Summary means are descriptive; they do not have a pooled p-value. Permutation p-values and BH q-values are exploratory, conditional on the fitted model, residual exchangeability, and unvalidated ZIP-ZCTA identifiers. Count residual magnitudes vary by region; this can affect the interpretation. Nonsignificance does not prove spatial adequacy. K4/K12 are sensitivity checks, not selected by results. No model refit.
