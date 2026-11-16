"""Step 2: run Weikun's exact rolling Random Forest implementation for 2021-2023.

This wrapper keeps the model code in Weikun's reviewed notebooks, while making
the Dhruvesh workflow explicit and reproducible. It does not alter the model
algorithms or their settings.

The script is intentionally not run automatically. The rolling fits are
computationally expensive and require scikit-learn and scipy.
"""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "Weikun" / "rolling_trajectory_outputs" / "inputs" / "nj_daily_features.csv.gz"
COHORT = REPO_ROOT / "Weikun" / "fixed60_trajectory_outputs" / "fixed60_20261027" / "common_regions.csv"
OUTPUT_ROOT = Path(__file__).resolve().parent / "outputs" / "model_runs_2021_2023"

RANDOM_FOREST_NOTEBOOK = REPO_ROOT / "Weikun" / "26_random_forest_rolling_trajectory.ipynb"


def load_random_forest_with_resume(notebook_path: Path):
    """Load RF code with a safe resume around its saved weekly estimators."""

    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    source = next(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if "def run_random_forest60" in "".join(cell.get("source", []))
    )
    old = """            model=RandomForestRegressor(**params)
            model.fit(train_x,yt.ravel()) # no validation-based tuning or OOB selection
            pred[:,batch,hh]=model.predict(predict_x).reshape(len(ids),len(batch))
            joblib.dump(model,models/f'rf_{dates[fit].date()}_h{h}.joblib',compress=3)
"""
    new = """            model_path=models/f'rf_{dates[fit].date()}_h{h}.joblib'
            if model_path.exists():
                model=joblib.load(model_path)
                print('Resumed RF model:',dates[fit].date(),'h',h,flush=True)
            else:
                model=RandomForestRegressor(**params)
                model.fit(train_x,yt.ravel()) # no validation-based tuning or OOB selection
                joblib.dump(model,model_path,compress=3)
            pred[:,batch,hh]=model.predict(predict_x).reshape(len(ids),len(batch))
"""
    if old not in source:
        raise RuntimeError("Could not locate the expected Random Forest fit block.")
    source = source.replace(old, new, 1)
    namespace = {"__name__": "dhruvesh_testing_random_forest_resume"}
    exec(compile(source, str(notebook_path), "exec"), namespace)
    return namespace["run_random_forest60"]


def main() -> None:
    for path in [SOURCE, COHORT, RANDOM_FOREST_NOTEBOOK]:
        if not path.exists():
            raise FileNotFoundError(f"Required workflow file is missing: {path}")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    print("Testing protocol: 2021-01-01 through 2023-12-28")
    print("Training: rolling 60 calendar days; refit every 7 days")
    print("Forecasts: direct horizons 1, 2, and 3 days")
    print("Model settings are frozen before evaluation.")
    print(f"Outputs will be written under: {OUTPUT_ROOT}")

    print(f"\nPreparing random_forest from {RANDOM_FOREST_NOTEBOOK.name}")
    output = OUTPUT_ROOT / "random_forest"
    runner = load_random_forest_with_resume(RANDOM_FOREST_NOTEBOOK)
    runner(
        SOURCE,
        COHORT,
        output,
        stage="evaluation",
        evaluation_plan_frozen=True,
    )
    print(f"Completed random_forest: {output}")


if __name__ == "__main__":
    main()
