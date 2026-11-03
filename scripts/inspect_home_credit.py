"""Inspeciona os campos iniciais do Home Credit."""

from pathlib import Path

import pandas as pd

DATA_PATH = Path("data/raw/application_train.csv")

COLUMNS = [
    "SK_ID_CURR",
    "TARGET",
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "DAYS_BIRTH",
    "CNT_CHILDREN",
    "NAME_INCOME_TYPE",
]


def main() -> None:
    """Exibe informações para definir os contratos de dados."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset não encontrado: {DATA_PATH}")

    all_columns = pd.read_csv(DATA_PATH, nrows=0).columns
    df = pd.read_csv(DATA_PATH, usecols=COLUMNS)

    print("\n=== HOME CREDIT ===")
    print(f"Registros: {len(df):,}")
    print(f"Total de colunas no CSV: {len(all_columns)}")

    print("\n=== TIPOS DAS COLUNAS SELECIONADAS ===")
    print(df.dtypes)

    print("\n=== VALORES AUSENTES ===")
    print(df.isna().sum())

    print("\n=== IDS DUPLICADOS ===")
    print(df["SK_ID_CURR"].duplicated().sum())

    print("\n=== DISTRIBUIÇÃO DO TARGET ===")
    print(df["TARGET"].value_counts(normalize=True))

    print("\n=== ESTATÍSTICAS NUMÉRICAS ===")
    print(df.describe().round(2))


if __name__ == "__main__":
    main()
