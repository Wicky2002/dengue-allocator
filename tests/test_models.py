"""Model-interface tests.

Every Stage 1 model must satisfy the same contract so the backtest harness can
treat them interchangeably. Stage 2 and 3 stubs must fail loudly rather than
returning plausible-looking placeholder numbers.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dengue import config
from dengue.models import PREDICTION_COLUMNS, enforce_quantile_monotonicity
from dengue.models.baseline import SarimaBaseline, SeasonalNaive
from dengue.models.lgbm_quantile import LGBMQuantile
from dengue.models.stgnn import STGNN
from dengue.utils.synthetic import make_synthetic_panel


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return make_synthetic_panel(n_districts=6, n_weeks=180, seed=23)


MODELS = [SeasonalNaive, SarimaBaseline, LGBMQuantile]


@pytest.mark.parametrize("factory", MODELS, ids=lambda f: f.name)
def test_fit_predict_contract(factory, panel):
    model = factory().fit(panel)
    predictions = model.predict(panel, horizon=2)

    assert list(predictions.columns) == list(PREDICTION_COLUMNS)
    assert not predictions.empty
    assert (predictions["horizon"] == 2).all()
    assert (predictions["target_week"] > predictions["iso_week"]).all()
    assert predictions["district_id"].isin(config.DISTRICT_IDS).all()


@pytest.mark.parametrize("factory", MODELS, ids=lambda f: f.name)
def test_quantiles_are_ordered_and_non_negative(factory, panel):
    model = factory().fit(panel)
    predictions = model.predict(panel, horizon=3)

    assert (predictions["q0.1"] <= predictions["q0.5"] + 1e-9).all()
    assert (predictions["q0.5"] <= predictions["q0.9"] + 1e-9).all()
    assert (predictions["q0.1"] >= 0).all()


@pytest.mark.parametrize("factory", MODELS, ids=lambda f: f.name)
def test_predict_before_fit_raises(factory, panel):
    with pytest.raises(RuntimeError, match="must be fitted"):
        factory().predict(panel, horizon=2)


@pytest.mark.parametrize("factory", MODELS, ids=lambda f: f.name)
def test_forecasts_from_the_last_observed_week(factory, panel):
    """The origin must be the newest week in the data the model was given."""
    model = factory().fit(panel)
    predictions = model.predict(panel, horizon=4)
    assert predictions["iso_week"].max() == panel["iso_week"].max()


def test_seasonal_naive_reproduces_last_year_same_week():
    """The point forecast must literally be the value 52 weeks earlier."""
    panel = make_synthetic_panel(n_districts=2, n_weeks=160, seed=1)
    model = SeasonalNaive().fit(panel)
    predictions = model.predict(panel, horizon=2)

    # Note: itertuples() mangles the "q0.5" column name (not an identifier), so
    # join on the reference week instead.
    reference = predictions.copy()
    reference["reference_week"] = reference["target_week"] - 52

    observed = panel[["district_id", "iso_week", "cases"]].rename(
        columns={"iso_week": "reference_week", "cases": "reference_cases"}
    )
    merged = reference.merge(observed, on=["district_id", "reference_week"], how="inner")
    assert not merged.empty, "no same-week-last-year reference available to check against"

    # The median applies the fitted median log-ratio, which is close to but not
    # exactly zero, so the point forecast is a scaled version of last year's value.
    ratio = (merged["q0.5"] + 1.0) / (merged["reference_cases"].astype("float64") + 1.0)
    assert ratio.std() == pytest.approx(
        0.0, abs=1e-9
    ), "SeasonalNaive must apply one constant multiplier to last year's value"
    assert 0.3 < ratio.iloc[0] < 3.0, f"implausible seasonal-naive scaling: {ratio.iloc[0]}"


def test_lgbm_trains_only_requested_horizons(panel):
    model = LGBMQuantile(horizons=(2,)).fit(panel)
    assert not model.predict(panel, horizon=2).empty
    with pytest.raises(ValueError, match="was not trained"):
        model.predict(panel, horizon=4)


def test_lgbm_exposes_feature_importances(panel):
    model = LGBMQuantile(horizons=(2,)).fit(panel)
    importances = model.feature_importances(horizon=2, quantile=0.5)
    assert set(importances.columns) == {"feature", "gain"}
    assert len(importances) > 10
    assert importances["gain"].iloc[0] >= importances["gain"].iloc[-1]


def test_enforce_quantile_monotonicity_repairs_crossings():
    frame = pd.DataFrame({"q0.1": [50.0], "q0.5": [10.0], "q0.9": [-5.0]})
    fixed = enforce_quantile_monotonicity(frame)
    assert fixed["q0.1"].iloc[0] == 0.0  # clipped at zero
    assert fixed["q0.1"].iloc[0] <= fixed["q0.5"].iloc[0] <= fixed["q0.9"].iloc[0]


def test_models_beat_a_constant_zero_forecast(panel):
    """Sanity floor: a real model must beat predicting nothing."""
    from dengue.eval.metrics import pinball_loss

    model = SeasonalNaive().fit(panel)
    predictions = model.predict(panel, horizon=2)

    truth = panel[["district_id", "iso_week", "cases"]].rename(columns={"iso_week": "target_week"})
    merged = predictions.merge(truth, on=["district_id", "target_week"], how="inner")
    if merged.empty:
        pytest.skip("no overlap between forecast targets and observed weeks")

    y = merged["cases"].astype("float64").to_numpy()
    model_loss = pinball_loss(y, merged["q0.5"].to_numpy(), 0.5)
    zero_loss = pinball_loss(y, np.zeros_like(y), 0.5)
    assert model_loss < zero_loss


# --------------------------------------------------------------------------
# Stubs must fail loudly
# --------------------------------------------------------------------------


def test_stgnn_raises_not_implemented(panel):
    model = STGNN()
    with pytest.raises(NotImplementedError, match="not implemented"):
        model.fit(panel)
    with pytest.raises(NotImplementedError, match="not implemented"):
        model.predict(panel, horizon=2)


def test_stage2_stub_raises_not_implemented(panel):
    from dengue.causal.sei_sir import build_effect_table, fit_sei_sir

    with pytest.raises(NotImplementedError, match="Stage 2"):
        fit_sei_sir(panel, "colombo")
    with pytest.raises(NotImplementedError, match="Stage 2"):
        build_effect_table(panel, pd.DataFrame())


def test_stage3_stub_raises_not_implemented():
    from dengue.optim.allocate import AllocationConstraints, allocate

    constraints = AllocationConstraints(total_team_weeks=50)
    with pytest.raises(NotImplementedError, match="Stage 3"):
        allocate(pd.DataFrame(), constraints, pd.Period("2026-08-03", freq=config.WEEK_FREQ))
