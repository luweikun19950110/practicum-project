# Complete Lag 1–7 sweep: findings

These are exploratory 2020 validation results from controlled diagnostic FE specifications, not changes to the main full-feature models.

- L1 has the lowest MAE among the seven single-lag configurations (0.796049).
- L1+L2 has the lowest observed MAE (0.778484) and RMSE (1.433823) among the 13 configurations. Its MAE is 2.21% lower than L1. This is not a formal claim that it beats every other pair: tests below compare each configuration with L1 only.
- L1+L7 MAE is 0.788096, approximately 1.00% lower than L1, but it is not the best observed pair.
- L1+L2 endpoint direction agreement is 33.70%, versus 34.60% for L1. Better count error does not establish better direction prediction. The observed always-flat reference is approximately 56.8%.
- Initial-training coefficient p-values and validation predictive gains answer different questions and use different data periods. They must not be read as interchangeable evidence.
- Residual lag correlations describe remaining temporal dependence; they are not Arellano–Bond AR tests, and no GMM instrument-validity claim is made.
- All 1,365 fit audit rows satisfy latest training target <= fit date. Retrospective onset availability is still unverified.

| variant   |      MAE |    RMSE |      bias |   direction_accuracy |
|:----------|---------:|--------:|----------:|---------------------:|
| L1        | 0.796049 | 1.46574 | 0.0815494 |             0.345996 |
| L2        | 0.801395 | 1.47836 | 0.0839392 |             0.34767  |
| L3        | 0.803397 | 1.48445 | 0.0847251 |             0.346221 |
| L4        | 0.804214 | 1.48792 | 0.0837792 |             0.345039 |
| L5        | 0.807801 | 1.4965  | 0.0856914 |             0.345925 |
| L6        | 0.809943 | 1.50103 | 0.0861489 |             0.346446 |
| L7        | 0.818487 | 1.51824 | 0.0933887 |             0.348197 |
| L1_L2     | 0.778484 | 1.43382 | 0.0700704 |             0.337034 |
| L1_L3     | 0.779925 | 1.43841 | 0.0707344 |             0.338075 |
| L1_L4     | 0.779564 | 1.43877 | 0.0693505 |             0.33607  |
| L1_L5     | 0.781541 | 1.44336 | 0.0701386 |             0.337477 |
| L1_L6     | 0.783068 | 1.44643 | 0.0706052 |             0.336168 |
| L1_L7     | 0.788096 | 1.45525 | 0.0749867 |             0.340586 |

## Paired validation comparisons against L1

| candidate   |   delta_MAE_L1_minus_candidate |    ci95_low |   ci95_high |      p_HAC7 |     p_HAC28 |   p_Holm_HAC7 |   p_Holm_HAC28 |
|:------------|-------------------------------:|------------:|------------:|------------:|------------:|--------------:|---------------:|
| L2          |                    -0.00534674 | -0.00825393 | -0.0028424  | 1.03148e-05 | 0.00105282  |   6.18886e-05 |     0.00852495 |
| L3          |                    -0.00734865 | -0.0111623  | -0.00388973 | 7.72543e-06 | 0.000217434 |   6.18034e-05 |     0.0026092  |
| L4          |                    -0.00816525 | -0.0130896  | -0.00398505 | 5.77456e-05 | 0.000463256 |   0.000115491 |     0.00509582 |
| L5          |                    -0.0117521  | -0.0183855  | -0.0062983  | 1.19991e-05 | 0.000947216 |   6.18886e-05 |     0.00852495 |
| L6          |                    -0.0138944  | -0.021119   | -0.00749833 | 3.13291e-06 | 0.000838574 |   2.81962e-05 |     0.00838574 |
| L7          |                    -0.0224381  | -0.0333684  | -0.0126334  | 2.91955e-07 | 0.00109383  |   3.2115e-06  |     0.00852495 |
| L1_L2       |                     0.0175642  |  0.00996795 |  0.0265905  | 1.34525e-07 | 0.0019599   |   1.6143e-06  |     0.0117594  |
| L1_L3       |                     0.0161234  |  0.00867895 |  0.0251454  | 1.74525e-06 | 0.00502049  |   1.74525e-05 |     0.0251025  |
| L1_L4       |                     0.0164842  |  0.00829583 |  0.0261335  | 8.77761e-06 | 0.00817209  |   6.18034e-05 |     0.0326884  |
| L1_L5       |                     0.0145075  |  0.00682453 |  0.0233457  | 1.41279e-05 | 0.0106174   |   6.18886e-05 |     0.0326884  |
| L1_L6       |                     0.0129806  |  0.00614835 |  0.0209187  | 1.51168e-05 | 0.0104248   |   6.18886e-05 |     0.0326884  |
| L1_L7       |                     0.00795212 |  0.00333021 |  0.0140092  | 0.000211508 | 0.02296     |   0.000211508 |     0.0326884  |