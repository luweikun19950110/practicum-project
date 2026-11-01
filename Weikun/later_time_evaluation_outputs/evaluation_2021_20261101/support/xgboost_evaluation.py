from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
GROUPS={
 'core_history':['cases_today','cases_lag_1','cases_lag_7','cases_lag_14'],
 'rolling_level':['cases_mean_7d','cases_mean_14d'],
 'volatility':['case_std_7d','case_std_14d'],
 'dynamics':['case_acceleration','case_jerk'],
 'local_rates':['case_rate_today_per_100k','case_rate_7d_per_100k','case_rate_14d_per_100k'],
 'sparse_history':['days_since_last_observed_case_censored','no_previous_observed_case'],
 'pressure':['nj_covid_pressure_7d','nj_covid_pressure_14d'],
 'month':[f'target_month_{k}' for k in range(2,13)],
 'weekday':[f'target_weekday_{k}' for k in range(2,8)]}

def run_xgboost60(source, cohort_file, output, stage='development', evaluation_plan_frozen=False):
    if stage not in ['development','evaluation']: raise ValueError('Unknown stage')
    if stage=='evaluation' and not evaluation_plan_frozen:
        raise ValueError('Freeze model/features/hyperparameters before running subsequent evaluation.')
    from xgboost import XGBRegressor
    import xgboost, platform
    params=dict(objective='reg:squarederror',tree_method='hist',n_estimators=200,
                max_depth=3,learning_rate=0.05,min_child_weight=20,subsample=0.8,
                colsample_bytree=1.0,reg_lambda=5.0,reg_alpha=0.0,max_bin=128,
                enable_categorical=True,max_cat_to_onehot=4,max_cat_threshold=64,
                random_state=20261027,n_jobs=4)
    source,output=Path(source),Path(output)
    if hashlib.sha256(source.read_bytes()).hexdigest()!='d18a70fe1b1efa550c0bc3e28edeca576f432996dfc85d67106c70069f79a9e4':raise ValueError('Feature input changed from frozen plan; use a new run directory.')
    output.mkdir(parents=True,exist_ok=True)
    with source.open('rb') as f:
        if f.read(7)==b'version': raise ValueError('Input is a Git LFS pointer. Download the real gzip data first.')
    models=output/'models';models.mkdir(exist_ok=True)
    importance=[]
    ids=pd.read_csv(cohort_file,dtype={'zip':str})['zip'].to_numpy(dtype='U5')
    numeric=sum([v for k,v in GROUPS.items() if k not in ['month','weekday','sparse_history']],[])
    cols=['zip','date','pressure_definition']+numeric
    frame=pd.read_csv(source,usecols=cols,dtype={'zip':str},parse_dates=['date'])
    dates=pd.date_range('2020-03-01','2021-12-31')
    frame=frame.loc[frame.zip.isin(ids)&frame.date.isin(dates)]
    assert len(ids)==585 and not frame.duplicated(['zip','date']).any()
    assert frame.pressure_definition.eq('valid_population_nj_origins_renormalized_v2').all()
    arrays={c:frame.pivot(index='zip',columns='date',values=c).reindex(index=ids,columns=dates).to_numpy(float) for c in numeric}
    counts=arrays['cases_today'];features=sum(GROUPS.values(),[])
    assert np.isfinite(counts).all() and (counts>=0).all()
    # End-of-day origins: initial fit includes mature targets through April29.
    # A 60-day interval includes14 warmup days, leaving45/44/43 pairs per ZIP.
    first=int(dates.get_loc('2020-04-29'))
    origin_start='2020-04-30' if stage=='development' else '2021-01-01'
    origin_end='2020-12-28' if stage=='development' else '2021-12-28'
    origins=np.flatnonzero((dates>=origin_start)&(dates<=origin_end))
    actual=np.stack([counts[:,origins+h] for h in (1,2,3)],axis=2)
    pred=np.full_like(actual,np.nan);logs=[];coefficients=[];omitted=[]
    # Anchor weekly schedule to April29, keep same schedule across stage boundaries.
    fit_indices=np.unique(first+7*((origins-first)//7))
    checkpoints=output/'checkpoints';checkpoints.mkdir(exist_ok=True)
    for fit in fit_indices:
        lo=fit-59
        batch=np.flatnonzero((origins>=fit)&(origins<fit+7))
        assert lo>=0 and len(batch)>0
        checkpoint=checkpoints/f'fit_{dates[fit].date()}.npz'
        if checkpoint.exists():
            with np.load(checkpoint,allow_pickle=False) as ck:
                assert np.array_equal(ck['origins'],dates[origins[batch]].to_numpy())
                pred[:,batch,:]=ck['predictions']
                saved=json.loads(str(ck['diagnostics']))
                logs=saved['logs'];coefficients=saved['coefficients'];omitted=saved['omitted']
                if 'importance' in saved:importance=saved['importance']
            print('Resumed fit:',dates[fit].date(),flush=True)
            continue

        last=np.full(len(ids),-1,dtype=int)
        gap=np.empty((len(ids),len(dates)));never=np.empty_like(gap)
        gap[:]=np.nan;never[:]=np.nan
        for t in range(lo,max(fit,int(origins[batch[-1]]))+1):
            last=np.where(counts[:,t]>0,t,last)
            never[:,t]=(last<0);gap[:,t]=np.where(last>=0,t-last,t-lo+1)
        arrays['no_previous_observed_case']=never
        arrays['days_since_last_observed_case_censored']=gap
        for hh,h in enumerate((1,2,3)):
            train=np.arange(lo+14,fit-h+1)
            target=dates+pd.Timedelta(days=h)
            for k in range(2,13): arrays[f'target_month_{k}']=np.broadcast_to((target.month==k).astype(float),counts.shape)
            for k in range(2,8): arrays[f'target_weekday_{k}']=np.broadcast_to((target.dayofweek==k-1).astype(float),counts.shape)
            xt=np.stack([arrays[f][:,train] for f in features],axis=2)
            xp=np.stack([arrays[f][:,origins[batch]] for f in features],axis=2)
            yt=counts[:,train+h]
            assert np.isfinite(xt).all() and np.isfinite(xp).all()
            assert train[0]-14>=lo and train[-1]+h<=fit and np.all(origins[batch]+h>fit)
            # Same34 epidemiologic/calendar columns, plus native categorical ZIP
            # to represent identity without treating postal numbers as ordered.
            def design(values):
                d=pd.DataFrame(values.reshape(-1,len(features)),columns=features)
                d['region_id']=pd.Categorical(np.repeat(ids,values.shape[1]),categories=ids)
                return d
            train_x,predict_x=design(xt),design(xp)
            model=XGBRegressor(**params)
            model.fit(train_x,yt.ravel()) # no validation scores / early stopping
            pred[:,batch,hh]=model.predict(predict_x).reshape(len(ids),len(batch))
            # Reproducible checkpoints store predictions and diagnostics; no estimator dump.
            for feature,gain in model.get_booster().get_score(importance_type='gain').items():
                importance.append(dict(fit_date=str(dates[fit].date()),horizon=h,feature=feature,training_split_gain=float(gain)))
            logs.append(dict(fit_date=str(dates[fit].date()),window_start=str(dates[lo].date()),window_end=str(dates[fit].date()),window_calendar_days=60,horizon=h,training_origin_start=str(dates[train[0]].date()),training_origin_end=str(dates[train[-1]].date()),latest_training_target=str(dates[train[-1]+h].date()),usable_training_origins=len(train),forecast_origin_start=str(dates[origins[batch[0]]].date()),forecast_origin_end=str(dates[origins[batch[-1]]].date()),candidate_columns=len(features),model_input_columns=len(features)+1,estimator="XGBoost",boosting_rounds=params["n_estimators"]))
        saved=dict(logs=logs,coefficients=coefficients,omitted=omitted)
        if 'importance' in locals():saved['importance']=importance
        temporary=checkpoint.with_suffix('.tmp.npz')
        np.savez_compressed(temporary,predictions=pred[:,batch,:],origins=dates[origins[batch]].to_numpy(),diagnostics=json.dumps(saved))
        temporary.replace(checkpoint)
        print('Completed fit:',dates[fit].date(),flush=True)
    assert np.isfinite(pred).all()
    np.savez_compressed(output/'predictions.npz',raw_predictions=pred,actual_cases=actual,zip=ids,forecast_origins=dates[origins].to_numpy(),horizons=[1,2,3])
    pd.DataFrame(logs).to_csv(output/'training_timing.csv',index=False)
    pd.DataFrame(importance).to_csv(output/'training_split_gain.csv',index=False)
    (output/'model_parameters.json').write_text(json.dumps(dict(parameters=params,xgboost_version=xgboost.__version__,python_version=platform.python_version(),tuning='None; fixed before viewing this run',region_identity='Native categorical ZIP, same region identity available to FE benchmark. Not numeric postal ordering.',static_attributes='Not added; matched34-column candidate information set'),indent=2),encoding='utf8')
    pd.DataFrame([(g,f) for g,fs in GROUPS.items() for f in fs],columns=['group','feature']).to_csv(output/'candidate_features.csv',index=False)
    p=np.maximum(pred,0);err=p-actual;da=np.diff(actual,axis=2);dp=np.diff(p,axis=2)
    aa=np.diff(actual,n=2,axis=2)[...,0];ap=np.diff(p,n=2,axis=2)[...,0]
    daily=pd.DataFrame(dict(forecast_origin=dates[origins],trajectory_MAE=np.abs(err).mean(axis=(0,2)),MSE=(err**2).mean(axis=(0,2)),mean_bias=err.mean(axis=(0,2)),slope_MAE=np.abs((p[...,2]-p[...,0]-actual[...,2]+actual[...,0])/2).mean(axis=0),direction_agreement=(np.sign(p[...,2]-p[...,0])==np.sign(actual[...,2]-actual[...,0])).mean(axis=0),two_step_shape_agreement=(np.sign(dp)==np.sign(da)).all(axis=2).mean(axis=0),change_MAE=np.abs(dp-da).mean(axis=(0,2)),acceleration_MAE=np.abs(ap-aa).mean(axis=0),all_zero_actual_path_share=(actual==0).all(axis=2).mean(axis=0)))
    daily.to_csv(output/'scores_by_forecast_origin.csv',index=False)
    rows=[]
    periods={'overall':np.repeat('all',len(daily)),'year':daily.forecast_origin.dt.year.astype(str).to_numpy(),'quarter':daily.forecast_origin.dt.to_period('Q').astype(str).to_numpy()}
    for scope,values in periods.items():
        for label in np.unique(values):
            d=daily.loc[values==label];r=dict(scope=scope,period=label,forecast_origins=len(d),regions=len(ids),paths=len(d)*len(ids),RMSE=float(np.sqrt(d.MSE.mean())))
            r.update({col:float(d[col].mean()) for col in daily.columns if col not in ['forecast_origin','MSE']});rows.append(r)
    scores=pd.DataFrame(rows);scores.to_csv(output/'trajectory_scores_by_period.csv',index=False)
    protocol=dict(stage=stage,initial_training=['2020-03-01','2020-04-29'],development=['2020-04-30','2020-12-31'],evaluation=['2021-01-01','2021-12-31'],window_calendar_days=60,retrain_every_days=7,first_fit='2020-04-29 end of day',prediction='Daily end-of-day origin predicts t+1,t+2,t+3; raw onset counts',boundaries='All3 targets remain within stage; development origins end Dec28 2020, evaluation origins end Dec28 2023. Last3 origins of evaluation2021 omitted so all targets remain in2021.',maturity='Every training target <=fit date; forecast targets >forecast origin>=fit date',feature_policy='Same34 candidates including bothPressure plus native categorical ZIP. No new static attributes, no feature selection. Training-only tree splits; no early stopping on validation.',warmup='14 days inside each60-day window,45/44/43 usable training origins per ZIP per horizon; sparse-history state reset at window start',inputs='Updated daily through origin; coefficients updated only on anchored7-day schedule',evaluation_policy='Algorithm and settings frozen before subsequent-period run. Past realized evaluation labels may enter future scheduled fits; no retrospective prediction changes or manual tuning.',limitation='Exploratory retrospective time evaluation;2021-2023 previously inspected. Onset-date availability assumed, reporting delays not modeled.',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf8')
    (output/'verification.json').write_text(json.dumps(dict(all_training_targets_mature=True,window_exactly60=True,forecast_targets_after_fit=True,all_predictions_finite=True,all34_candidates_considered=True,per_zip_metrics_produced=False,no_validation_early_stopping=True),indent=2))
    (output/'RESULTS.md').write_text('# XGBoost rolling60-day trajectory evaluation\n\n'+scores.to_string(index=False)+'\n\n60 calendar days,14 within-window warmup days;45/44/43 supervised origins per horizon per ZIP. Weekly re-estimation, daily predictor updates. No Pressure ablation or seasonal naive. Primary score is ZIP-path trajectory MAE; change/acceleration and direction/shape are supplementary. Scores are retrospective and exploratory. See protocol.json and training_timing.csv for information boundaries. No coefficient p-values or causal feature interpretations are asserted for this XGBoost estimator.\n',encoding='utf8')
    return scores, output

if __name__=='__main__':
    import sys
    root=Path(sys.argv[1]);destination=Path(sys.argv[2])
    run_xgboost60(root/'rolling_trajectory_outputs/inputs/nj_daily_features.csv.gz',root/'fixed60_trajectory_outputs/fixed60_20261027/common_regions.csv',destination,stage='evaluation',evaluation_plan_frozen=True)
