from pathlib import Path
import sys

def analyze(root,output):
    root,output=Path(root),Path(output)
    sys.path.insert(0,str(Path(__file__).parent))
    from three_model_2021_analysis import three_model_analysis
    from warning_2021_analysis import analyze_warnings
    from focus_analysis import focus_analysis
    runs={m:output/n for m,n in [('Dynamic Panel FE','dynamic_panel'),('XGBoost','xgboost'),('Random Forest','random_forest')]}
    three_model_analysis({m:p/'predictions.npz' for m,p in runs.items()},output/'comparison')
    analyze_warnings(root,runs,output/'warning_evaluation')
    return focus_analysis(output)
