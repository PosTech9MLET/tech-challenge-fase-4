"""Pipeline do modelo baseline de Credit Scoring (features + XGBoost)."""

import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OrdinalEncoder
from xgboost import XGBClassifier

from src.features.build import CATEGORICAL, MODEL_FEATURES, NUMERIC, build_features
from src.utils.config import settings

logger = logging.getLogger(__name__)

MODEL_FILE = "baseline.joblib"
METRICS_FILE = "baseline_metrics.json"

XGB_PARAMS = {
    "n_estimators": 400,
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 5,
    "eval_metric": "auc",
}


def build_pipeline(seed: int = 42) -> Pipeline:
    """Monta o pipeline completo: dados brutos → features → XGBoost.

    Categorias desconhecidas na inferência viram ``NaN`` (tratado nativamente
    pelo XGBoost), então dados de produção com categorias novas não quebram o
    modelo.

    Args:
        seed: semente do XGBoost.

    Returns:
        Pipeline do scikit-learn que recebe o DataFrame bruto.
    """
    encoder = OrdinalEncoder(
        handle_unknown="use_encoded_value",
        unknown_value=np.nan,
        encoded_missing_value=np.nan,
    )
    columns = ColumnTransformer(
        [("cat", encoder, CATEGORICAL), ("num", "passthrough", NUMERIC)],
        verbose_feature_names_out=False,
    )
    columns.set_output(transform="pandas")
    return Pipeline(
        [
            ("features", FunctionTransformer(build_features)),
            ("columns", columns),
            ("xgb", XGBClassifier(**XGB_PARAMS, random_state=seed)),
        ]
    )


def save_model(pipeline: Pipeline, metrics: dict[str, float]) -> Path:
    """Salva o pipeline treinado e as métricas (inclui o limiar de decisão)."""
    settings.models_dir.mkdir(parents=True, exist_ok=True)
    path = settings.models_dir / MODEL_FILE
    joblib.dump(pipeline, path)
    (settings.models_dir / METRICS_FILE).write_text(json.dumps(metrics, indent=2))
    return path


def load_model() -> Pipeline:
    """Carrega o pipeline treinado de ``models/``."""
    return joblib.load(settings.models_dir / MODEL_FILE)


def load_threshold() -> float:
    """Lê o limiar de decisão salvo no treino."""
    text = (settings.models_dir / METRICS_FILE).read_text()
    return float(json.loads(text)["threshold"])


def score(raw: pd.DataFrame, model: Pipeline | None = None) -> pd.Series:
    """Calcula a probabilidade de inadimplência (PD) para dados brutos.

    Args:
        raw: DataFrame com as colunas brutas (target é ignorado se presente).
        model: pipeline já carregado; se omitido, carrega de ``models/``.

    Returns:
        Série com a probabilidade de inadimplência, indexada como ``raw``.
    """
    pipeline = model if model is not None else load_model()
    proba = pipeline.predict_proba(raw)[:, 1]
    return pd.Series(proba, index=raw.index, name="score")


__all__ = ["MODEL_FEATURES", "build_pipeline", "load_model", "save_model", "score"]
