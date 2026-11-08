"""Analisa o impacto do Data Drift nas predições do XGBoost."""

import json
from pathlib import Path

import pandas as pd

from src.models.baseline import load_model, load_threshold
from src.pipelines.prepare_data import PRODUCTION_FILE
from src.pipelines.score_impact import compare_prediction_scores
from src.utils.config import settings

DRIFT_FILE = "production_drift.parquet"
REPORT_DIR = Path(__file__).resolve().parents[1] / "reports"


def main() -> None:
    """Compara scores da produção original e da produção simulada."""
    data_dir = settings.data_dir / "processed"

    production = pd.read_parquet(data_dir / PRODUCTION_FILE)
    drifted = pd.read_parquet(data_dir / DRIFT_FILE)

    model = load_model()
    threshold = load_threshold()

    _, summary = compare_prediction_scores(
        production,
        drifted,
        model,
        threshold,
    )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    output = REPORT_DIR / "score_impact.json"

    output.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    print("=== IMPACTO DO DATA DRIFT NO XGBOOST ===")
    print(f"Registros comparados: {summary['records']:,}")
    print(f"Limiar de classificação: {summary['threshold']:.4f}")
    print(f"Score médio original: {summary['mean_score_before']:.4f}")
    print(f"Score médio simulado: {summary['mean_score_after']:.4f}")
    print(f"Mudança absoluta média: {summary['mean_absolute_change']:.4f}")

    print(f"Acima do limiar, original: {summary['share_above_threshold_before']:.2%}")
    print(f"Acima do limiar, simulado: {summary['share_above_threshold_after']:.2%}")

    print(f"Classificações alteradas: {summary['changed_decisions']:,}")
    print(
        "Percentual de classificações alteradas: "
        f"{summary['changed_decisions_pct']:.2f}%"
    )

    print(f"\nRelatório gerado: {output}")


if __name__ == "__main__":
    main()
