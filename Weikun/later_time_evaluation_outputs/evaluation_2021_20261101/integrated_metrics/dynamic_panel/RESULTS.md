# Residual spatial autocorrelation: rolling60 weekly model

  scope period  horizon  valid_tests  mean_Moran_I  median_Moran_I  raw_p_below_05_share  BH_q_below_05_share  positive_I_and_BH_q_below_05_share
overall    all        1          362      0.027663        0.017746              0.312155             0.223757                            0.218232
overall    all        2          362      0.034839        0.021569              0.375691             0.270718                            0.267956
overall    all        3          362      0.041203        0.025594              0.417127             0.306630                            0.306630

Moran I is computed separately for each origin and horizon. A positive value suggests clustering of similarly signed forecast errors under the chosen geographic weights. Summary means are descriptive; they do not have a pooled p-value. Permutation p-values and BH q-values are exploratory, conditional on the fitted model, residual exchangeability, and unvalidated ZIP-ZCTA identifiers. Count residual magnitudes vary by region; this can affect the interpretation. Nonsignificance does not prove spatial adequacy. K4/K12 are sensitivity checks, not selected by results. No model refit.
