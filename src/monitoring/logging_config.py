"""Configuração de logs estruturados em JSON para o Credit Scoring."""

import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    """Formata registros de log como objetos JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Converte um registro de log para JSON."""
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        for field in (
            "event",
            "status",
            "records",
            "pipeline",
            "error_type",
        ):
            if hasattr(record, field):
                payload[field] = getattr(record, field)

        return json.dumps(payload, ensure_ascii=False)


def configure_json_logging(
    logger_name: str = "credit_scoring",
) -> logging.Logger:
    """Configura um logger dedicado para observabilidade."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    return logger
