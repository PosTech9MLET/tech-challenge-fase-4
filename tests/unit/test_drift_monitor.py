"""Testes para extração de alertas do Evidently."""

import json

import pytest

from src.pipelines.drift_monitor import extract_psi_alerts


@pytest.mark.parametrize(
    ("psi", "expected_alert"),
    [
        (0.05, False),
        (0.20, True),
        (0.35, True),
    ],
)
def test_psi_alerts(tmp_path, psi, expected_alert):
    """Verifica a classificação do PSI pelo limiar."""
    report = {
        "metrics": [
            {
                "config": {
                    "type": "evidently:metric_v2:ValueDrift",
                    "column": "AMT_INCOME_TOTAL",
                    "threshold": 0.20,
                },
                "value": psi,
            }
        ]
    }

    path = tmp_path / "report.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    results = extract_psi_alerts(path)

    assert results["AMT_INCOME_TOTAL"]["psi"] == psi
    assert results["AMT_INCOME_TOTAL"]["alert"] is expected_alert


def test_report_without_psi_is_rejected(tmp_path):
    """Relatórios sem métricas de drift devem ser rejeitados."""
    path = tmp_path / "empty.json"
    path.write_text('{"metrics": []}', encoding="utf-8")

    with pytest.raises(ValueError, match="Nenhuma métrica"):
        extract_psi_alerts(path)
