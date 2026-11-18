import pandas as pd
import pandera.pandas as pa
import pytest

from src.data import home_credit
from src.pipelines import prepare_data
from tests.unit.conftest import make_home_credit


@pytest.fixture
def raw_csv(tmp_path, monkeypatch):
    monkeypatch.setattr(home_credit.settings, "data_dir", tmp_path)
    monkeypatch.setattr(prepare_data.settings, "data_dir", tmp_path)
    (tmp_path / "raw").mkdir()
    path = tmp_path / "raw" / "application_train.csv"
    make_home_credit().to_csv(path, index=False)
    return path


def test_run_gera_referencia_e_producao_sem_sobreposicao(raw_csv, tmp_path):
    prepare_data.run(production_size=0.3)
    ref = pd.read_parquet(tmp_path / "processed" / "reference.parquet")
    prod = pd.read_parquet(tmp_path / "processed" / "production_base.parquet")
    assert len(ref) + len(prod) == 4000
    assert set(ref["SK_ID_CURR"]).isdisjoint(prod["SK_ID_CURR"])
    assert ref["TARGET"].mean() == pytest.approx(prod["TARGET"].mean(), abs=0.01)


def test_contrato_bloqueia_dados_invalidos(raw_csv, tmp_path):
    df = pd.read_csv(raw_csv)
    df.loc[0, "AMT_INCOME_TOTAL"] = -10.0
    df.to_csv(raw_csv, index=False)
    with pytest.raises(pa.errors.SchemaErrors):
        prepare_data.run()
    assert not (tmp_path / "processed").exists()


def test_csv_ausente_da_erro_claro(tmp_path, monkeypatch):
    monkeypatch.setattr(home_credit.settings, "data_dir", tmp_path)
    with pytest.raises(FileNotFoundError, match="application_train.csv"):
        home_credit.load_application_train()
