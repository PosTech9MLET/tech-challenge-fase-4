"""Contratos de qualidade para os dados Home Credit."""

import pandas as pd
import pandera.pandas as pa

FEATURE_COLUMNS = (
    "SK_ID_CURR",
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "DAYS_BIRTH",
    "CNT_CHILDREN",
    "NAME_INCOME_TYPE",
)


def credit_schema(training: bool = True) -> pa.DataFrameSchema:
    """Define as regras para treinamento ou inferencia."""
    columns = {
        "SK_ID_CURR": pa.Column(int, nullable=False, unique=True),
        "AMT_INCOME_TOTAL": pa.Column(float, pa.Check.gt(0), nullable=False),
        "AMT_CREDIT": pa.Column(float, pa.Check.gt(0), nullable=False),
        "AMT_ANNUITY": pa.Column(float, pa.Check.gt(0), nullable=True),
        "DAYS_BIRTH": pa.Column(int, pa.Check.le(-6575), nullable=False),
        "CNT_CHILDREN": pa.Column(int, pa.Check.ge(0), nullable=False),
        "NAME_INCOME_TYPE": pa.Column(str, nullable=False),
    }

    if training:
        columns["TARGET"] = pa.Column(
            int,
            pa.Check.isin([0, 1]),
            nullable=False,
        )

    return pa.DataFrameSchema(
        columns=columns,
        strict=False,
        coerce=False,
        name=("HomeCreditTraining" if training else "HomeCreditInference"),
    )


def validate_training_batch(df: pd.DataFrame) -> pd.DataFrame:
    """Valida um lote de treinamento."""
    return credit_schema(training=True).validate(df, lazy=True)


def validate_inference_batch(df: pd.DataFrame) -> pd.DataFrame:
    """Valida um lote de inferencia."""
    return credit_schema(training=False).validate(df, lazy=True)
