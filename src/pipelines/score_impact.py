"""Compara as predições antes e depois do Data Drift."""

import pandas as pd
from sklearn.pipeline import Pipeline

from src.features.build import ID_COLUMN, TARGET
from src.models.baseline import score


def _validate_base(name: str, data: pd.DataFrame) -> None:
    """Valida uma base: não vazia, com ID presente, sem nulos e único."""
    if data.empty:
        raise ValueError(f"{name} não pode estar vazio.")

    if ID_COLUMN not in data.columns:
        raise ValueError(f"{ID_COLUMN} ausente em {name}.")

    if data[ID_COLUMN].isna().any() or not data[ID_COLUMN].is_unique:
        raise ValueError(f"IDs inválidos ou duplicados em {name}.")


def _validate_inputs(
    production: pd.DataFrame,
    drifted: pd.DataFrame,
    threshold: float,
) -> None:
    """Valida o limiar e as duas bases antes de comparar os scores."""
    if not 0 < threshold < 1:
        raise ValueError("O threshold deve estar entre 0 e 1.")

    _validate_base("production", production)
    _validate_base("drifted", drifted)

    if set(production[ID_COLUMN]) != set(drifted[ID_COLUMN]):
        raise ValueError("As duas bases devem conter os mesmos clientes.")


def _predict(data: pd.DataFrame, column: str, model: Pipeline) -> pd.DataFrame:
    """Gera os scores de uma base, indexados pelo ID do cliente."""
    features = data.drop(columns=[TARGET], errors="ignore")
    probabilities = score(features, model=model)

    return pd.DataFrame(
        {
            ID_COLUMN: data[ID_COLUMN].to_numpy(),
            column: probabilities.to_numpy(),
        }
    )


def _summarize(
    comparison: pd.DataFrame,
    threshold: float,
) -> dict[str, float | int]:
    """Calcula o resumo agregado e marca as decisões que cruzaram o limiar."""
    before_positive = comparison["score_before"] >= threshold
    after_positive = comparison["score_after"] >= threshold

    comparison["crossed_threshold"] = before_positive != after_positive

    return {
        "records": len(comparison),
        "threshold": float(threshold),
        "mean_score_before": float(comparison["score_before"].mean()),
        "mean_score_after": float(comparison["score_after"].mean()),
        "mean_absolute_change": float(comparison["score_delta"].abs().mean()),
        "share_above_threshold_before": float(before_positive.mean()),
        "share_above_threshold_after": float(after_positive.mean()),
        "changed_decisions": int(comparison["crossed_threshold"].sum()),
        "changed_decisions_pct": float(comparison["crossed_threshold"].mean() * 100),
    }


def compare_prediction_scores(
    production: pd.DataFrame,
    drifted: pd.DataFrame,
    model: Pipeline,
    threshold: float,
) -> tuple[pd.DataFrame, dict[str, float | int]]:
    """Compara scores dos mesmos clientes, alinhados pelo ID."""
    _validate_inputs(production, drifted, threshold)

    before = _predict(production, "score_before", model)
    after = _predict(drifted, "score_after", model)

    comparison = before.merge(
        after,
        on=ID_COLUMN,
        how="inner",
        validate="one_to_one",
    )

    comparison["score_delta"] = comparison["score_after"] - comparison["score_before"]

    summary = _summarize(comparison, threshold)

    return comparison, summary
