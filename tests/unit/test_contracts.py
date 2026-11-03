"""Testes dos contratos de qualidade Home Credit."""

import pandas as pd
import pandera.pandas as pa
import pytest

from src.data.contracts import (
    validate_inference_batch,
    validate_training_batch,
)


@pytest.fixture
def valid_batch() -> pd.DataFrame:
    """Cria um lote sintetico e valido."""
    return pd.DataFrame(
        {
            "SK_ID_CURR": [100001, 100002],
            "AMT_INCOME_TOTAL": [100000.0, 150000.0],
            "AMT_CREDIT": [200000.0, 300000.0],
            "AMT_ANNUITY": [10000.0, 15000.0],
            "DAYS_BIRTH": [-12000, -16000],
            "CNT_CHILDREN": [0, 2],
            "NAME_INCOME_TYPE": ["Working", "Pensioner"],
            "TARGET": [0, 1],
        }
    )


def test_valid_training_batch(valid_batch: pd.DataFrame) -> None:
    """Aceita um lote valido de treinamento."""
    validated = validate_training_batch(valid_batch)

    assert len(validated) == 2


@pytest.mark.parametrize(
    ("column", "invalid_value"),
    [
        ("AMT_INCOME_TOTAL", -100.0),
        ("AMT_CREDIT", 0.0),
        ("DAYS_BIRTH", -3000),
        ("CNT_CHILDREN", -1),
        ("TARGET", 3),
    ],
)
def test_invalid_values_are_rejected(
    valid_batch: pd.DataFrame,
    column: str,
    invalid_value: float | int,
) -> None:
    """Rejeita valores que violam os contratos."""
    invalid = valid_batch.copy()
    invalid.loc[0, column] = invalid_value

    with pytest.raises(pa.errors.SchemaErrors) as exc:
        validate_training_batch(invalid)

    assert column in exc.value.failure_cases["column"].tolist()


def test_duplicated_id_is_rejected(
    valid_batch: pd.DataFrame,
) -> None:
    """Rejeita identificadores duplicados."""
    invalid = valid_batch.copy()
    invalid.loc[1, "SK_ID_CURR"] = invalid.loc[0, "SK_ID_CURR"]

    with pytest.raises(pa.errors.SchemaErrors):
        validate_training_batch(invalid)


def test_nullable_annuity_is_accepted(
    valid_batch: pd.DataFrame,
) -> None:
    """Permite valores ausentes na anuidade bruta."""
    batch = valid_batch.copy()
    batch.loc[0, "AMT_ANNUITY"] = float("nan")

    validated = validate_training_batch(batch)

    assert pd.isna(validated.loc[0, "AMT_ANNUITY"])


def test_inference_does_not_require_target(
    valid_batch: pd.DataFrame,
) -> None:
    """Aceita inferencia sem a coluna TARGET."""
    batch = valid_batch.drop(columns=["TARGET"])

    validated = validate_inference_batch(batch)

    assert len(validated) == 2
