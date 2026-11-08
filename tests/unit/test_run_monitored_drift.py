"""Testes da execução monitorada do Data Drift."""

import pytest
from pandera.errors import SchemaErrors

from scripts import run_monitored_drift


def test_monitored_drift_exports_metrics(tmp_path, monkeypatch, hc_df):
    """Verifica a exportação das métricas de execução e PSI."""
    monkeypatch.setattr(
        run_monitored_drift,
        "REPORT_DIR",
        tmp_path,
    )

    monkeypatch.setattr(
        run_monitored_drift,
        "load_application_train",
        lambda: hc_df.head(10).copy(),
    )

    def fake_run():
        """Simula a geração do relatório de Data Drift."""
        (tmp_path / "drift_alerts.json").write_text(
            '{"simulated": {"AMT_CREDIT": {"psi": 0.4521}}}\n',
            encoding="utf-8",
        )

    monkeypatch.setattr(
        run_monitored_drift,
        "run_drift_main",
        fake_run,
    )

    run_monitored_drift.main()

    content = (tmp_path / "operational_metrics.prom").read_text(encoding="utf-8")

    # Verifica a execução bem-sucedida dos pipelines.
    assert (
        'credit_pipeline_runs_total{pipeline="data_loading",status="success"} 1.0'
    ) in content

    assert (
        'credit_pipeline_runs_total{pipeline="data_validation",status="success"} 1.0'
    ) in content

    assert (
        'credit_pipeline_runs_total{pipeline="drift_monitor",status="success"} 1.0'
    ) in content

    # Verifica o registro de duração.
    assert "credit_pipeline_duration_seconds" in content

    # Verifica o PSI exportado.
    assert ('credit_data_drift_psi{feature="AMT_CREDIT"} 0.4521') in content


def test_monitored_drift_exports_failure(tmp_path, monkeypatch, hc_df):
    """Verifica o registro de falhas no monitoramento."""
    monkeypatch.setattr(
        run_monitored_drift,
        "REPORT_DIR",
        tmp_path,
    )

    monkeypatch.setattr(
        run_monitored_drift,
        "load_application_train",
        lambda: hc_df.head(10).copy(),
    )

    def fake_run():
        """Simula uma falha durante o monitoramento."""
        raise RuntimeError("Falha simulada")

    monkeypatch.setattr(
        run_monitored_drift,
        "run_drift_main",
        fake_run,
    )

    with pytest.raises(RuntimeError, match="Falha simulada"):
        run_monitored_drift.main()

    content = (tmp_path / "operational_metrics.prom").read_text(encoding="utf-8")

    # Os dados foram carregados e validados corretamente.
    assert (
        'credit_pipeline_runs_total{pipeline="data_validation",status="success"} 1.0'
    ) in content

    # O monitoramento de drift falhou.
    assert (
        'credit_pipeline_runs_total{pipeline="drift_monitor",status="error"} 1.0'
    ) in content

    # As métricas foram exportadas mesmo após a falha.
    assert "credit_pipeline_duration_seconds" in content


def test_invalid_batch_blocks_drift(tmp_path, monkeypatch, hc_df):
    """Impede que dados inválidos avancem para o Data Drift."""
    monkeypatch.setattr(
        run_monitored_drift,
        "REPORT_DIR",
        tmp_path,
    )

    # Cria um lote com valor de crédito inválido.
    invalid = hc_df.head(10).copy()
    invalid.loc[invalid.index[0], "AMT_CREDIT"] = 0.0

    monkeypatch.setattr(
        run_monitored_drift,
        "load_application_train",
        lambda: invalid,
    )

    def forbidden_drift_run():
        """Falha se o monitoramento for executado indevidamente."""
        pytest.fail("O drift nao deveria executar com dados invalidos")

    monkeypatch.setattr(
        run_monitored_drift,
        "run_drift_main",
        forbidden_drift_run,
    )

    # O Pandera deve bloquear o lote inválido.
    with pytest.raises(SchemaErrors):
        run_monitored_drift.main()

    content = (tmp_path / "operational_metrics.prom").read_text(encoding="utf-8")

    # O carregamento foi bem-sucedido.
    assert (
        'credit_pipeline_runs_total{pipeline="data_loading",status="success"} 1.0'
    ) in content

    # A validação deve registrar o erro.
    assert (
        'credit_pipeline_runs_total{pipeline="data_validation",status="error"} 1.0'
    ) in content

    # O monitoramento de drift não deve ser executado.
    assert 'pipeline="drift_monitor"' not in content
