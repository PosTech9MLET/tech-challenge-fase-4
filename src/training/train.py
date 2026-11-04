"""Treino e avaliação do baseline de Credit Scoring, com registro no MLflow."""

import logging

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

from src.data.contracts import validate_training_batch
from src.features.build import GENDER, TARGET
from src.models.baseline import XGB_PARAMS, build_pipeline, save_model
from src.pipelines.prepare_data import REFERENCE_FILE
from src.utils.config import settings

logger = logging.getLogger(__name__)

EXPERIMENT = "credit-scoring-baseline"
AGE_BINS = [0, 30, 45, 60, 200]
AGE_LABELS = ["lt30", "30_44", "45_59", "60_plus"]
MIN_GROUP_POSITIVES = 30


def ks_statistic(y_true: pd.Series, scores: np.ndarray) -> float:
    """Estatística KS entre os scores de bons e maus pagadores."""
    fpr, tpr, _ = roc_curve(y_true, scores)
    return float((tpr - fpr).max())


def best_f1_threshold(y_true: pd.Series, scores: np.ndarray) -> float:
    """Limiar que maximiza o F1 (útil com classe positiva rara)."""
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    denom = np.clip(precision + recall, 1e-12, None)
    f1 = 2 * precision * recall / denom
    return float(thresholds[int(np.argmax(f1[:-1]))])


def evaluate(
    y_true: pd.Series, scores: np.ndarray, threshold: float | None = None
) -> dict[str, float]:
    """Calcula AUC, KS, PR-AUC e F1 no limiar (ou no melhor limiar por F1)."""
    cut = best_f1_threshold(y_true, scores) if threshold is None else threshold
    return {
        "auc": float(roc_auc_score(y_true, scores)),
        "ks": ks_statistic(y_true, scores),
        "pr_auc": float(average_precision_score(y_true, scores)),
        "threshold": cut,
        "f1": float(f1_score(y_true, scores >= cut)),
    }


def auc_by_group(
    y_true: pd.Series, scores: pd.Series, groups: pd.Series, prefix: str
) -> dict[str, float]:
    """AUC por subgrupo, ignorando grupos com poucos inadimplentes.

    Args:
        y_true: target real, indexado como ``scores`` e ``groups``.
        scores: probabilidades previstas.
        groups: rótulo do grupo de cada linha (``NaN`` é ignorado).
        prefix: prefixo do nome da métrica (ex.: ``gender``).

    Returns:
        Dicionário ``auc_<prefix>_<grupo>`` → AUC.
    """
    frame = pd.concat([y_true, scores, groups], axis=1, keys=["y", "s", "g"])
    result: dict[str, float] = {}
    for name, part in frame.dropna(subset=["g"]).groupby("g", observed=True):
        if part["y"].sum() >= MIN_GROUP_POSITIVES and part["y"].nunique() == 2:
            result[f"auc_{prefix}_{name}"] = float(roc_auc_score(part["y"], part["s"]))
    return result


def fairness_metrics(
    x_val: pd.DataFrame, y_val: pd.Series, scores: np.ndarray
) -> dict[str, float]:
    """AUC por gênero e por faixa etária (análise de viés, não é feature)."""
    proba = pd.Series(scores, index=y_val.index)
    ages = pd.cut(-x_val["DAYS_BIRTH"] / 365.25, AGE_BINS, labels=AGE_LABELS)
    gender = x_val[GENDER].where(x_val[GENDER].isin(["F", "M"]))
    return {
        **auc_by_group(y_val, proba, gender, "gender"),
        **auc_by_group(y_val, proba, ages, "age"),
    }


def train(reference: pd.DataFrame):
    """Treina o baseline na referência, com hold-out estratificado de 20%.

    Args:
        reference: dataset de referência já validado pelo contrato.

    Returns:
        Tupla (pipeline treinado, métricas gerais, métricas de viés).
    """
    x = reference.drop(columns=[TARGET])
    y = reference[TARGET]
    x_train, x_val, y_train, y_val = train_test_split(
        x, y, test_size=0.2, stratify=y, random_state=settings.random_seed
    )
    pipeline = build_pipeline(settings.random_seed)
    pipeline.fit(x_train, y_train)
    scores = pipeline.predict_proba(x_val)[:, 1]
    metrics = evaluate(y_val, scores)
    return pipeline, metrics, fairness_metrics(x_val, y_val, scores)


def main() -> None:
    """Valida a referência, treina o baseline e registra tudo no MLflow."""
    path = settings.data_dir / "processed" / REFERENCE_FILE
    reference = pd.read_parquet(path)
    validate_training_batch(reference)
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run(run_name="baseline-xgboost"):
        pipeline, metrics, fairness = train(reference)
        mlflow.log_params({**XGB_PARAMS, "n_rows": len(reference)})
        mlflow.log_metrics({**metrics, **fairness})
        mlflow.sklearn.log_model(
            pipeline, name="model", serialization_format="cloudpickle"
        )
        save_model(pipeline, metrics)
    logger.info("Baseline treinado: %s", metrics)
    logger.info("Métricas por grupo: %s", fairness)


if __name__ == "__main__":
    logging.basicConfig(level=settings.log_level)
    main()
