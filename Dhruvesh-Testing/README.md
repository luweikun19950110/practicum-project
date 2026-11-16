# Dhruvesh Testing Workflow

This folder reproduces Weikun's chronological testing workflow in a readable sequence.

## Step 1: protocol and data check

`01_protocol_and_data_check.py` verifies the input panel and records the evaluation rules before any model is run.

The planned testing protocol is:

- Initial history: data available before the testing period
- Testing origins: January 1, 2021 through December 28, 2023
- Training window: the previous 60 calendar days
- Refit schedule: every 7 days
- Forecast horizon: direct predictions for 1, 2, and 3 days ahead
- Candidate features: the same 34-feature pool used by Weikun
- ZIP cohort: the 585 ZIP codes used in the model outputs
- Evaluation: count error, trajectory movement, outbreak detection, warning precision, and lead time

The models and evaluation outputs will be added only after this protocol check passes.

## Step 2: run the models

`02_run_testing_models.py` calls the reviewed implementations in Weikun's notebooks 24, 25, and 26. It runs them with `stage="evaluation"` and `evaluation_plan_frozen=True`, with outputs separated by model under `outputs/model_runs_2021_2023/`.

The runner does not create a single permanent estimator. It reproduces the rolling process: each algorithm refits on its current 60-day window every seven days and produces direct 1-, 2-, and 3-day forecasts.

## Step 3: compare validation and testing

`03_compare_validation_testing.py` combines Weikun's 2020 validation summaries with the new 2021-2023 testing summaries. It creates a CSV comparison table and a four-panel chart for trajectory MAE, RMSE, direction agreement, and two-step shape agreement.
