"""Testes da comparação de scores antes e depois do drift."""

import numpy as np
import pandas as pd
import pytest

from src.pipelines.score_impact import compare_prediction_scores


class FakeModel:
    """Modelo simples para testar o cálculo sem treinar XGBoost."""

    def predict_proba(self, data):
        assert "TARGET" not in data.columns
        probabilities = data["AMT_CREDIT"].to_numpy() / 1000
        return np.column_stack([1 - probabilities, probabilities])


@pytest.fixture
def sample_frames():
    production = pd.DataFrame(
        {
            "SK_ID_CURR": [100, 101],
            "AMT_CREDIT": [100.0, 300.0],
            "TARGET": [0, 1],
        }
    )

    # Ordem propositalmente invertida para testar alinhamento por ID.
    drifted = pd.DataFrame(
        {
            "SK_ID_CURR": [101, 100],
            "AMT_CREDIT": [800.0, 200.0],
            "TARGET": [1, 0],
        }
    )

    return production, drifted


def test_scores_are_aligned_by_id(sample_frames):
    production, drifted = sample_frames

    comparison, summary = compare_prediction_scores(
        production,
        drifted,
        FakeModel(),
        threshold=0.5,
    )

    comparison = comparison.set_index("SK_ID_CURR")

    assert comparison.loc[100, "score_before"] == pytest.approx(0.1)
    assert comparison.loc[100, "score_after"] == pytest.approx(0.2)
    assert comparison.loc[101, "score_before"] == pytest.approx(0.3)
    assert comparison.loc[101, "score_after"] == pytest.approx(0.8)

    assert summary["changed_decisions"] == 1
    assert summary["changed_decisions_pct"] == pytest.approx(50.0)


def test_mismatched_ids_are_rejected(sample_frames):
    production, drifted = sample_frames
    drifted.loc[0, "SK_ID_CURR"] = 999

    with pytest.raises(ValueError, match="mesmos clientes"):
        compare_prediction_scores(production, drifted, FakeModel(), 0.5)


def test_duplicated_ids_are_rejected(sample_frames):
    production, drifted = sample_frames
    production.loc[1, "SK_ID_CURR"] = 100

    with pytest.raises(ValueError, match="duplicados"):
        compare_prediction_scores(production, drifted, FakeModel(), 0.5)


def test_invalid_threshold_is_rejected(sample_frames):
    production, drifted = sample_frames

    with pytest.raises(ValueError, match="threshold"):
        compare_prediction_scores(production, drifted, FakeModel(), 1.5)
