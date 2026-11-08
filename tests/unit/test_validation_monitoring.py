"""Testes da observabilidade da validação Pandera."""

import logging

import pandas as pd
import pytest
from pandera.errors import SchemaErrors
from prometheus_client import CollectorRegistry

from src.monitoring.metrics import build_metrics
from src.monitoring.validation import validate_training_with_monitoring


def test_valid_batch_is_monitored(
    hc_df: pd.DataFrame,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Registra sucesso, quantidade de linhas e métrica."""
    registry = CollectorRegistry()
    metrics = build_metrics(registry)
    logger = logging.getLogger("test.validation")

    with caplog.at_level(logging.INFO, logger="test.validation"):
        validate_training_with_monitoring(
            hc_df.head(10),
            metrics=metrics,
            logger=logger,
        )

    assert any(
        getattr(record, "status", None) == "approved"
        and getattr(record, "records", None) == 10
        for record in caplog.records
    )

    assert (
        registry.get_sample_value(
            "credit_pipeline_runs_total",
            {"pipeline": "data_validation", "status": "success"},
        )
        == 1
    )


def test_invalid_batch_is_monitored(
    hc_df: pd.DataFrame,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Registra rejeição e preserva o bloqueio do Pandera."""
    registry = CollectorRegistry()
    metrics = build_metrics(registry)
    logger = logging.getLogger("test.validation")

    invalid = hc_df.head(10).copy()
    invalid.loc[invalid.index[0], "AMT_CREDIT"] = 0.0

    with (
        caplog.at_level(logging.WARNING, logger="test.validation"),
        pytest.raises(SchemaErrors),
    ):
        validate_training_with_monitoring(
            invalid,
            metrics=metrics,
            logger=logger,
        )

    assert any(
        getattr(record, "status", None) == "rejected"
        and getattr(record, "records", None) == 10
        and getattr(record, "error_type", None) == "SchemaErrors"
        for record in caplog.records
    )

    assert (
        registry.get_sample_value(
            "credit_pipeline_runs_total",
            {"pipeline": "data_validation", "status": "error"},
        )
        == 1
    )
