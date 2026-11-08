"""Detecção de Data Drift com Evidently."""

import json
from pathlib import Path

import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

DRIFT_COLUMNS = [
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
]

PSI_THRESHOLD = 0.2
SAMPLE_SIZE = 5000
RANDOM_SEED = 42


def generate_drift_report(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    output: Path,
) -> None:
    """Compara distribuições e gera relatórios HTML e JSON."""
    for name, df in (
        ("referência", reference),
        ("produção", current),
    ):
        missing = set(DRIFT_COLUMNS) - set(df.columns)

        if missing:
            raise ValueError(f"Colunas ausentes em {name}: {sorted(missing)}")

        if df.empty:
            raise ValueError(f"Dataset vazio: {name}")

    reference_sample = reference[DRIFT_COLUMNS].sample(
        n=min(SAMPLE_SIZE, len(reference)),
        random_state=RANDOM_SEED,
    )

    current_sample = current[DRIFT_COLUMNS].sample(
        n=min(SAMPLE_SIZE, len(current)),
        random_state=RANDOM_SEED,
    )

    report = Report(
        [
            DataDriftPreset(
                columns=DRIFT_COLUMNS,
                method="psi",
                threshold=PSI_THRESHOLD,
            )
        ]
    )

    snapshot = report.run(
        current_data=current_sample,
        reference_data=reference_sample,
    )

    output.parent.mkdir(parents=True, exist_ok=True)

    snapshot.save_html(str(output))

    json_path = output.with_suffix(".json")
    json_path.write_text(
        snapshot.json(),
        encoding="utf-8",
    )


def extract_psi_alerts(
    report_path: Path,
) -> dict[str, dict[str, float | bool]]:
    """Extrai métricas de PSI e classifica os alertas."""
    data = json.loads(report_path.read_text(encoding="utf-8"))
    results = {}

    for metric in data.get("metrics", []):
        config = metric.get("config", {})

        if not config.get("type", "").endswith(":ValueDrift"):
            continue

        column = config["column"]
        psi = float(metric["value"])
        threshold = float(config["threshold"])

        results[column] = {
            "psi": psi,
            "threshold": threshold,
            "alert": psi >= threshold,
        }

    if not results:
        raise ValueError("Nenhuma métrica de PSI encontrada no relatório.")

    return results
