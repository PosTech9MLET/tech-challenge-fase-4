"""Configurações do projeto carregadas do .env (Pydantic Settings)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Variáveis de ambiente do projeto."""

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    env: str = "local"
    log_level: str = "INFO"
    random_seed: int = 42
    mlflow_tracking_uri: str = f"sqlite:///{ROOT_DIR / 'mlflow.db'}"
    data_dir: Path = ROOT_DIR / "data"
    models_dir: Path = ROOT_DIR / "models"


settings = Settings()
