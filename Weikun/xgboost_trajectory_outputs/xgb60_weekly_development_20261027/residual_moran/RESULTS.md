# Residual spatial autocorrelation: rolling60 weekly model

  scope period  horizon  valid_tests  mean_Moran_I  median_Moran_I  raw_p_below_05_share  BH_q_below_05_share  positive_I_and_BH_q_below_05_share
overall    all        1          243      0.026861        0.019564              0.378601             0.271605                            0.263374
overall    all        2          243      0.032914        0.025660              0.419753             0.325103                            0.320988
overall    all        3          243      0.037613        0.029224              0.465021             0.399177                            0.395062

Moran I is computed separately for each origin and horizon. A positive value suggests clustering of similarly signed forecast errors under the chosen geographic weights. Summary means are descriptive; they do not have a pooled p-value. Permutation p-values and BH q-values are exploratory, conditional on the fitted model, residual exchangeability, and unvalidated ZIP-ZCTA identifiers. Count residual magnitudes vary by region; this can affect the interpretation. Nonsignificance does not prove spatial adequacy. K4/K12 are sensitivity checks, not selected by results. No model refit.
