"""Demonstra a rejeicao de um lote invalido pelo Pandera."""

from pathlib import Path

import pandas as pd
import pandera.pandas as pa

from src.data.contracts import (
    FEATURE_COLUMNS,
    validate_training_batch,
)

DATA_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "raw" / "application_train.csv"
)


def main() -> None:
    """Injeta erros em uma amostra real e testa o bloqueio."""
    columns = [*FEATURE_COLUMNS, "TARGET"]
    df = pd.read_csv(DATA_PATH, usecols=columns, nrows=5)

    print("=== VALIDACAO DO LOTE ORIGINAL ===")
    validate_training_batch(df)
    print("Lote original aprovado.")

    invalid = df.copy()

    # Simulacoes de erros de qualidade
    invalid.loc[0, "AMT_INCOME_TOTAL"] = -100.0
    invalid.loc[1, "AMT_CREDIT"] = 0.0
    invalid.loc[2, "DAYS_BIRTH"] = -3000
    invalid.loc[3, "TARGET"] = 3
    invalid.loc[4, "SK_ID_CURR"] = invalid.loc[0, "SK_ID_CURR"]

    print("\n=== VALIDACAO DO LOTE INVALIDO ===")

    try:
        validate_training_batch(invalid)
    except pa.errors.SchemaErrors as error:
        print("Lote REJEITADO pelo contrato de dados.")
        print("\nViolacoes encontradas:")

        columns = ["column", "check", "failure_case"]
        print(error.failure_cases[columns].to_string(index=False))
        return

    raise RuntimeError("ERRO: o contrato aprovou um lote invalido.")


if __name__ == "__main__":
    main()
