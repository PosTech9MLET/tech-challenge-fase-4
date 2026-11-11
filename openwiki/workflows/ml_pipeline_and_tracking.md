---
type: workflow
title: ML Pipeline, DVC Stages & Experiment Tracking
description: How the reproducible DVC pipeline (validate, prepare_data, train, simulate_drift, detect_drift, score_impact) turns the Home Credit CSV into a baseline XGBoost credit-scoring model, how features are built, what MLflow records, and which model and metrics files each stage produces.
tags: [ml-pipeline, dvc, mlflow, experiment-tracking, feature-engineering, xgboost, model-artifacts, model-card]
verified:
  - by: openwiki/0.7.2
    at: 2026-11-09T02:03:21.311Z
sources:
  - id: openwiki-source-5f5b95b3d6a215fa02ceb945
    resource: repo://.env.example
  - id: openwiki-source-269c1f28e5de4ed38ee00d6b
    resource: repo://data/raw/application_train.csv.dvc
  - id: openwiki-source-45f7d2a4e749798ed3a41141
    resource: repo://docs/model_card.md
  - id: openwiki-source-4935f5c0efb229189fbcdd99
    resource: repo://dvc.lock
  - id: openwiki-source-cfa03d5d7ac7270f0bb1bf28
    resource: repo://dvc.yaml
  - id: openwiki-source-11ba73b3ffd2cb972063e78b
    resource: repo://models/baseline_metrics.json
  - id: openwiki-source-05ccef8d4cf1698187f20464
    resource: repo://pyproject.toml
  - id: openwiki-source-b5672e8c6fe51c1d4051fd28
    resource: repo://scripts/analyze_score_impact.py
  - id: openwiki-source-6d5d6449122bc859c0c552a8
    resource: repo://src/data/contracts.py
  - id: openwiki-source-214118d922fe1ca5c2383b44
    resource: repo://src/data/home_credit.py
  - id: openwiki-source-cd5f91b2d1b7100bb20e38ce
    resource: repo://src/features/build.py
  - id: openwiki-source-11b9d806fcc6dd6e7747ed87
    resource: repo://src/main.py
  - id: openwiki-source-bef30f0ca72ee4bce1ca9e59
    resource: repo://src/models/baseline.py
  - id: openwiki-source-0b481e6de0f6fd0862204a36
    resource: repo://src/pipelines/prepare_data.py
  - id: openwiki-source-fcfbfa02b8c3ddf398465b4a
    resource: repo://src/training/train.py
  - id: openwiki-source-f12fdb76c2f98bd11af25d76
    resource: repo://src/utils/config.py
  - id: openwiki-source-f9ca9cdda3a0ae93b2ab0055
    resource: repo://tests/unit/test_baseline.py
  - id: openwiki-source-85682b837c4bbfc1b73890d0
    resource: repo://tests/unit/test_features.py
  - id: openwiki-source-e9644626d37bc03f84bcb73f
    resource: repo://tests/unit/test_prepare_data.py
generated: { by: "openwiki/0.7.2", at: "2026-11-09T02:03:21.311Z" }
---

# ML Pipeline, DVC Stages & Experiment Tracking

The project trains a baseline credit-scoring model (default probability, "PD") on the Kaggle Home Credit `application_train.csv`. The workflow is declared as a DVC pipeline in [`dvc.yaml`](../../dvc.yaml) and run with `uv run dvc repro`. Each stage shells out to a Python module through `uv run python -m ...`. The first three stages (`validate`, `prepare_data`, `train`) build the model. The last three (`simulate_drift`, `detect_drift`, `score_impact`) are covered in [Drift Monitoring & Score Impact](drift_monitoring_and_score_impact.md) and are only summarised here.

## DVC stage dependency graph

```mermaid
flowchart TD
    RAW["data/raw/application_train.csv (DVC-tracked)"]
    VAL["validate"]
    PREP["prepare_data"]
    REF["reference.parquet"]
    PROD["production_base.parquet"]
    TRAIN["train"]
    MODEL["models/baseline.joblib"]
    METRICS["models/baseline_metrics.json"]
    SIM["simulate_drift"]
    DRIFTED["production_drift.parquet"]
    DET["detect_drift"]
    REPORTS["reports/drift_*.html and drift_*.json"]
    ALERTS["reports/drift_alerts.json"]
    SCORE["score_impact"]
    IMPACT["reports/score_impact.json"]

    RAW --> VAL
    RAW --> PREP
    PREP --> REF
    PREP --> PROD
    REF --> TRAIN
    TRAIN --> MODEL
    TRAIN --> METRICS
    PROD --> SIM
    SIM --> DRIFTED
    REF --> DET
    PROD --> DET
    DRIFTED --> DET
    DET --> REPORTS
    DET --> ALERTS
    PROD --> SCORE
    DRIFTED --> SCORE
    MODEL --> SCORE
    METRICS --> SCORE
    SCORE --> IMPACT
```
*Figure 1: Data and artifact dependencies between DVC stages, as declared in `dvc.yaml`.*

| Stage | Command module | Key outputs |
| :--- | :--- | :--- |
| `validate` | `scripts.validate_home_credit` | none (acts as a gate and has no downstream artifact edge) |
| `prepare_data` | `src.pipelines.prepare_data` | `data/processed/reference.parquet`, `data/processed/production_base.parquet` |
| `train` | `src.training.train` | `models/baseline.joblib`, `models/baseline_metrics.json` (metrics) |
| `simulate_drift` | `scripts.simulate_home_credit_drift` | `data/processed/production_drift.parquet` |
| `detect_drift` | `scripts.run_drift` | `reports/drift_baseline.html`, `reports/drift_simulated.html`, `reports/drift_baseline.json`, `reports/drift_simulated.json`, `reports/drift_alerts.json` |
| `score_impact` | `scripts.analyze_score_impact` | `reports/score_impact.json` |

Operational notes:

- **Stage invalidation is dependency-driven.** `train` depends on `src/features`, `src/models` and `src/training` as whole directories, plus `reference.parquet`. Editing any file in those packages re-runs training and, transitively, `score_impact`. `validate`, `prepare_data` and `simulate_drift` all depend on `src/data`.
- **`cache: false` outputs.** Small, human-diffable JSON files are declared with `cache: false`, so DVC leaves them out of its cache and Git can track them directly. These are `models/baseline_metrics.json` (a `metrics` entry of `train`), `reports/drift_baseline.json` and `reports/drift_simulated.json` (plain `outs` of `detect_drift`), and `reports/drift_alerts.json` and `reports/score_impact.json` (`metrics` entries). Parquet files, `baseline.joblib` and the HTML drift reports use the default cached behaviour.
- **Raw data is pinned by hash.** [`data/raw/application_train.csv.dvc`](../../data/raw/application_train.csv.dvc) records the md5 of the raw CSV. [`dvc.lock`](../../dvc.lock) records md5 and size for every dependency and output of every stage, which makes a rerun with unchanged inputs a no-op.
- **`score_impact` also depends on `baseline_metrics.json`.** It needs the saved decision threshold as well as the model file.

## Data preparation (`prepare_data`)

[`src/pipelines/prepare_data.py`](../../src/pipelines/prepare_data.py) implements `run(production_size=0.3)`:

1. `load_application_train()` in `src/data/home_credit.py` reads only the `RAW_COLUMNS` from `data/raw/application_train.csv`. It raises `FileNotFoundError` with the Kaggle download URL if the file is missing.
2. `validate_training_batch()` applies the Pandera training contract (see [Data Contracts](../concepts/data_contracts.md)). The check is lazy, so all violations are collected. A violation raises `SchemaErrors` and **nothing is written**, which a unit test asserts by checking that `data/processed` does not exist.
3. `split_reference_production()` makes a stratified split on `TARGET` with `settings.random_seed`. 70% becomes the **reference** set (used for training and as the drift baseline) and 30% becomes the **production** set. Both keep their original row order.
4. Both files are written as Parquet under `data/processed/`.

The persisted columns are raw. Feature engineering is deliberately not applied at this point. It lives inside the model pipeline, so simulated changes to raw production columns such as income flow into the derived ratios at scoring time.

The standalone `validate` stage runs [`scripts/validate_home_credit.py`](../../scripts/validate_home_credit.py), which loads only the contract columns and calls `validate_training_batch()`. It has no `outs`, so a validation failure fails `dvc repro`, but no later stage reads anything from it.

## Feature engineering

[`src/features/build.py`](../../src/features/build.py) holds the column lists and `build_features()`:

- `CATEGORICAL` has 8 columns, such as `NAME_INCOME_TYPE` and `OCCUPATION_TYPE`. `NUMERIC_RAW` has 15 columns, including the `EXT_SOURCE_*` scores and the `AMT_*` and `DAYS_*` columns.
- `DERIVED` has five columns: `AGE_YEARS` (from `DAYS_BIRTH`), `CREDIT_INCOME_RATIO`, `ANNUITY_INCOME_RATIO`, `CREDIT_TERM` and `EMPLOYED_RATIO`.
- `MODEL_FEATURES = CATEGORICAL + NUMERIC` is the exact output schema of `build_features()`.
- `build_features()` is a **pure, stateless** function. It replaces the `DAYS_EMPLOYED` sentinel `365243` with `NaN`, computes the derived columns, and converts `±inf` in the derived columns to `NaN`. This makes division by zero safe. It is therefore safe to apply identically at training and inference.
- `CODE_GENDER` (`GENDER`), `SK_ID_CURR` and `TARGET` are not model features. Gender is kept in the raw data only for bias analysis, and a test asserts it never reaches the booster.

## Baseline model

[`src/models/baseline.py`](../../src/models/baseline.py) builds one scikit-learn `Pipeline` that accepts the **raw** DataFrame:

1. `FunctionTransformer(build_features)`.
2. A `ColumnTransformer` with an `OrdinalEncoder` for categoricals and passthrough for numerics. Unknown or missing categories become `NaN` (`handle_unknown="use_encoded_value"`), so unseen production categories do not break scoring. XGBoost handles `NaN` natively.
3. `XGBClassifier(**XGB_PARAMS, random_state=seed)`, with `n_estimators=400`, `max_depth=4`, `learning_rate=0.05`, `subsample=0.8`, `colsample_bytree=0.8`, `min_child_weight=5` and `eval_metric="auc"`.

The module also owns the persistence and inference helpers used by later stages:

- `save_model(pipeline, metrics)` writes `models/baseline.joblib` and `models/baseline_metrics.json` under `settings.models_dir`.
- `load_model()` and `load_threshold()` read them back. The decision threshold is the `threshold` key in the metrics file.
- `score(raw, model=None)` returns `predict_proba[:, 1]` as a Series named `score`, indexed like the input. A `TARGET` column is ignored if present.

## Training and evaluation (`train`)

[`src/training/train.py`](../../src/training/train.py) `main()`:

1. Reads `data/processed/reference.parquet` and re-validates it with `validate_training_batch()`.
2. Calls `train()`, which holds out a stratified 20% validation split (seeded with `settings.random_seed`), fits the pipeline on the other 80%, and scores the held-out part.
3. Computes `evaluate()`: `auc`, `ks` (max of TPR minus FPR), `pr_auc`, `threshold` and `f1`. The threshold is the score that maximises F1 on the precision/recall curve, chosen because the positive class is rare.
4. Computes fairness metrics with `auc_by_group()`: AUC per gender (`F` and `M` only) and per age band (`lt30`, `30_44`, `45_59`, `60_plus`). Groups with fewer than `MIN_GROUP_POSITIVES = 30` positives, or with only one class, are skipped. Keys look like `auc_gender_F` and `auc_age_lt30`.

[`models/baseline_metrics.json`](../../models/baseline_metrics.json) holds only the five overall metrics (`auc`, `ks`, `pr_auc`, `threshold`, `f1`). In the committed snapshot the AUC is about 0.766 and the threshold about 0.141. The per-group fairness metrics go to MLflow only, not to this file.

## MLflow experiment tracking

Inside `main()`, MLflow is configured and used like this:

- `mlflow.set_tracking_uri(settings.mlflow_tracking_uri)`. The default is `sqlite:///<repo>/mlflow.db`, and `.env.example` uses `sqlite:///mlflow.db`. `mlflow.db` is git-ignored and docker-ignored.
- `mlflow.set_experiment("credit-scoring-baseline")` and a run named `baseline-xgboost`.
- `log_params`: all `XGB_PARAMS` plus `n_rows`.
- `log_metrics`: the overall metrics merged with the fairness metrics.
- `mlflow.sklearn.log_model(pipeline, name="model", serialization_format="cloudpickle")`.

MLflow's copy of the model is a tracked run artifact. The file that downstream stages actually load is the separate `models/baseline.joblib` written by `save_model()` (inside the same run context). That file and the metrics JSON are the DVC-tracked outputs. MLflow is not a DVC dependency, so re-running `train` always creates a new MLflow run.

Settings come from [`src/utils/config.py`](../../src/utils/config.py) (`Settings`, `.env` loading): `random_seed=42`, `data_dir=<repo>/data`, `models_dir=<repo>/models`, `mlflow_tracking_uri`, `log_level`. See [Configuration & Environment](../concepts/configuration_and_environment.md).

## Model card

[`docs/model_card.md`](../../docs/model_card.md) is a template that lists nine headings in Portuguese: model details, intended use, factors, metrics, evaluation data, training data, quantitative analysis (including fairness), ethical considerations, and limitations and recommendations. It has no content of its own yet. The fairness AUCs logged by `train` are the intended input for section 7.

## Entrypoint note

[`src/main.py`](../../src/main.py) is only a placeholder. Its `main()` prints a message and does not run the pipeline. Pipeline execution goes through `dvc repro` or the individual `python -m` modules above. Coverage is configured in `pyproject.toml` with `source = ["src"]` and `omit = ["src/main.py"]`.

## Tests

Unit tests under `tests/unit/` cover this workflow:

- `test_features.py`: output columns equal `MODEL_FEATURES`, the sentinel becomes null, the ratios are correct, income changes propagate to the ratios, and division by zero gives `NaN`.
- `test_prepare_data.py`: reference and production are disjoint with a matching target rate, invalid data blocks output, and a missing CSV gives a clear error.
- `test_baseline.py`: AUC and KS sanity checks, fairness keys, unknown categories do not break scoring, gender is not a model feature, and a joblib save/load round trip preserves scores and threshold.

See [Test Suite & CI](../testing/test_suite_and_ci.md) and [Architecture Overview](../architecture/overview.md) for the wider context, and [Quality Standards](development_and_quality.md) for lint and complexity gates.
