"""Pipeline de preparação: bruto → contrato → referência e produção."""

import logging

from src.data.contracts import validate_training_batch
from src.data.home_credit import load_application_train, split_reference_production
from src.utils.config import settings

logger = logging.getLogger(__name__)

REFERENCE_FILE = "reference.parquet"
PRODUCTION_FILE = "production_base.parquet"


def run(production_size: float = 0.3) -> None:
    """Valida o dataset bruto e grava referência (70%) e produção (30%).

    As colunas persistidas são brutas: a engenharia de atributos faz parte do
    pipeline do modelo, para que alterações simuladas nos dados de produção se
    propaguem às features derivadas.

    Raises:
        pandera.errors.SchemaErrors: se o contrato de dados for violado
            (a ingestão é bloqueada e nada é gravado).
    """
    raw = load_application_train()
    validate_training_batch(raw)
    reference, production = split_reference_production(
        raw, production_size, settings.random_seed
    )
    out_dir = settings.data_dir / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    reference.to_parquet(out_dir / REFERENCE_FILE)
    production.to_parquet(out_dir / PRODUCTION_FILE)
    logger.info(
        "Referência=%d linhas, produção=%d linhas (%s)",
        len(reference),
        len(production),
        out_dir,
    )


if __name__ == "__main__":
    logging.basicConfig(level=settings.log_level)
    run()
