"""Simulação controlada de Data Drift no Home Credit."""

import numpy as np
import pandas as pd


def simulate_income_credit_drift(
    data: pd.DataFrame,
    fraction: float = 0.60,
    income_multiplier: float = 1.40,
    credit_multiplier: float = 1.30,
    seed: int = 42,
) -> pd.DataFrame:
    """Simula mudanças em renda e crédito sem alterar os dados originais."""
    required = {"AMT_INCOME_TOTAL", "AMT_CREDIT"}
    missing = required - set(data.columns)

    if missing:
        raise ValueError(f"Colunas ausentes: {sorted(missing)}")

    if data.empty:
        raise ValueError("O dataset não pode estar vazio.")

    if not 0 < fraction <= 1:
        raise ValueError("fraction deve estar entre 0 e 1.")

    if income_multiplier <= 1 or credit_multiplier <= 1:
        raise ValueError("Os multiplicadores devem ser maiores que 1.")

    drifted = data.copy(deep=True)

    rng = np.random.default_rng(seed)
    quantity = max(1, int(len(data) * fraction))

    positions = rng.choice(
        len(data),
        size=quantity,
        replace=False,
    )

    for column, multiplier in (
        ("AMT_INCOME_TOTAL", income_multiplier),
        ("AMT_CREDIT", credit_multiplier),
    ):
        col_idx = drifted.columns.get_loc(column)
        values = drifted.iloc[positions, col_idx].to_numpy()
        drifted.iloc[positions, col_idx] = values * multiplier

    return drifted
