"""Valida os dados originais do Home Credit."""

from pathlib import Path

import pandas as pd

from src.data.contracts import FEATURE_COLUMNS, validate_training_batch

DATA_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "raw" / "application_train.csv"
)


def main() -> None:
    """Carrega e valida o dataset de treinamento."""
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"Arquivo nao encontrado: {DATA_PATH}")

    columns = [*FEATURE_COLUMNS, "TARGET"]
    df = pd.read_csv(DATA_PATH, usecols=columns)

    print(f"Validando {len(df):,} registros...")

    validated = validate_training_batch(df)

    print("Contrato de dados: APROVADO")
    print(f"Registros validados: {len(validated):,}")


if __name__ == "__main__":
    main()
