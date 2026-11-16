# Frozen Random Forest evaluation, 2021–2023

2020-12-23 checkpoints for horizons 1–3, held fixed throughout the evaluation. The original MA3 case-surge rule and risk threshold of 0 apply to 585 NJ ZIPs. The 1,092 daily forecast origins run from 2021-01-01 through 2023-12-28.

| Period | Calendar dates | Events detected | Correct warnings | AP | Lead days (mean / median) | Residual Moran’s I (D1 / D2 / D3) |
|---|---|---:|---:|---:|---:|---:|
| 2021–2023 overall | 2021-01-01 to 2023-12-31 | 83.1% (4,062/4,891) | 68.7% (4,062/5,915) | 0.487 | 1.21 / 1 | 0.032 / 0.032 / 0.032 |
| 2021 | 2021-01-01 to 2021-12-31 | 81.9% (2,255/2,752) | 74.7% (2,258/3,023) | 0.525 | 1.19 / 1 | 0.032 / 0.034 / 0.037 |
| 2022 | 2022-01-01 to 2022-12-31 | 84.5% (1,626/1,924) | 63.3% (1,625/2,569) | 0.472 | 1.24 / 1 | 0.030 / 0.027 / 0.030 |
| 2023 | 2023-01-01 to 2023-12-31 | 84.2% (181/215) | 55.4% (179/323) | 0.380 | 1.17 / 1 | 0.033 / 0.035 / 0.029 |
| Delta | 2021-07-01 to 2021-09-27 | 83.6% (652/780) | 71.5% (654/915) | 0.524 | 1.21 / 1 | 0.019 / 0.018 / 0.018 |
| Early Omicron (emergence through BA.1) | 2021-12-01 to 2022-03-19 | 82.5% (514/623) | 81.9% (497/607) | 0.542 | 1.16 / 1 | 0.062 / 0.067 / 0.075 |
| Omicron BA.1 predominance (sensitivity) | 2021-12-19 to 2022-03-19 | 82.2% (295/359) | 80.9% (296/366) | 0.516 | 1.14 / 1 | 0.057 / 0.058 / 0.061 |

- The pooled AP uses all eligible ZIP-day scores. Positive ZIP-day prevalence was 4.51%, 2.98%, and 0.30% in 2021, 2022, and 2023, respectively. Compare AP with these base rates when interpreting year-to-year changes.
- Forecasts and warning cooldown continue across internal year boundaries. Detection and lead are grouped by event confirmation date. Precision and AP are grouped by forecast origin. The 2021 row includes three year-end origins excluded from the standalone 2021 run.
- Residual Moran’s I is the mean of daily global I across the 585 ZIPs, separately for each horizon, with the original row-standardized geographic KNN8 matrix. Positive values indicate spatial clustering of similar residuals under that matrix. These are descriptive point estimates.
- Early Omicron extends the original December window through March 19, 2022 (109 days). The narrower BA.1 predominance window spans 91 days. These calendar windows use national surveillance context. [CDC MMWR](https://www.cdc.gov/mmwr/volumes/71/wr/mm7134a3.htm)
- Retrospective use of onset-date records assumes they were available at each forecast origin.
