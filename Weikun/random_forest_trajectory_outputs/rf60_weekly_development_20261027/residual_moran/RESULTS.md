# Residual spatial autocorrelation: rolling60 weekly model

  scope period  horizon  valid_tests  mean_Moran_I  median_Moran_I  raw_p_below_05_share  BH_q_below_05_share  positive_I_and_BH_q_below_05_share
overall    all        1          243      0.019768        0.014959              0.288066             0.197531                            0.185185
overall    all        2          243      0.024491        0.019282              0.349794             0.238683                            0.226337
overall    all        3          243      0.027791        0.022199              0.411523             0.283951                            0.271605

Moran I is computed separately for each origin and horizon. A positive value suggests clustering of similarly signed forecast errors under the chosen geographic weights. Summary means are descriptive; they do not have a pooled p-value. Permutation p-values and BH q-values are exploratory, conditional on the fitted model, residual exchangeability, and unvalidated ZIP-ZCTA identifiers. Count residual magnitudes vary by region; this can affect the interpretation. Nonsignificance does not prove spatial adequacy. K4/K12 are sensitivity checks, not selected by results. No model refit.
