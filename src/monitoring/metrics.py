"""Métricas operacionais dos pipelines de Credit Scoring."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from math import isfinite
from time import perf_counter

from prometheus_client import (
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
)


@dataclass(frozen=True)
class MonitoringMetrics:
    """Agrupa os indicadores operacionais do projeto."""

    runs: Counter
    duration: Histogram
    drift_psi: Gauge


def build_metrics(
    registry: CollectorRegistry | None = None,
) -> MonitoringMetrics:
    """Cria as métricas, permitindo um registro isolado para testes."""
    target = REGISTRY if registry is None else registry

    return MonitoringMetrics(
        runs=Counter(
            "credit_pipeline_runs_total",
            "Total de execucoes por pipeline e resultado.",
            ["pipeline", "status"],
            registry=target,
        ),
        duration=Histogram(
            "credit_pipeline_duration_seconds",
            "Duracao das execucoes em segundos.",
            ["pipeline"],
            registry=target,
        ),
        drift_psi=Gauge(
            "credit_data_drift_psi",
            "Valor do PSI por variavel monitorada.",
            ["feature"],
            registry=target,
        ),
    )


METRICS = build_metrics()


@contextmanager
def observe_pipeline(
    pipeline: str,
    metrics: MonitoringMetrics = METRICS,
) -> Iterator[None]:
    """Registra duracao e sucesso ou erro de uma execucao."""
    started = perf_counter()
    status = "success"

    try:
        yield
    except Exception:
        status = "error"
        raise
    finally:
        elapsed = perf_counter() - started

        metrics.runs.labels(
            pipeline=pipeline,
            status=status,
        ).inc()

        metrics.duration.labels(
            pipeline=pipeline,
        ).observe(elapsed)


def record_psi(
    feature: str,
    value: float,
    metrics: MonitoringMetrics = METRICS,
) -> None:
    """Atualiza o PSI mais recente de uma variavel."""
    if not isfinite(value) or value < 0:
        raise ValueError("PSI deve ser finito e nao negativo.")

    metrics.drift_psi.labels(feature=feature).set(value)
