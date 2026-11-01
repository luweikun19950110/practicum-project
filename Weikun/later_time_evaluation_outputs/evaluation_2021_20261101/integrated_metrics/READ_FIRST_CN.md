# 2021统一评价结果

先看 unified_evaluation_scorecard.csv：病例/trajectory、AP、事件检出率、预警正确比例、提前时间及每个horizon的Residual Moran’s I。

- Moran平均值：DP为0.0277/0.0348/0.0412，XGB为0.0223/0.0276/0.0328，RF为0.0206/0.0268/0.0318。
- 三个模型都仍有正的平均空间误差相关。RF平均值最低，仅为描述性比较，没有检验模型间Moran均值差异的显著性。
- 每个日期、horizon使用全部585个ZIP。不是只用8个ZIP：每个地区连接8个最近邻，取对称并集后部分地区邻居超过8个。
- 主结果q_BH_all_models对三个模型共3258次检验共同BH校正；各模型子文件的q_BH仅对该模型1086次检验校正，二者范围不同。
- mean_Moran_I没有一个总体p值。positive_BH_significant_share表示同时I>0且联合BH q<0.05的日期比例，不是预测准确率。
- 平均预警提前时间DP1.238天、XGB1.108天、RF1.200天，中位数均1天。仅针对被检出的事件，未检出的事件不进入均值。
- 提前时间参考第二个连续达标日的事件确认，不等于生物学爆发前预警。
- 不重训，不改变原预测，不查看2022—2023结果。地理ZIP–ZCTA对应仍是未经权威验证的编号匹配，置换推断为探索性诊断。

residual_moran_period_summary.csv包含全年、Delta时间段和12月的分horizon结果。
residual_moran_all_models.csv包含逐日I、p、两种BH范围。
residual_moran_comparison_2021.png可用于汇报。
