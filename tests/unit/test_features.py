import numpy as np

from src.features.build import GENDER, MODEL_FEATURES, build_features


def test_build_features_devolve_apenas_colunas_do_modelo(hc_df):
    out = build_features(hc_df.drop(columns=["TARGET"]))
    assert list(out.columns) == MODEL_FEATURES
    assert GENDER not in out.columns
    assert "SK_ID_CURR" not in out.columns


def test_sentinela_de_dias_empregado_vira_nulo(hc_df):
    out = build_features(hc_df)
    assert (out["DAYS_EMPLOYED"] != 365243).all()
    assert out["DAYS_EMPLOYED"].isna().any()


def test_razoes_financeiras(hc_df):
    out = build_features(hc_df)
    esperado = hc_df["AMT_CREDIT"] / hc_df["AMT_INCOME_TOTAL"]
    assert np.allclose(out["CREDIT_INCOME_RATIO"], esperado)
    assert (out["AGE_YEARS"] > 18).all()


def test_alterar_renda_propaga_para_razoes(hc_df):
    antes = build_features(hc_df)["CREDIT_INCOME_RATIO"]
    drift = hc_df.assign(AMT_INCOME_TOTAL=hc_df["AMT_INCOME_TOTAL"] * 2)
    depois = build_features(drift)["CREDIT_INCOME_RATIO"]
    assert np.allclose(depois, antes / 2)


def test_divisao_por_zero_vira_nulo(hc_df):
    df = hc_df.copy()
    df.loc[df.index[0], "AMT_INCOME_TOTAL"] = 0.0
    out = build_features(df)
    assert np.isnan(out["CREDIT_INCOME_RATIO"].iloc[0])
