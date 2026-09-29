"""Smoke tests: garantem que o projeto importa e a config carrega."""

from src.utils.config import settings


def test_settings_carrega():
    assert settings.random_seed == 42
    assert settings.data_dir.name == "data"
