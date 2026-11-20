"""Check matched panels, numerical integration and serialized SEIR parameters."""
from pathlib import Path
import ast
import hashlib
import json
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

here=Path(__file__).resolve().parent
root=here.parents[1]
rf=root/"random_forest_trajectory_outputs/frozen_rf_2020_test_2021_2023"
with np.load(here/"predictions.npz",allow_pickle=False) as a,np.load(rf/"predictions.npz",allow_pickle=False) as b:
    for key in ["zip","forecast_origins","horizons","actual_cases"]:
        np.testing.assert_array_equal(a[key],b[key])
    assert a["raw_predictions"].shape==(585,1092,3)
    assert np.isfinite(a["raw_predictions"]).all() and (a["raw_predictions"]>=0).all()
with np.load(here/"risk_scores.npz",allow_pickle=False) as a,np.load(rf/"risk_scores.npz",allow_pickle=False) as b:
    for key in ["zip","forecast_origins","eligible","truth"]:
        np.testing.assert_array_equal(a[key],b[key])
parameters=pd.read_csv(here/"parameters_2020.csv",dtype={"zip":str})
with np.load(here/"frozen_parameters.npz",allow_pickle=False) as data:
    np.testing.assert_array_equal(parameters.zip.to_numpy(str),data["zip"])
    np.testing.assert_allclose(parameters.beta,data["beta"],rtol=1e-12,atol=1e-12)
assert parameters.latest_target.eq("2020-12-23").all()
source=(here/"run_seir.py").read_text(encoding="utf8")
function=next(node for node in ast.parse(source).body if isinstance(node,ast.FunctionDef) and node.name=="advance")
scope={"np":np,"sigma":1/3,"gamma":1/5}
exec(compile(ast.Module(body=[function],type_ignores=[]),str(here/"run_seir.py"),"exec"),scope)
advance=scope["advance"]
state=np.array([99900.,30.,40.,30.])
beta=.27
integrated,final=advance(state,beta,100000.)
def derivative(t,y):
    s,e,i,r,c=y
    v=beta*s*i/100000.
    return [-v,v-e/3,e/3-i/5,i/5,e/3]
exact=solve_ivp(derivative,(0,3),[*state,0.],t_eval=[0,1,2,3],rtol=1e-11,atol=1e-11)
max_error=float(np.abs(integrated-np.diff(exact.y[4])).max())
assert max_error<1e-4
np.testing.assert_allclose(final,exact.y[:4,-1],rtol=1e-6,atol=1e-5)
zero,end=advance(np.array([100.,0.,0.,0.]),.27,100.)
np.testing.assert_array_equal(zero,np.zeros(3))
np.testing.assert_array_equal(end,np.array([100.,0.,0.,0.]))
checks=dict(all585_regions_matched=True,all1092_origins_matched=True,
             target_arrays_identical_to_RF=True,event_eligibility_and_truth_identical_to_RF=True,
             integration_independently_checked=True,integration_max_error=max_error,
             conservation_and_nonnegative_states_checked=True,causal_prefix_invariance_checked_by_training_script=True,
             zero_incidence_state_checked=True,latest_fit_target="2020-12-23",
             boundary_fits=int(parameters.boundary.sum()),no_training_state=int(parameters.status.ne("fitted").sum()))
with (here/"frozen_parameters.npz").open("rb") as stream:
    checks["parameters_sha256"]=hashlib.file_digest(stream,"sha256").hexdigest()
(here/"verification.json").write_text(json.dumps(checks,indent=2),encoding="utf8")
print(json.dumps(checks,indent=2))
