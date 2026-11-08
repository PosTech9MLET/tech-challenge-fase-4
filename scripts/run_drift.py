"""Gera relatórios e alertas de Data Drift do Home Credit."""

import json
from pathlib import Path

import pandas as pd

from src.pipelines.drift_monitor import (
    extract_psi_alerts,
    generate_drift_report,
)
from src.pipelines.prepare_data import (
    PRODUCTION_FILE,
    REFERENCE_FILE,
)
from src.utils.config import settings

DRIFT_FILE = "production_drift.parquet"
REPORT_DIR = Path(__file__).resolve().parents[1] / "reports"


def main() -> None:
    """Compara os cenários e registra alertas de Data Drift."""
    data_dir = settings.data_dir / "processed"

    reference = pd.read_parquet(data_dir / REFERENCE_FILE)
    production = pd.read_parquet(data_dir / PRODUCTION_FILE)
    drifted = pd.read_parquet(data_dir / DRIFT_FILE)

    baseline_report = REPORT_DIR / "drift_baseline.html"
    simulated_report = REPORT_DIR / "drift_simulated.html"

    generate_drift_report(reference, production, baseline_report)
    generate_drift_report(reference, drifted, simulated_report)

    results = {
        "baseline": extract_psi_alerts(baseline_report.with_suffix(".json")),
        "simulated": extract_psi_alerts(simulated_report.with_suffix(".json")),
    }

    print("=== MONITORAMENTO DE DATA DRIFT ===")

    for scenario, columns in results.items():
        print(f"\nCenário: {scenario}")

        for column, metric in columns.items():
            status = "ALERTA: DRIFT DETECTADO" if metric["alert"] else "SEM ALERTA"
            print(f"{column}: PSI={metric['psi']:.4f} | {status}")

    output = REPORT_DIR / "drift_alerts.json"
    output.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nAlertas registrados em: {output}")


if __name__ == "__main__":
    main()
