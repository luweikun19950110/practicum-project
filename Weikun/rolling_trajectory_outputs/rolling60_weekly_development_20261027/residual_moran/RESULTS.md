# Residual spatial autocorrelation: rolling60 weekly model

  scope period  horizon  valid_tests  mean_Moran_I  median_Moran_I  raw_p_below_05_share  BH_q_below_05_share  positive_I_and_BH_q_below_05_share
overall    all        1          243      0.025396        0.019898              0.333333             0.246914                            0.242798
overall    all        2          243      0.031826        0.024509              0.403292             0.308642                            0.304527
overall    all        3          243      0.038911        0.031635              0.481481             0.366255                            0.362140

Moran I is computed separately for each origin and horizon. A positive value suggests clustering of similarly signed forecast errors under the chosen geographic weights. Summary means are descriptive; they do not have a pooled p-value. Permutation p-values and BH q-values are exploratory, conditional on the fitted model, residual exchangeability, and unvalidated ZIP-ZCTA identifiers. Count residual magnitudes vary by region; this can affect the interpretation. Nonsignificance does not prove spatial adequacy. K4/K12 are sensitivity checks, not selected by results. No model refit.
