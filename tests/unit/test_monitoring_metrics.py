"""Testes das metricas operacionais com Prometheus."""

import pytest
from prometheus_client import CollectorRegistry

from src.monitoring.metrics import (
    build_metrics,
    observe_pipeline,
    record_psi,
)


def test_pipeline_success_is_recorded():
    """Registra uma execucao bem-sucedida e sua duracao."""
    registry = CollectorRegistry()
    metrics = build_metrics(registry)

    with observe_pipeline("prepare_data", metrics):
        total = 2 + 2

    assert total == 4

    assert (
        registry.get_sample_value(
            "credit_pipeline_runs_total",
            {"pipeline": "prepare_data", "status": "success"},
        )
        == 1
    )

    assert (
        registry.get_sample_value(
            "credit_pipeline_duration_seconds_count",
            {"pipeline": "prepare_data"},
        )
        == 1
    )


def test_pipeline_error_is_recorded():
    """Registra falhas sem esconder a excecao original."""
    registry = CollectorRegistry()
    metrics = build_metrics(registry)

    with (
        pytest.raises(ValueError, match="Lote invalido"),
        observe_pipeline("data_validation", metrics),
    ):
        raise ValueError("Lote invalido")

    assert (
        registry.get_sample_value(
            "credit_pipeline_runs_total",
            {"pipeline": "data_validation", "status": "error"},
        )
        == 1
    )


def test_psi_is_recorded():
    """Armazena o PSI por variavel monitorada."""
    registry = CollectorRegistry()
    metrics = build_metrics(registry)

    record_psi("AMT_INCOME_TOTAL", 0.6733, metrics)
    record_psi("AMT_CREDIT", 0.4521, metrics)

    assert registry.get_sample_value(
        "credit_data_drift_psi",
        {"feature": "AMT_INCOME_TOTAL"},
    ) == pytest.approx(0.6733)

    assert registry.get_sample_value(
        "credit_data_drift_psi",
        {"feature": "AMT_CREDIT"},
    ) == pytest.approx(0.4521)


def test_invalid_psi_is_rejected():
    """Nao permite registrar PSI negativo."""
    metrics = build_metrics(CollectorRegistry())

    with pytest.raises(ValueError, match="PSI"):
        record_psi("AMT_CREDIT", -1.0, metrics)
