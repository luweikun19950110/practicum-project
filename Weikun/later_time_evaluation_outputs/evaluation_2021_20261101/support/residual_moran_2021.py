from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd

def residual_moran(archive, geography, output, permutations=999, seed=20261027):
    """Global residual Moran's I at each origin/horizon, no fitting."""
    archive,geography,output=Path(archive),Path(geography),Path(output)
    output.mkdir(parents=True,exist_ok=True)
    with np.load(archive,allow_pickle=False) as z:
        ids=z['zip'].astype(str);dates=pd.to_datetime(z['forecast_origins']);h=z['horizons']
        residual=np.maximum(z['raw_predictions'],0)-z['actual_cases']
    assert np.array_equal(h,[1,2,3]) and np.isfinite(residual).all()
    g=pd.read_csv(geography,sep='\t',dtype={'GEOID':str});g.columns=g.columns.str.strip()
    g['GEOID']=g.GEOID.str.zfill(5)
    assert not g.GEOID.duplicated().any()
    matched=g.set_index('GEOID').reindex(ids)
    coords=matched[['INTPTLAT','INTPTLONG']].apply(pd.to_numeric,errors='coerce').to_numpy()
    if not np.isfinite(coords).all():raise ValueError('Missing coordinates: do not silently drop regions')
    n,T,H=residual.shape;assert n==len(ids) and len(set(ids))==n
    # Haversine distance, internal representative points, not polygon centroids.
    lat,lon=np.deg2rad(coords).T
    dlat=lat[:,None]-lat;dlon=lon[:,None]-lon
    term=np.sin(dlat/2)**2+np.cos(lat[:,None])*np.cos(lat)*np.sin(dlon/2)**2
    distance=6371.0088*2*np.arcsin(np.sqrt(np.clip(term,0,1)))
    np.fill_diagonal(distance,np.inf)
    order=np.argsort(distance,axis=1,kind='stable') # stable tie-break = saved cohort order
    centered=residual.reshape(n,-1)-residual.reshape(n,-1).mean(axis=0)
    den=(centered**2).sum(axis=0);valid=den>1e-20;expected=-1/(n-1)
    def weights(k):
        binary=np.zeros((n,n),bool);binary[np.arange(n)[:,None],order[:,:k]]=True
        binary|=binary.T;np.fill_diagonal(binary,False)
        w=binary/binary.sum(axis=1)[:,None]
        assert np.allclose(w.sum(axis=1),1) and np.all(np.diag(w)==0)
        return w,binary
    def statistic(z,w):
        # Edge form avoids a new dependency on spatial-statistics packages.
        i,j=np.nonzero(w)
        return (n/w.sum())*np.einsum('e,ec,ec->c',w[i,j],z[i],z[j],optimize=False)/np.where(valid,den,np.nan)
    results=[];sensitivity=[]
    for k in [4,8,12]:
        w,binary=weights(k);observed=statistic(centered,w)
        sensitivity.append(observed)
        if k!=8:continue
        ei,ej=np.nonzero(w);ew=w[ei,ej]
        pd.DataFrame(dict(origin_zip=ids[ei],neighbor_zip=ids[ej],weight=ew,distance_km=distance[ei,ej])).to_csv(output/'spatial_weights_knn8.csv',index=False)
        pd.DataFrame(dict(zip=ids,latitude=coords[:,0],longitude=coords[:,1],neighbor_degree=binary.sum(axis=1),geography_status='exact_identifier_match_unvalidated')).to_csv(output/'geography_alignment.csv',index=False)
        rng=np.random.default_rng(seed);extreme=np.zeros(centered.shape[1],dtype=int)
        # One permutation of region labels for the whole residual cube preserves
        # each region's temporal/horizon profile. Tests remain marginal by date/h.
        for b in range(permutations):
            perm=rng.permutation(n)
            sim=statistic(centered[perm],w)
            extreme+=np.abs(sim-expected)>=np.abs(observed-expected)-1e-14
            if (b+1)%100==0:print(f'Moran permutations: {b+1}/{permutations}',flush=True)
        p=(extreme+1)/(permutations+1);p[~valid]=np.nan
        # BH across all valid origin-horizon tests in THIS stage/run.
        q=np.full_like(p,np.nan);idx=np.flatnonzero(valid);ranked=idx[np.argsort(p[idx])]
        q[ranked]=np.minimum(1,np.minimum.accumulate((p[ranked]*len(idx)/np.arange(1,len(idx)+1))[::-1])[::-1])
        for t,date in enumerate(dates):
            for hh,horizon in enumerate(h):
                c=t*H+hh
                results.append(dict(forecast_origin=str(date.date()),target_date=str((date+pd.Timedelta(days=int(horizon))).date()),horizon=int(horizon),regions=n,Moran_I=observed[c],expected_I=expected,p_permutation_two_sided=p[c],q_BH=q[c],residual_variance=float(den[c]/n),status='ok' if valid[c] else 'undefined_constant_residuals'))
        # Independent dense-form formula check on first valid residual vector.
        c=int(idx[0]);vec=centered[:,c]
        assert np.isclose(observed[c],n/w.sum()*(vec@w@vec)/(vec@vec))
        assert np.allclose(statistic(centered+0,w),statistic(-centered,w),equal_nan=True)
    table=pd.DataFrame(results);table.to_csv(output/'residual_moran_by_origin_horizon.csv',index=False)
    sens=[]
    for k,values in zip([4,8,12],sensitivity):
        for hh,horizon in enumerate(h):
            v=values.reshape(T,H)[:,hh];sens.append(dict(k=k,horizon=int(horizon),mean_Moran_I=float(np.nanmean(v)),median_Moran_I=float(np.nanmedian(v)),positive_I_share=float(np.mean(v>0)),inference='Descriptive sensitivity only; no p-values for alternative k'))
    pd.DataFrame(sens).to_csv(output/'weight_sensitivity.csv',index=False)
    summary=[]
    for scope,labels in [('overall',np.repeat('all',len(table))),('quarter',pd.to_datetime(table.forecast_origin).dt.to_period('Q').astype(str).to_numpy()),('year',pd.to_datetime(table.forecast_origin).dt.year.astype(str).to_numpy())]:
        for label in np.unique(labels):
            for horizon in h:
                d=table.loc[(labels==label)&table.horizon.eq(horizon)&table.status.eq('ok')]
                summary.append(dict(scope=scope,period=label,horizon=int(horizon),valid_tests=len(d),mean_Moran_I=d.Moran_I.mean(),median_Moran_I=d.Moran_I.median(),raw_p_below_05_share=d.p_permutation_two_sided.lt(.05).mean(),BH_q_below_05_share=d.q_BH.lt(.05).mean(),positive_I_and_BH_q_below_05_share=(d.Moran_I.gt(0)&d.q_BH.lt(.05)).mean()))
    summary=pd.DataFrame(summary);summary.to_csv(output/'residual_moran_summary.csv',index=False)
    protocol=dict(metric="Global residual Moran's I",residual='max(raw_prediction,0)-actual; sign convention does not change I',alignment='At each forecast origin and horizon, compare585 ZIP residuals; never flatten region-days or sum across regions',spatial_weights='Symmetric union of8 nearest neighbors using haversine distances between2021 Gazetteer internal points; zero diagonal, row-standardized after symmetrizing. Weights after normalization are not necessarily symmetric.',primary_k=8,sensitivity_k=[4,12],distance='Great-circle km; internal points, not polygon centroid or adjacency',mapping='Exact postal ZIP identifier to ZCTA GEOID remains unvalidated; diagnostic conditional on this mapping',null='Exchangeability of residual labels across regions conditional on fitted predictions; heteroskedastic count residuals may violate it. Exploratory diagnostic, not a formal spatial-regression specification test.',permutations=permutations,seed=seed,p_value='(1+count(|I_perm-EI|>=|I_obs-EI|))/(B+1), two-sided centered atEI=-1/(n-1)',multiple_testing='Benjamini-Hochberg across all valid dates x horizons in this stage; overlapping dates/spatial dependence mean FDR control is not guaranteed. No pooled overall significance claim.',constant_residual_policy='Undefined I and p, retained as NA',parameter_fitting='None. No prediction or feature changes.',inference='Positive I indicates similar signed residuals cluster under selected W. Nonsignificance is not evidence that all spatial patterns are explained.',reference='https://pysal.org/esda/stable/user-guide/global_morans_i.html',archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),geography_sha256=hashlib.sha256(geography.read_bytes()).hexdigest())
    (output/'residual_moran_definition.json').write_text(json.dumps(protocol,indent=2),encoding='utf8')
    (output/'verification.json').write_text(json.dumps(dict(all585_coordinates_present=True,weights_zero_diagonal=True,weights_rows_sum_to_one=True,dense_formula_crosscheck=True,sign_invariance_verified=True,predictions_unchanged=True,tests=len(table)),indent=2))
    report='# Residual spatial autocorrelation: rolling60 weekly model\n\n'+summary.loc[summary.scope.eq('overall')].to_string(index=False)+'\n\nMoran I is computed separately for each origin and horizon. A positive value suggests clustering of similarly signed forecast errors under the chosen geographic weights. Summary means are descriptive; they do not have a pooled p-value. Permutation p-values and BH q-values are exploratory, conditional on the fitted model, residual exchangeability, and unvalidated ZIP-ZCTA identifiers. Count residual magnitudes vary by region; this can affect the interpretation. Nonsignificance does not prove spatial adequacy. K4/K12 are sensitivity checks, not selected by results. No model refit.\n'
    (output/'RESULTS.md').write_text(report,encoding='utf8')
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,axes=plt.subplots(3,1,figsize=(12,8),sharex=True)
        for ax,horizon in zip(axes,h):
            d=table.loc[table.horizon.eq(horizon)];x=pd.to_datetime(d.forecast_origin)
            ax.plot(x,d.Moran_I,color='#2563eb',lw=1,label="Residual Moran's I")
            sig=d.q_BH.lt(.05);ax.scatter(x[sig],d.loc[sig,'Moran_I'],s=9,color='#d94841',label='BH q <0.05 (exploratory)')
            ax.axhline(expected,color='#64748b',ls='--',lw=1,label='Randomization expectation')
            ax.set(ylabel="Moran's I",title=f'{horizon}-day ahead');ax.grid(alpha=.2)
        axes[0].legend(frameon=False,ncol=3,fontsize=8);axes[-1].set_xlabel('Forecast origin')
        fig.suptitle('Residual spatial clustering |8-neighbor geographic weights |2021 temporal evaluation')
        fig.tight_layout();fig.savefig(output/'residual_moran_by_origin.png',dpi=220);plt.close(fig)
    except ImportError:print('Optional plot requires matplotlib')
    return table,summary
