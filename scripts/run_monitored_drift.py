"""Executa validação e Data Drift com métricas Prometheus."""

import json

from prometheus_client import CollectorRegistry, write_to_textfile

from scripts.run_drift import REPORT_DIR
from scripts.run_drift import main as run_drift_main
from src.data.home_credit import load_application_train
from src.monitoring.metrics import build_metrics, observe_pipeline, record_psi
from src.monitoring.validation import validate_training_with_monitoring


def main() -> None:
    """Valida os dados, monitora drift e exporta métricas."""
    registry = CollectorRegistry()
    metrics = build_metrics(registry)
    output = REPORT_DIR / "operational_metrics.prom"

    try:
        with observe_pipeline("data_loading", metrics):
            data = load_application_train()

        validate_training_with_monitoring(data, metrics=metrics)

        with observe_pipeline("drift_monitor", metrics):
            run_drift_main()

            report_path = REPORT_DIR / "drift_alerts.json"
            alerts = json.loads(report_path.read_text(encoding="utf-8"))

            for feature, result in alerts["simulated"].items():
                record_psi(
                    feature,
                    float(result["psi"]),
                    metrics,
                )

    finally:
        output.parent.mkdir(parents=True, exist_ok=True)
        write_to_textfile(str(output), registry)

    print("\n=== MÉTRICAS OPERACIONAIS ===")
    print(f"Arquivo Prometheus gerado: {output}")


if __name__ == "__main__":
    main()
