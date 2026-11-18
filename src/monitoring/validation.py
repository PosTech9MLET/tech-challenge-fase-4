"""Observabilidade da validação de dados com Pandera."""

import logging

import pandas as pd
from pandera.errors import SchemaError, SchemaErrors

from src.data.contracts import validate_training_batch
from src.monitoring.logging_config import configure_json_logging
from src.monitoring.metrics import (
    METRICS,
    MonitoringMetrics,
    observe_pipeline,
)


def validate_training_with_monitoring(
    batch: pd.DataFrame,
    *,
    metrics: MonitoringMetrics = METRICS,
    logger: logging.Logger | None = None,
) -> None:
    """Valida um lote e registra logs e métricas operacionais."""
    audit_logger = logger if logger is not None else configure_json_logging()

    context = {
        "event": "data_validation",
        "pipeline": "home_credit",
        "records": len(batch),
    }

    with observe_pipeline("data_validation", metrics):
        try:
            validate_training_batch(batch)

        except (SchemaError, SchemaErrors) as exc:
            audit_logger.warning(
                "Lote rejeitado pelo contrato Pandera",
                extra={
                    **context,
                    "status": "rejected",
                    "error_type": type(exc).__name__,
                },
            )
            raise

        except Exception as exc:
            audit_logger.error(
                "Erro inesperado na validacao",
                extra={
                    **context,
                    "status": "error",
                    "error_type": type(exc).__name__,
                },
            )
            raise

        else:
            audit_logger.info(
                "Lote aprovado",
                extra={
                    **context,
                    "status": "approved",
                },
            )
