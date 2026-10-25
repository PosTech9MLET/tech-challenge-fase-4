---
type: concept
title: Environment Configuration & Settings Management
description: Detailed guide to runtime configuration management using Pydantic Settings, environment variable overrides via .env files, and ROOT_DIR-based path resolution across environments.
tags: [configuration, environment, pydantic-settings, dotenv, path-resolution]
verified:
  - by: openwiki/0.7.2
    at: 2026-10-24T23:05:52.220Z
sources:
  - id: openwiki-source-5f5b95b3d6a215fa02ceb945
    resource: repo://.env.example
  - id: openwiki-source-f12fdb76c2f98bd11af25d76
    resource: repo://src/utils/config.py
  - id: openwiki-source-154200283d94041bcf05d48f
    resource: repo://tests/unit/test_smoke.py
generated: { by: "openwiki/0.7.2", at: "2026-10-24T23:05:52.220Z" }
---

# Environment Configuration & Settings Management

Centralized configuration management ensures that runtime parameters, environment variables, path resolutions, and reproducibility settings remain consistent across local development, continuous integration (CI) pipelines, containerized deployments, and production environments.

In this repository, settings management is centralized in [`src/utils/config.py`](../../src/utils/config.py) using Pydantic Settings (`pydantic-settings`). Configuration parameters are strongly typed, backed by default values, and automatically populated or overridden by environment variables and local `.env` files.

---

## Architecture & Resolution Control Flow

The configuration module dynamically determines the project's root directory and resolves all relative filesystem paths and database URIs from that anchor. It also enforces precedence when merging environment source layers.

<!-- openwiki: mermaid parse failed and this diagram was converted to a text fence so it does not break rendering. Fix the diagram source and restore the mermaid fence. Parser error: Heuristic: an unescaped angle bracket inside a label breaks rendering; rephrase the label. -->
```text
flowchart TD
    OSEnv["OS Environment Variables\n(ENV, LOG_LEVEL, etc.)"] --> Overrides["Precedence Logic\n(OS Env > .env > Defaults)"]
    DotEnv["Dotenv File\n(ROOT_DIR / .env)"] --> Overrides
    Defaults["Pydantic Field Defaults\n(env='local', seed=42, etc.)"] --> Overrides
    RootDir["Path Anchor Calculation\nROOT_DIR = Path(__file__).resolve().parents[2]"] --> PathResolution["Path Resolution\n(data/, models/, mlflow.db)"]
    Overrides --> SettingsModel["Settings Model Instantiation\n(pydantic_settings.BaseSettings)"]
    PathResolution --> SettingsModel
    SettingsModel --> Singleton["Global settings Singleton\n(src.utils.config.settings)"]
    Singleton --> Ingestion["src/data/"]
    Singleton --> Training["src/training/"]
    Singleton --> Pipeline["src/main.py"]
    Singleton --> TestSuite["tests/unit/test_smoke.py"]
```
*Figure 1: Configuration precedence hierarchy, root path resolution, and global singleton distribution.*

---

## Root Directory Anchor (`ROOT_DIR`)

To prevent issues with relative working directories when executing code from different locations (such as running Pytest from repository root, executing scripts from `scripts/`, or importing modules inside Jupyter notebooks), path resolution relies on a calculated `ROOT_DIR` anchor in [`src/utils/config.py`](../../src/utils/config.py):

```python
ROOT_DIR = Path(__file__).resolve().parents[2]
```

Because `__file__` resolves to `src/utils/config.py`, moving up three parent steps (`parents[0]` = `src/utils`, `parents[1]` = `src`, `parents[2]` = repository root) dynamically locates the repository base path across operating systems (Linux, macOS, Windows) and execution environments.

---

## The `Settings` Model

The `Settings` class extends Pydantic's `BaseSettings` and manages configuration loading via `SettingsConfigDict`:

```python
class Settings(BaseSettings):
    """Variáveis de ambiente do projeto."""

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    env: str = "local"
    log_level: str = "INFO"
    random_seed: int = 42
    mlflow_tracking_uri: str = f"sqlite:///{ROOT_DIR / 'mlflow.db'}"
    data_dir: Path = ROOT_DIR / "data"
    models_dir: Path = ROOT_DIR / "models"
```

### Model Configuration (`model_config`)

- **`env_file = ROOT_DIR / ".env"`**: Directs Pydantic to read environment key-value pairs from `.env` located at the repository root.
- **`extra = "ignore"`**: Ignores unmapped environment variables or unexpected keys in `.env` without throwing validation errors.

### Configuration Fields Specification

| Field Name | Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `env` | `str` | `"local"` | Execution environment identifier (e.g., `local`, `dev`, `staging`, `prod`). |
| `log_level` | `str` | `"INFO"` | Logging verbosity level (e.g., `DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `random_seed` | `int` | `42` | Global random seed used for deterministic data splitting, transformations, and model training. |
| `mlflow_tracking_uri` | `str` | `f"sqlite:///{ROOT_DIR / 'mlflow.db'}"` | MLflow tracking backend database URI, defaulted to a local SQLite database at repository root. |
| `data_dir` | `Path` | `ROOT_DIR / "data"` | Root path for dataset storage (`raw/`, `interim/`, `processed/`, `features/`). |
| `models_dir` | `Path` | `ROOT_DIR / "models"` | Target directory for saving serialized model artifacts and checkpoints. |

---

## Environment Variable Precedence & `.env` Loading

Configuration values are resolved according to a strict three-tier precedence hierarchy:

1. **Operating System Environment Variables**: Variables explicitly set in the OS shell or container runtime (e.g., `export LOG_LEVEL=DEBUG` or Docker environment options) hold highest priority.
2. **Local `.env` File**: Key-value pairs defined in `ROOT_DIR / .env` override Pydantic field defaults when an OS environment variable is not present.
3. **Pydantic Model Defaults**: Built-in default field values defined in `Settings` serve as fallback values.

### Setting Up Local Environment Configuration

Developers customize local environments using the provided template file [`.env.example`](../../.env.example):

```bash
# Copy the example environment file to .env
cp .env.example .env
```

The standard [`.env.example`](../../.env.example) template contains:

```env
ENV=local
LOG_LEVEL=INFO
RANDOM_SEED=42
MLFLOW_TRACKING_URI=sqlite:///mlflow.db
```

---

## Module Singleton & Application Usage

[`src/utils/config.py`](../../src/utils/config.py) instantiates a global configuration object at import time:

```python
settings = Settings()
```

Application submodules, pipelines, and scripts import `settings` directly to access configuration parameters:

```python
from src.utils.config import settings

# Example usage in pipeline execution or training
print(f"Running in environment: {settings.env}")
print(f"Data directory: {settings.data_dir}")
print(f"MLflow URI: {settings.mlflow_tracking_uri}")
```

---

## Testing & Configuration Verification

System initialization and configuration loading are verified through smoke tests in [`tests/unit/test_smoke.py`](../../tests/unit/test_smoke.py):

```python
from src.utils.config import settings


def test_settings_carrega():
    assert settings.random_seed == 42
    assert settings.data_dir.name == "data"
```

### Overriding Settings During Testing

When writing unit or integration tests that require specific configuration values (such as isolated temporary test directories or custom log levels), Pytest's `monkeypatch` fixture can override `settings` attributes or environment variables:

```python
def test_custom_config(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")
    assert settings.data_dir == tmp_path / "data"
```

---

## Related Documents

- [System Architecture & ML Pipeline Design](../architecture/overview.md) – Overview of component boundaries, data processing flow, and system module responsibilities.
- [Test Suite & CI Pipeline](../testing/test_suite_and_ci.md) – Details on unit and integration testing, Pytest execution, and CI/CD quality gates.
- [Development & Quality Workflows](../workflows/development_and_quality.md) – Standard development workflow, linting rules, pre-commit hooks, and environment setup guidelines.
