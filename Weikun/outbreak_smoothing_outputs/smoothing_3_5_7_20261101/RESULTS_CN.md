# Notebook29：3、5、7天均值对照

仅改变病例平滑窗口，并让基线使用相同窗口。为避免当前和基线共享原始病例，基线排除最近相同窗口长度的均值位置。这是配套定义的变化，不是仅替换当前均值而继续使用MA3基线。

仍用此前28个均值、+2SD、最近3天累计至少5例、连续2天确认、7天结束/冷却。预测范围始终未来3天，未重新训练，未使用2021—2023年。主方案仍为MA3。

## 事件数

 smoothing_days  events_2020  zips_with_events
              3         1838               496
              5         1755               492
              7         1625               491

## 9—12月

 smoothing_days            model  average_precision  positive_origin_share  events  event_recall  warning_precision  mean_lead_days  threshold
              3 Dynamic Panel FE           0.520026               0.059398    1131      0.786030           0.679144        1.304837          0
              3          XGBoost           0.542057               0.059398    1131      0.729443           0.836714        1.135758          0
              3    Random Forest           0.540082               0.059398    1131      0.793103           0.766667        1.230769          0
              5 Dynamic Panel FE           0.612649               0.057126    1082      0.824399           0.684049        1.511211          0
              5          XGBoost           0.635929               0.057126    1082      0.797597           0.842773        1.289687          0
              5    Random Forest           0.635364               0.057126    1082      0.826248           0.765411        1.434004          0
              7 Dynamic Panel FE           0.633050               0.053904     992      0.790323           0.664970        1.572704          0
              7          XGBoost           0.650027               0.053904     992      0.785282           0.835837        1.331194          0
              7    Random Forest           0.652963               0.053904     992      0.780242           0.741379        1.457364          0

## 至少提前2天与已出现异常条件

 smoothing_days            model lead_days  detected_events  eligible_events  recall_of_all_events  share_already_qualifying  recall_at_least_2_days
              3 Dynamic Panel FE   SUMMARY              889             1131              0.786030                  0.754781                0.201592
              3          XGBoost   SUMMARY              825             1131              0.729443                  0.888485                0.088417
              3    Random Forest   SUMMARY              897             1131              0.793103                  0.811594                0.159151
              5 Dynamic Panel FE   SUMMARY              892             1082              0.824399                  0.627803                0.326248
              5          XGBoost   SUMMARY              863             1082              0.797597                  0.800695                0.176525
              5    Random Forest   SUMMARY              894             1082              0.826248                  0.699105                0.270795
              7 Dynamic Panel FE   SUMMARY              784              992              0.790323                  0.586735                0.341734
              7          XGBoost   SUMMARY              779              992              0.785282                  0.771502                0.193548
              7    Random Forest   SUMMARY              774              992              0.780242                  0.673127                0.270161

先看01_smoothing_metrics.png，再看03同一ZIP事件定义图。不同窗口定义不同事件，不能只以最高AP挑定义。更长窗口有更多已观测历史成分、更平滑；分数改善不等于能更早捕捉真实疫情。MA5/7在未来日期的计算依然只用截至origin的真实值及本次3个预测值，不使用未来真实病例。
