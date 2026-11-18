import numpy as np
import pandas as pd
import pytest

from src.features.build import CATEGORICAL, RAW_COLUMNS


def make_home_credit(n: int = 4000, seed: int = 0) -> pd.DataFrame:
    """Gera dados sintéticos no formato do application_train (sem dados reais)."""
    rng = np.random.default_rng(seed)
    ext = rng.uniform(0.05, 0.95, (n, 3))
    income = rng.lognormal(12, 0.5, n).round(2)
    credit = (income * rng.uniform(1, 6, n)).round(2)
    logit = -2.4 - 5.0 * (ext[:, 1] - 0.5) - 3.0 * (ext[:, 2] - 0.5)
    target = (rng.uniform(size=n) < 1 / (1 + np.exp(-logit))).astype(int)
    df = pd.DataFrame(
        {
            "SK_ID_CURR": np.arange(100_000, 100_000 + n),
            "TARGET": target,
            "CODE_GENDER": rng.choice(["F", "M", "XNA"], n, p=[0.64, 0.35, 0.01]),
            "DAYS_BIRTH": -rng.integers(7_000, 24_000, n),
            "CNT_CHILDREN": rng.integers(0, 4, n),
            "AMT_INCOME_TOTAL": income,
            "AMT_CREDIT": credit,
            "AMT_ANNUITY": (credit / rng.uniform(10, 30, n)).round(2),
            "AMT_GOODS_PRICE": (credit * 0.9).round(2),
            "DAYS_EMPLOYED": -rng.integers(0, 10_000, n),
            "DAYS_REGISTRATION": -rng.integers(0, 15_000, n).astype(float),
            "DAYS_ID_PUBLISH": -rng.integers(0, 6_000, n),
            "DAYS_LAST_PHONE_CHANGE": -rng.integers(0, 3_000, n).astype(float),
            "CNT_FAM_MEMBERS": rng.integers(1, 6, n).astype(float),
            "REGION_RATING_CLIENT": rng.integers(1, 4, n),
            "REGION_POPULATION_RELATIVE": rng.uniform(0.001, 0.07, n),
            "EXT_SOURCE_1": ext[:, 0],
            "EXT_SOURCE_2": ext[:, 1],
            "EXT_SOURCE_3": ext[:, 2],
        }
    )
    df.loc[rng.choice(n, n // 6, replace=False), "DAYS_EMPLOYED"] = 365243
    df.loc[rng.choice(n, n // 3, replace=False), "EXT_SOURCE_1"] = np.nan
    df.loc[rng.choice(n, 20, replace=False), "AMT_ANNUITY"] = np.nan
    choices = {
        "NAME_CONTRACT_TYPE": ["Cash loans", "Revolving loans"],
        "FLAG_OWN_CAR": ["Y", "N"],
        "FLAG_OWN_REALTY": ["Y", "N"],
        "NAME_INCOME_TYPE": ["Working", "Pensioner", "State servant"],
        "NAME_EDUCATION_TYPE": ["Higher education", "Secondary / secondary special"],
        "NAME_FAMILY_STATUS": ["Married", "Single / not married"],
        "NAME_HOUSING_TYPE": ["House / apartment", "With parents"],
        "OCCUPATION_TYPE": ["Laborers", "Core staff", "Managers"],
    }
    for col in CATEGORICAL:
        df[col] = rng.choice(choices[col], n)
    df.loc[rng.choice(n, n // 4, replace=False), "OCCUPATION_TYPE"] = np.nan
    return df[RAW_COLUMNS]


@pytest.fixture
def hc_df() -> pd.DataFrame:
    return make_home_credit()
