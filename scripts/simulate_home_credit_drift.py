"""Executa a simulação de Data Drift no Home Credit."""

import pandas as pd

from src.data.contracts import validate_inference_batch
from src.data.simulate_drift import simulate_income_credit_drift
from src.pipelines.prepare_data import PRODUCTION_FILE
from src.utils.config import settings

DRIFT_FILE = "production_drift.parquet"


def main() -> None:
    """Gera uma base de produção com drift controlado."""
    data_dir = settings.data_dir / "processed"
    source = data_dir / PRODUCTION_FILE

    if not source.is_file():
        raise FileNotFoundError(f"Execute primeiro o pipeline de preparação: {source}")

    production = pd.read_parquet(source)

    drifted = simulate_income_credit_drift(
        production,
        fraction=0.80,
        income_multiplier=1.80,
        credit_multiplier=1.70,
        seed=42,
    )

    # Na inferência, o TARGET não está disponível.
    inference_data = drifted.drop(columns=["TARGET"], errors="ignore")
    validate_inference_batch(inference_data)

    output = data_dir / DRIFT_FILE
    drifted.to_parquet(output, index=False)

    print("=== SIMULAÇÃO DE DATA DRIFT ===")
    print(f"Registros: {len(drifted):,}")
    print("Contrato Pandera: APROVADO")

    for column in ("AMT_INCOME_TOTAL", "AMT_CREDIT"):
        before = production[column].mean()
        after = drifted[column].mean()

        print(f"\n{column}")
        print(f"Média original: {before:,.2f}")
        print(f"Média simulada: {after:,.2f}")
        print(f"Variação: {(after / before - 1) * 100:.2f}%")

    print(f"\nArquivo gerado: {output}")


if __name__ == "__main__":
    main()
