"""Tests for EnsembleBlend: the model that actually uses the GA's tuned
blend weights, rather than leaving them recorded but unused."""

from __future__ import annotations

import pandas as pd
import pytest

from dengue import config
from dengue.eval.backtest import rolling_origin
from dengue.models import PREDICTION_COLUMNS
from dengue.models.ensemble import _EQUAL_WEIGHTS, EnsembleBlend
from dengue.utils.synthetic import make_synthetic_panel


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return make_synthetic_panel(n_districts=4, n_weeks=150, seed=23)


def test_equal_weights_sum_to_one():
    assert sum(_EQUAL_WEIGHTS.values()) == pytest.approx(1.0)


def test_fit_predict_returns_prediction_columns_and_monotonic_quantiles(panel):
    model = EnsembleBlend(horizons=(2,))
    model.fit(panel)
    predictions = model.predict(panel, horizon=2)

    assert not predictions.empty
    assert list(predictions.columns) == list(PREDICTION_COLUMNS)
    assert (predictions["q0.1"] <= predictions["q0.5"]).all()
    assert (predictions["q0.5"] <= predictions["q0.9"]).all()


def test_predict_before_fit_raises(panel):
    model = EnsembleBlend(horizons=(2,))
    with pytest.raises(RuntimeError, match="must be fitted"):
        model.predict(panel, horizon=2)


def test_explicit_weights_are_used_verbatim(panel):
    model = EnsembleBlend(horizons=(2,), weights={"w_naive": 1.0, "w_sarima": 0.0, "w_lgbm": 0.0})
    model.fit(panel)
    blended = model.predict(panel, horizon=2)

    naive_only = model._models["w_naive"].predict(panel, horizon=2)
    merged = blended.merge(
        naive_only,
        on=["district_id", "iso_week", "target_week", "horizon"],
        suffixes=("", "_naive"),
    )
    assert (merged["q0.5"] == merged["q0.5_naive"]).all()


def test_falls_back_to_equal_weights_without_a_tuned_file(panel, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "TUNED_PARAMS_PATH", tmp_path / "missing.json")

    model = EnsembleBlend(horizons=(2,))  # weights=None -> resolved lazily
    model.fit(panel)
    predictions = model.predict(panel, horizon=2)
    assert not predictions.empty


def test_rolling_origin_never_predicts_the_past(panel):
    """Same leakage guarantee every other model gets -- EnsembleBlend is a
    normal ForecastModel and must not bypass the harness in any way."""
    predictions = rolling_origin(EnsembleBlend, panel, horizons=(2,), stride=8)
    assert not predictions.empty
    assert (predictions["target_week"] > predictions["iso_week"]).all()


def test_a_failing_sub_model_does_not_crash_the_blend(panel, monkeypatch):
    from dengue.models.baseline import SeasonalNaive

    def _boom(self, panel, horizon):
        raise RuntimeError("synthetic sub-model failure")

    monkeypatch.setattr(SeasonalNaive, "predict", _boom)

    model = EnsembleBlend(horizons=(2,))
    model.fit(panel)
    predictions = model.predict(panel, horizon=2)
    # Two of three sub-models still succeed, so a blend is still possible.
    assert not predictions.empty
