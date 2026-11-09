---
type: guide
title: Quickstart & Task Routing
description: Entry point for the credit-scoring reliability project (Pandera contracts, XGBoost/MLflow baseline, Evidently drift, Prometheus/Grafana observability). Gives setup steps, the ordered run-through commands, and a task-routing map to the architecture, concepts, workflow, operations and testing pages.
tags: [quickstart, task-routing, environment-setup, commands, wiki-map, credit-scoring]
verified:
  - by: openwiki/0.7.2
    at: 2026-11-09T02:01:44.977Z
sources:
  - id: openwiki-source-5f5b95b3d6a215fa02ceb945
    resource: repo://.env.example
  - id: openwiki-source-164e2da859b5277df81c7d94
    resource: repo://.github/workflows/ci.yml
  - id: openwiki-source-4d1645cb6317345817452838
    resource: repo://.pre-commit-config.yaml
  - id: openwiki-source-8037e2358a2c4f9b2c722a11
    resource: repo://AGENTS.md
  - id: openwiki-source-05ccef8d4cf1698187f20464
    resource: repo://pyproject.toml
  - id: openwiki-source-23775c3de52f3ab95a13cb8b
    resource: repo://README.md
  - id: openwiki-source-d63450a84702158a6ce7cde3
    resource: repo://scripts/check_notebooks.py
  - id: openwiki-source-1fd01080171f877c089206b9
    resource: repo://scripts/run_monitored_drift.py
  - id: openwiki-source-11b9d806fcc6dd6e7747ed87
    resource: repo://src/main.py
  - id: openwiki-source-f12fdb76c2f98bd11af25d76
    resource: repo://src/utils/config.py
generated: { by: "openwiki/0.7.2", at: "2026-11-09T02:01:44.977Z" }
---

# Quickstart & Task Routing

This repository is the FIAP Tech Challenge Fase 4 project (Machine Learning Engineering). It simulates a fintech that uses a credit-scoring model and builds a reliability layer around it. The README objective list covers:

- Pandera data contracts.
- An XGBoost baseline tracked in MLflow.
- Evidently data-drift simulation and detection.
- Analysis of drift impact on predictions.
- Structured logs, Prometheus metrics and a Grafana dashboard.
- Automatic alert rules for drift and collector downtime.
- Governance, privacy and LGPD documentation.

The dataset is Home Credit Default Risk (Kaggle). It is a local artifact and is not versioned.

Use this page to set up the project, run it end to end, and find the right deeper page.

## Task Routing Map

```mermaid
flowchart TD
    Start["Task"] --> Choice{"What are you working on?"}
    Choice -->|"System map, layers, data flow"| Arch["Architecture Overview"]
    Choice -->|"Pandera contracts, drift, score impact"| DC["Data Contracts and Drift"]
    Choice -->|"Features, training, MLflow"| ML["ML Pipeline and Tracking"]
    Choice -->|"Logs, Prometheus, Grafana, alerts"| Obs["Observability Stack"]
    Choice -->|".env, settings, paths"| Cfg["Configuration and Environment"]
    Choice -->|"Ruff, pre-commit, notebooks, complexity"| Dev["Development and Quality"]
    Choice -->|"Pytest, markers, CI jobs"| Test["Test Suite and CI"]
```

| If you need to... | Read | Domain |
|---|---|---|
| Understand how data contracts, training, drift monitoring, score impact and observability fit together | [Architecture Overview](architecture/overview.md) | Architecture |
| Change or understand Pandera contracts, batch validation, Home Credit loading, drift simulation, the Evidently PSI monitor, or score-impact analysis | [Data Contracts, Drift Detection and Score Impact](concepts/data_contracts_and_drift.md) | Concepts |
| Change settings, `.env` values or directory resolution | [Environment Configuration & Settings Management](concepts/configuration_and_environment.md) | Concepts |
| Prepare data, engineer features, train the baseline, or read MLflow results | [ML Pipeline Structure & Experiment Tracking](workflows/ml_pipeline_and_tracking.md) | Workflows |
| Run or modify structured logging, Prometheus metrics, the Docker Compose stack, alert rules or the Grafana dashboard | [Observability Stack: Logging, Metrics, Prometheus and Grafana](operations/observability_stack.md) | Operations |
| Work with Ruff, pre-commit, Radon/Xenon gates or notebook hygiene | [Quality Standards, Quality Gates, & Notebook Hygiene](workflows/development_and_quality.md) | Workflows |
| Run or add tests, understand markers, coverage and the GitHub Actions jobs | [Test Suite & CI/CD Pipelines](testing/test_suite_and_ci.md) | Testing |

## Setup

Prerequisites (README): Python 3.12, Git, [uv](https://docs.astral.sh/uv/), and the dataset file. Docker with the Compose plugin is needed only for the observability stack, not for running the Python scripts.

```bash
uv python install 3.12
uv sync --locked
cp .env.example .env          # PowerShell: Copy-Item .env.example .env
uv run pre-commit install     # optional: enable local quality hooks
```

`.env.example` sets `ENV=local`, `LOG_LEVEL=INFO`, `RANDOM_SEED=42` and `MLFLOW_TRACKING_URI=sqlite:///mlflow.db`. The README copies `.env` "when needed", because `Settings` in [`../src/utils/config.py`](../src/utils/config.py) has defaults for every field. It also provides `data_dir` and `models_dir`, and ignores unknown variables. See [Configuration](concepts/configuration_and_environment.md).

Download `application_train.csv` from Kaggle and place it at `data/raw/application_train.csv`. Raw data, processed datasets and trained models are local and must not be pushed to GitHub.

## End-to-end run order

Run these from the repository root, in order (README "Executar o fluxo completo"):

```bash
uv run python -m scripts.validate_home_credit        # 1. validate input with Pandera
uv run python -m src.pipelines.prepare_data          # 2. reference / production-base split
uv run python -m src.training.train                  # 3. train + log baseline to MLflow
uv run python -m scripts.simulate_home_credit_drift  # 4. simulate drift in production data
uv run python -m scripts.run_drift                   # 5. Evidently PSI reports and alerts
uv run python -m scripts.analyze_score_impact        # 6. compare scores before/after drift
uv run python -m scripts.run_monitored_drift         # 7. validation + drift + .prom export
```

```mermaid
flowchart LR
    CSV["data/raw/application_train.csv"] --> V["Pandera contract"]
    V --> P["prepare_data: reference and production base"]
    P --> T["train: baseline.joblib + MLflow"]
    P --> S["simulate drift"]
    S --> D["run_drift: Evidently PSI"]
    T --> I["score impact"]
    S --> I
    D --> M["run_monitored_drift"]
    M --> PROM["reports/operational_metrics.prom"]
    PROM --> OBS["Node Exporter, Prometheus, Grafana"]
```

Key outputs:

- `data/processed/*.parquet`, `models/baseline.joblib` and `models/baseline_metrics.json`.
- `reports/drift_*.html` and `reports/drift_*.json`, `reports/drift_alerts.json` and `reports/score_impact.json`.
- `reports/operational_metrics.prom`, which Prometheus reads via Node Exporter's textfile collector.

Details live in [Data Contracts and Drift](concepts/data_contracts_and_drift.md) and [ML Pipeline](workflows/ml_pipeline_and_tracking.md).

Things to know before changing anything:

- The "production" data is a random split of the historical data, not a later time period.
- Drift is artificially simulated on two variables, `AMT_INCOME_TOTAL` and `AMT_CREDIT`.
- Scoring does not run Pandera validation on every call.
- `src/main.py` is only a placeholder entrypoint. Its `main()` prints a "project initialized" message, and it is excluded from coverage. The real entrypoints are the modules and scripts above.

## Observability stack

Python runs locally through `uv`. [`compose.observability.yaml`](../compose.observability.yaml) starts only Node Exporter, Prometheus and Grafana. It does not train the model or schedule drift runs. After step 7, set `GRAFANA_ADMIN_PASSWORD` and start the stack:

```bash
docker compose -f compose.observability.yaml up -d
```

Grafana is at `http://localhost:3000`, Prometheus at `http://localhost:9090` and Node Exporter at `http://localhost:9100`. Alerts are evaluated by Prometheus only; no Alertmanager notification channel is configured. The `.prom` file reflects the latest run only, so it can go stale. Setup, metrics, alert rules and troubleshooting are in [Observability Stack](operations/observability_stack.md).

## Quality and tests

```bash
uv run pytest -v
uv run ruff check .
uv run ruff format . --check
uv run python scripts/check_notebooks.py
uv run pre-commit run --all-files
uv run radon cc src -a -s
uv run xenon --max-absolute B --max-modules A --max-average A src
```

- **Ruff** enforces the `E`, `F`, `I`, `N`, `UP`, `D`, `B` and `SIM` rules at 88 columns with Google-style docstrings. Notebooks are excluded.
- **Radon/Xenon** gates run in CI over `src`.
- **Pre-commit** runs file-hygiene hooks, Ruff check and format, and `nbstripout`. A local `check-notebooks` hook then runs `scripts/check_notebooks.py` on changed `.ipynb` files.
- **`check_notebooks.py`** checks the notebook paths you pass, or every `notebooks/**/*.ipynb` if none are given. It lists code cells that have outputs or a non-null `execution_count`, exits with status 1 if any are found, and suggests `uv run nbstripout <notebook.ipynb>`.
- **CI** (`.github/workflows/ci.yml`) runs on pushes and PRs to `main` and `development`, and on manual dispatch.
  - A `quality` job runs Ruff, the notebook check and the Radon/Xenon gates.
  - A `test` job runs pytest with coverage and uploads `coverage.xml`.
  - The `docker` image-push job is disabled (`if: false`) until a root `Dockerfile` exists.

See [Development and Quality](workflows/development_and_quality.md) and [Test Suite & CI](testing/test_suite_and_ci.md).

## Agent guidance

[`../AGENTS.md`](../AGENTS.md) treats source code and tests as authoritative. It also asks agents to use OpenWiki retrieval just in time, run the narrowest quiet validation, and not hand-edit generated wiki pages.
