"""Gera gráficos de fairness (ROC, FPR, FNR, recall) a partir do baseline treinado.

Este script treina o modelo na referência, computa as predições no hold-out
e gera quatro figuras em ``reports/figures/``:

- ``roc_by_gender.png`` — curvas ROC por gênero
- ``roc_by_age.png`` — curvas ROC por faixa etária
- ``error_rates_by_gender.png`` — FPR, FNR e recall por gênero
- ``error_rates_by_age.png`` — FPR, FNR e recall por faixa etária

Pré-requisito: executar o pipeline de preparação para gerar
``data/processed/reference.parquet``.
"""

from pathlib import Path

import pandas as pd

from src.features.build import GENDER
from src.pipelines.prepare_data import REFERENCE_FILE
from src.training.train import train
from src.utils.config import settings
from src.visualization.fairness_plots import (
    plot_error_rates_by_group,
    plot_roc_by_group,
)

FIGURES_DIR = Path(__file__).resolve().parents[1] / "reports" / "figures"


def main() -> None:
    """Treina o baseline e gera os gráficos de fairness."""
    path = settings.data_dir / "processed" / REFERENCE_FILE
    if not path.is_file():
        raise FileNotFoundError(f"Execute primeiro o pipeline de preparação: {path}")

    reference = pd.read_parquet(path)
    pipeline, metrics, fairness = train(reference)

    # Recomputa predições no hold-out para obter x_val, y_val e scores.
    from sklearn.model_selection import train_test_split

    from src.features.build import TARGET

    x = reference.drop(columns=[TARGET])
    y = reference[TARGET]
    x_train, x_val, y_train, y_val = train_test_split(
        x, y, test_size=0.2, stratify=y, random_state=settings.random_seed
    )
    scores = pipeline.predict_proba(x_val)[:, 1]

    threshold = metrics["threshold"]

    # Gera os quatro gráficos.
    plot_roc_by_group(
        x_val,
        y_val,
        scores,
        GENDER,
        "Gênero",
        FIGURES_DIR / "roc_by_gender.png",
    )
    plot_roc_by_group(
        x_val,
        y_val,
        scores,
        "DAYS_BIRTH",
        "Faixa Etária",
        FIGURES_DIR / "roc_by_age.png",
    )
    plot_error_rates_by_group(
        x_val,
        y_val,
        scores,
        threshold,
        GENDER,
        "Gênero",
        FIGURES_DIR / "error_rates_by_gender.png",
    )
    plot_error_rates_by_group(
        x_val,
        y_val,
        scores,
        threshold,
        "DAYS_BIRTH",
        "Faixa Etária",
        FIGURES_DIR / "error_rates_by_age.png",
    )

    print("=== GRÁFICOS DE FAIRNESS GERADOS ===")
    print(f"Diretório: {FIGURES_DIR}")
    print(f"Limiar de decisão: {threshold:.4f}")
    print(f"AUC geral: {metrics['auc']:.4f}")
    print(
        f"FPR: {metrics['fpr']:.4f} | "
        f"FNR: {metrics['fnr']:.4f} | "
        f"Recall: {metrics['recall']:.4f}"
    )
    print("\nMétricas por grupo:")
    for key, value in sorted(fairness.items()):
        print(f"  {key}: {value:.4f}")


if __name__ == "__main__":
    main()
