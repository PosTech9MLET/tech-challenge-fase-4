"""Engenharia de atributos do Home Credit (transformações sem estado)."""

import numpy as np
import pandas as pd

TARGET = "TARGET"
ID_COLUMN = "SK_ID_CURR"
# Usado apenas na análise de viés; NÃO é feature do modelo.
GENDER = "CODE_GENDER"

DAYS_EMPLOYED_SENTINEL = 365243

CATEGORICAL = [
    "NAME_CONTRACT_TYPE",
    "FLAG_OWN_CAR",
    "FLAG_OWN_REALTY",
    "NAME_INCOME_TYPE",
    "NAME_EDUCATION_TYPE",
    "NAME_FAMILY_STATUS",
    "NAME_HOUSING_TYPE",
    "OCCUPATION_TYPE",
]
NUMERIC_RAW = [
    "CNT_CHILDREN",
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "AMT_GOODS_PRICE",
    "DAYS_EMPLOYED",
    "DAYS_REGISTRATION",
    "DAYS_ID_PUBLISH",
    "DAYS_LAST_PHONE_CHANGE",
    "CNT_FAM_MEMBERS",
    "REGION_RATING_CLIENT",
    "REGION_POPULATION_RELATIVE",
    "EXT_SOURCE_1",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3",
]
DERIVED = [
    "AGE_YEARS",
    "CREDIT_INCOME_RATIO",
    "ANNUITY_INCOME_RATIO",
    "CREDIT_TERM",
    "EMPLOYED_RATIO",
]
NUMERIC = [*NUMERIC_RAW, *DERIVED]
MODEL_FEATURES = [*CATEGORICAL, *NUMERIC]

# Colunas lidas do CSV bruto e persistidas em referência/produção.
RAW_COLUMNS = [
    ID_COLUMN,
    TARGET,
    GENDER,
    "DAYS_BIRTH",
    *CATEGORICAL,
    *NUMERIC_RAW,
]


def build_features(raw: pd.DataFrame) -> pd.DataFrame:
    """Transforma colunas brutas nas features do modelo.

    Aplica o tratamento do código sentinela de ``DAYS_EMPLOYED`` e cria razões
    financeiras. É uma função pura (sem estado aprendido), portanto segura
    para treino e inferência. Alterações simuladas em colunas brutas (ex.:
    renda) propagam-se para as razões derivadas.

    Args:
        raw: DataFrame com as colunas brutas (``RAW_COLUMNS`` sem o target).

    Returns:
        DataFrame com exatamente as colunas de ``MODEL_FEATURES``.
    """
    out = raw.copy()
    out["DAYS_EMPLOYED"] = out["DAYS_EMPLOYED"].replace(DAYS_EMPLOYED_SENTINEL, np.nan)
    out["AGE_YEARS"] = -out["DAYS_BIRTH"] / 365.25
    out["CREDIT_INCOME_RATIO"] = out["AMT_CREDIT"] / out["AMT_INCOME_TOTAL"]
    out["ANNUITY_INCOME_RATIO"] = out["AMT_ANNUITY"] / out["AMT_INCOME_TOTAL"]
    out["CREDIT_TERM"] = out["AMT_ANNUITY"] / out["AMT_CREDIT"]
    out["EMPLOYED_RATIO"] = out["DAYS_EMPLOYED"] / out["DAYS_BIRTH"]
    out[DERIVED] = out[DERIVED].replace([np.inf, -np.inf], np.nan)
    return out[MODEL_FEATURES]
