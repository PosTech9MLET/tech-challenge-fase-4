"""Testes da simulação de Data Drift."""

import numpy as np
import pandas as pd
import pytest

from src.data.contracts import validate_training_batch
from src.data.simulate_drift import simulate_income_credit_drift


def test_simulation_changes_income_and_credit(hc_df: pd.DataFrame) -> None:
    """Verifica mudanças nas duas variáveis selecionadas."""
    original = hc_df.head(20).copy()
    drifted = simulate_income_credit_drift(original)

    changed = drifted["AMT_INCOME_TOTAL"].ne(original["AMT_INCOME_TOTAL"])

    assert changed.sum() == 12

    np.testing.assert_allclose(
        drifted.loc[changed, "AMT_INCOME_TOTAL"],
        original.loc[changed, "AMT_INCOME_TOTAL"] * 1.40,
    )

    np.testing.assert_allclose(
        drifted.loc[changed, "AMT_CREDIT"],
        original.loc[changed, "AMT_CREDIT"] * 1.30,
    )

    pd.testing.assert_series_equal(drifted["SK_ID_CURR"], original["SK_ID_CURR"])

    pd.testing.assert_series_equal(drifted["TARGET"], original["TARGET"])

    validate_training_batch(drifted)


def test_simulation_is_reproducible(hc_df: pd.DataFrame) -> None:
    """A mesma semente deve produzir o mesmo resultado."""
    original = hc_df.head(20).copy()
    snapshot = original.copy(deep=True)

    first = simulate_income_credit_drift(original, seed=42)
    second = simulate_income_credit_drift(original, seed=42)

    pd.testing.assert_frame_equal(first, second)
    pd.testing.assert_frame_equal(original, snapshot)


@pytest.mark.parametrize("fraction", [0, -0.1, 1.5])
def test_invalid_fraction_is_rejected(hc_df: pd.DataFrame, fraction: float) -> None:
    """Rejeita proporções inválidas de registros."""
    with pytest.raises(ValueError, match="fraction"):
        simulate_income_credit_drift(hc_df.head(20), fraction=fraction)
