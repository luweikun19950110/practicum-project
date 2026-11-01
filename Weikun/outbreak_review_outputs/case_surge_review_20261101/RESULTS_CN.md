# Notebook28：事件定义与预警稳定性

## 主方案提前量

                 lead_days  detected_events  share_of_detections  recall_of_all_events  already_qualifying  share_already_qualifying  recall_at_least_2_days  recall_before_current_qualification
model                                                                                                                                                                                            
Dynamic Panel FE   SUMMARY              889                  1.0              0.786030                 671                  0.754781                0.201592                             0.192750
XGBoost            SUMMARY              825                  1.0              0.729443                 733                  0.888485                0.088417                             0.081344
Random Forest      SUMMARY              897                  1.0              0.793103                 728                  0.811594                0.159151                             0.149425

## 事件定义敏感性

scenario  min_cases  sd_multiplier  events_2020  zips_with_events
 PRIMARY          5            2.0         1838               496
    MIN3          3            2.0         2548               538
   MIN10         10            2.0         1030               374
   SD1_5          5            1.5         1965               497
   SD2_5          5            2.5         1657               492

## 9—12月评估

scenario            model  average_precision  positive_origin_share  event_recall  warning_precision  threshold
 PRIMARY Dynamic Panel FE           0.520026               0.059398      0.786030           0.679144          0
 PRIMARY          XGBoost           0.542057               0.059398      0.729443           0.836714          0
 PRIMARY    Random Forest           0.540082               0.059398      0.793103           0.766667          0
    MIN3 Dynamic Panel FE           0.503618               0.084562      0.780850           0.674825          0
    MIN3          XGBoost           0.543063               0.084562      0.782873           0.867065          0
    MIN3    Random Forest           0.545267               0.084562      0.814565           0.805333          0
   MIN10 Dynamic Panel FE           0.559344               0.031127      0.761035           0.744048          0
   MIN10          XGBoost           0.551975               0.031127      0.704718           0.829749          0
   MIN10    Random Forest           0.543116               0.031127      0.773212           0.758209          0
   SD1_5 Dynamic Panel FE           0.541467               0.068169      0.805578           0.705460          0
   SD1_5          XGBoost           0.569269               0.068169      0.762100           0.839964          0
   SD1_5    Random Forest           0.562131               0.068169      0.794094           0.765823          0
   SD2_5 Dynamic Panel FE           0.501292               0.048816      0.801418           0.673191          0
   SD2_5          XGBoost           0.519105               0.048816      0.753799           0.836895          0
   SD2_5    Random Forest           0.514346               0.048816      0.798379           0.751192          0

主方案PRIMARY=三天至少5例、超过历史平均+2SD、连续两天确认。其它只改一个条件，未替换主定义。所有方案先4—8月校准，9—12月仅评估；未使用2021—2023年。AP随标签及正例率变化，不能跨定义挑最高AP证明方法更好。案例是按DP各结果类型MA3的中位数选取，展示三模型同一时段；它们用于解释而非证明典型性。

已满足异常条件后、确认前发出的预警与在当天尚未满足条件时发出的预警需区分。qualifying_at_alarm=False不能证明历史从未出现异常，不能等同真实疫情尚未发生。提前量只对检出事件有定义，>=2天召回率以全部事件为分母。所有现有统计仍为回顾性探索，未完成独立临床/公共卫生事件验证。
