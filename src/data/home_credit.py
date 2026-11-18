"""Carga do application_train do Home Credit e split referência/produção."""

import logging
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from src.features.build import RAW_COLUMNS, TARGET
from src.utils.config import settings

logger = logging.getLogger(__name__)

RAW_FILENAME = "application_train.csv"


def raw_path() -> Path:
    """Caminho esperado do CSV bruto em ``data/raw``."""
    return settings.data_dir / "raw" / RAW_FILENAME


def load_application_train() -> pd.DataFrame:
    """Lê apenas as colunas necessárias do ``application_train.csv``.

    Returns:
        DataFrame bruto com as colunas de ``RAW_COLUMNS``.

    Raises:
        FileNotFoundError: se o CSV não estiver em ``data/raw``.
    """
    path = raw_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} não encontrado. Baixe application_train.csv em "
            "https://www.kaggle.com/competitions/home-credit-default-risk/data"
        )
    return pd.read_csv(path, usecols=RAW_COLUMNS)


def split_reference_production(
    df: pd.DataFrame, production_size: float, seed: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa referência (treino) e base de produção, estratificando o target."""
    reference, production = train_test_split(
        df, test_size=production_size, stratify=df[TARGET], random_state=seed
    )
    return reference.sort_index(), production.sort_index()
