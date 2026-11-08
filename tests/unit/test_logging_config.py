"""Testes da configuração de logs estruturados."""

import json
import logging

from src.monitoring.logging_config import JsonFormatter


def test_json_formatter():
    """Verifica se o log JSON contém os campos esperados."""
    logger = logging.getLogger("test_logging")

    record = logger.makeRecord(
        name="test_logging",
        level=logging.INFO,
        fn="test.py",
        lno=1,
        msg="Validação concluída",
        args=(),
        exc_info=None,
        extra={
            "event": "data_validation",
            "status": "approved",
            "records": 5000,
            "pipeline": "home_credit",
        },
    )

    result = json.loads(JsonFormatter().format(record))

    assert result["level"] == "INFO"
    assert result["event"] == "data_validation"
    assert result["status"] == "approved"
    assert result["records"] == 5000
    assert result["pipeline"] == "home_credit"
    assert result["message"] == "Validação concluída"
    assert "timestamp" in result
