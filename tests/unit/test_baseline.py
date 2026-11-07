import numpy as np
import pytest
from sklearn.model_selection import train_test_split

from src.models import baseline
from src.models.baseline import build_pipeline, score
from src.training.train import (
    auc_by_group,
    best_f1_threshold,
    evaluate,
    ks_statistic,
    train,
)


@pytest.fixture
def trained(hc_df):
    return train(hc_df)


def test_baseline_tem_poder_de_separacao(trained):
    _, metrics, _ = trained
    assert metrics["auc"] > 0.65
    assert 0 < metrics["ks"] < 1
    assert 0 < metrics["threshold"] < 1


def test_metricas_de_vies_por_genero_e_idade(trained):
    _, _, fairness = trained
    assert any(k.startswith("auc_gender_") for k in fairness)
    assert "auc_gender_XNA" not in fairness


def test_score_retorna_probabilidades(trained, hc_df):
    pipeline, _, _ = trained
    proba = score(hc_df.head(50), model=pipeline)
    assert len(proba) == 50
    assert proba.between(0, 1).all()
    assert list(proba.index) == list(hc_df.head(50).index)


def test_categoria_desconhecida_nao_quebra(trained, hc_df):
    pipeline, _, _ = trained
    novo = hc_df.head(20).assign(NAME_INCOME_TYPE="Categoria nova")
    assert score(novo, model=pipeline).notna().all()


def test_modelo_nao_usa_genero(trained):
    pipeline, _, _ = trained
    names = pipeline.named_steps["xgb"].get_booster().feature_names
    assert "CODE_GENDER" not in names


def test_salvar_e_carregar_modelo(trained, hc_df, tmp_path, monkeypatch):
    pipeline, metrics, _ = trained
    monkeypatch.setattr(baseline.settings, "models_dir", tmp_path)
    baseline.save_model(pipeline, metrics)
    recarregado = baseline.load_model()
    assert np.allclose(
        score(hc_df.head(10), model=recarregado),
        score(hc_df.head(10), model=pipeline),
    )
    assert baseline.load_threshold() == pytest.approx(metrics["threshold"])


def test_metricas_auxiliares():
    y = np.array([0, 0, 0, 0, 1, 1, 1, 0, 1, 0])
    s = np.array([0.1, 0.2, 0.15, 0.3, 0.8, 0.7, 0.9, 0.4, 0.6, 0.05])
    import pandas as pd

    ys = pd.Series(y)
    assert ks_statistic(ys, s) == pytest.approx(1.0)
    assert 0.4 <= best_f1_threshold(ys, s) <= 0.6
    assert evaluate(ys, s, threshold=0.5)["f1"] == pytest.approx(1.0)


def test_grupos_pequenos_sao_ignorados(hc_df):
    import pandas as pd

    y = hc_df["TARGET"].head(100)
    s = pd.Series(np.random.default_rng(0).uniform(size=100), index=y.index)
    grupos = pd.Series(["a"] * 100, index=y.index)
    assert auc_by_group(y, s, grupos, "x") == {}


def test_pipeline_aceita_split_simples(hc_df):
    x = hc_df.drop(columns=["TARGET"])
    x_tr, x_te, y_tr, _ = train_test_split(
        x, hc_df["TARGET"], test_size=0.2, random_state=0
    )
    model = build_pipeline(0).fit(x_tr, y_tr)
    assert model.predict_proba(x_te).shape == (len(x_te), 2)
