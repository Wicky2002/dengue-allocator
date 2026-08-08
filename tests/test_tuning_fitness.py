"""Tuning fitness-function tests: composite scoring, and the real wiring
from a genome through the leakage-safe backtest harness to a scalar.

The LightGBM fitness path is exercised for real (genome -> LGBMQuantile ->
rolling_origin -> score_predictions -> scalar) on a tiny synthetic panel with
a capped ``n_estimators``, so it stays a few seconds rather than minutes --
see :mod:`tests.test_tuning_genetic` for the pure-numpy GA engine tests this
file does not repeat.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dengue import config
from dengue.eval.backtest import default_folds, rolling_origin
from dengue.models import PREDICTION_COLUMNS
from dengue.models.baseline import SeasonalNaive
from dengue.tuning.fitness import (
    FitnessConfig,
    aggregate_scores,
    blend_predictions,
    build_search_fold,
    composite_fitness,
    make_ensemble_fitness,
    make_lgbm_fitness,
    merge_base_predictions,
)
from dengue.tuning.search_spaces import LGBM_SEARCH_SPACE
from dengue.utils.synthetic import make_synthetic_panel


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return make_synthetic_panel(n_districts=3, n_weeks=150, seed=11)


@pytest.fixture(scope="module")
def search_fold(panel):
    val = next(f for f in default_folds(panel) if f.name == "val")
    weeks = pd.PeriodIndex(sorted(panel["iso_week"].unique()), freq=config.WEEK_FREQ)
    return build_search_fold(val, weeks, n_origins=2, stride=4)


# --------------------------------------------------------------------------
# build_search_fold
# --------------------------------------------------------------------------


def test_build_search_fold_stays_inside_the_val_window(panel, search_fold):
    val = next(f for f in default_folds(panel) if f.name == "val")
    assert val.eval_start <= search_fold.eval_start <= search_fold.eval_end <= val.eval_end
    assert search_fold.train_end == val.train_end


def test_build_search_fold_raises_when_val_is_too_short(panel):
    val = next(f for f in default_folds(panel) if f.name == "val")
    weeks = pd.PeriodIndex(sorted(panel["iso_week"].unique()), freq=config.WEEK_FREQ)
    with pytest.raises(ValueError, match="only has"):
        build_search_fold(val, weeks, n_origins=1000, stride=4)


# --------------------------------------------------------------------------
# aggregate_scores / composite_fitness
# --------------------------------------------------------------------------


def test_aggregate_scores_means_across_horizons_within_a_fold():
    scores = pd.DataFrame(
        {
            "fold": ["search", "search", "search", "search", "other", "other"],
            "metric": ["pinball_mean", "pinball_mean", "coverage_80", "coverage_80"] * 1
            + ["pinball_mean", "coverage_80"],
            "value": [10.0, 20.0, 0.7, 0.9, 999.0, 0.0],
        }
    )
    pinball_mean, coverage_mean = aggregate_scores(scores, fold="search")
    assert pinball_mean == pytest.approx(15.0)
    assert coverage_mean == pytest.approx(0.8)


def test_composite_fitness_equals_pinball_inside_the_coverage_dead_band():
    cfg = FitnessConfig(coverage_penalty_weight=2.0, coverage_tolerance=0.03)
    value = composite_fitness(pinball_mean=10.0, coverage_80=0.79, cfg=cfg)
    assert value == pytest.approx(10.0)


def test_composite_fitness_penalizes_outside_the_dead_band():
    cfg = FitnessConfig(coverage_penalty_weight=2.0, coverage_tolerance=0.03)
    value = composite_fitness(pinball_mean=10.0, coverage_80=0.60, cfg=cfg)
    # gap = |0.60 - 0.80| - 0.03 = 0.17
    assert value == pytest.approx(10.0 * (1.0 + 2.0 * 0.17))


def test_composite_fitness_returns_penalty_value_for_nan_pinball():
    cfg = FitnessConfig(penalty_value=1e6)
    assert composite_fitness(float("nan"), 0.8, cfg) == 1e6


# --------------------------------------------------------------------------
# LGBM fitness: real genome -> LGBMQuantile -> rolling_origin -> scalar
# --------------------------------------------------------------------------


def test_make_lgbm_fitness_returns_a_finite_scalar_on_a_tiny_panel(panel, search_fold):
    fitness_fn = make_lgbm_fitness(
        panel, search_fold, horizons=(2,), stride=4, fitness_cfg=FitnessConfig()
    )
    genome = dict(LGBM_SEARCH_SPACE.sample(np.random.default_rng(0)))
    genome["n_estimators"] = 20  # cap fit cost for a fast unit test

    value = fitness_fn(genome)
    assert np.isfinite(value)
    assert value < FitnessConfig().penalty_value


def test_make_lgbm_fitness_is_deterministic_for_the_same_genome(panel, search_fold):
    fitness_fn = make_lgbm_fitness(panel, search_fold, horizons=(2,), stride=4)
    genome = {**dict(LGBM_SEARCH_SPACE.sample(np.random.default_rng(1))), "n_estimators": 20}

    assert fitness_fn(genome) == pytest.approx(fitness_fn(genome))


def test_make_lgbm_fitness_returns_penalty_value_when_the_backtest_raises(
    panel, search_fold, monkeypatch
):
    import dengue.tuning.fitness as fitness_module

    def _boom(*args, **kwargs):
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr(fitness_module, "rolling_origin", _boom)

    fitness_fn = make_lgbm_fitness(
        panel,
        search_fold,
        horizons=(2,),
        stride=4,
        fitness_cfg=FitnessConfig(penalty_value=12345.0),
    )
    genome = dict(LGBM_SEARCH_SPACE.sample(np.random.default_rng(0)))
    assert fitness_fn(genome) == 12345.0


def test_make_lgbm_fitness_returns_penalty_value_when_the_backtest_is_empty(
    panel, search_fold, monkeypatch
):
    import dengue.tuning.fitness as fitness_module

    monkeypatch.setattr(fitness_module, "rolling_origin", lambda *a, **kw: pd.DataFrame())

    fitness_fn = make_lgbm_fitness(
        panel, search_fold, horizons=(2,), stride=4, fitness_cfg=FitnessConfig(penalty_value=42.0)
    )
    genome = dict(LGBM_SEARCH_SPACE.sample(np.random.default_rng(0)))
    assert fitness_fn(genome) == 42.0


# --------------------------------------------------------------------------
# Ensemble fitness: merge_base_predictions, blend_predictions
# --------------------------------------------------------------------------


def _prediction_frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)[list(PREDICTION_COLUMNS)]


def test_merge_base_predictions_inner_joins_on_common_rows():
    common = {"district_id": "COLOMBO", "iso_week": pd.Period("2024-01-01", freq="W"), "horizon": 2}
    common["target_week"] = common["iso_week"] + 2

    naive = _prediction_frame([{**common, "q0.1": 1.0, "q0.5": 2.0, "q0.9": 3.0}])
    sarima = _prediction_frame([{**common, "q0.1": 4.0, "q0.5": 5.0, "q0.9": 6.0}])
    lgbm_only_row = dict(common)
    lgbm_only_row["district_id"] = "GALLE"  # no matching row in the other two
    lgbm = pd.concat(
        [
            _prediction_frame([{**common, "q0.1": 7.0, "q0.5": 8.0, "q0.9": 9.0}]),
            _prediction_frame([{**lgbm_only_row, "q0.1": 0.0, "q0.5": 0.0, "q0.9": 0.0}]),
        ],
        ignore_index=True,
    )

    merged = merge_base_predictions({"w_naive": naive, "w_sarima": sarima, "w_lgbm": lgbm})

    assert len(merged) == 1  # the GALLE-only row has no match in naive/sarima
    assert merged.loc[0, "q0.5__w_naive"] == 2.0
    assert merged.loc[0, "q0.5__w_sarima"] == 5.0
    assert merged.loc[0, "q0.5__w_lgbm"] == 8.0


def test_merge_base_predictions_returns_empty_frame_with_fewer_than_two_models():
    common = {
        "district_id": "COLOMBO",
        "iso_week": pd.Period("2024-01-01", freq="W"),
        "target_week": pd.Period("2024-01-15", freq="W"),
        "horizon": 2,
    }
    only_one = {"w_naive": _prediction_frame([{**common, "q0.1": 1.0, "q0.5": 2.0, "q0.9": 3.0}])}
    merged = merge_base_predictions(only_one)
    assert merged.empty


def test_blend_predictions_is_a_weighted_average_and_stays_monotonic():
    merged = pd.DataFrame(
        [
            {
                "district_id": "COLOMBO",
                "iso_week": pd.Period("2024-01-01", freq="W"),
                "target_week": pd.Period("2024-01-15", freq="W"),
                "horizon": 2,
                "q0.1__a": 1.0,
                "q0.5__a": 2.0,
                "q0.9__a": 3.0,
                "q0.1__b": 5.0,
                "q0.5__b": 6.0,
                "q0.9__b": 7.0,
            }
        ]
    )
    blended = blend_predictions(merged, {"a": 0.25, "b": 0.75})

    assert blended.loc[0, "q0.5"] == pytest.approx(0.25 * 2.0 + 0.75 * 6.0)
    assert (blended["q0.1"] <= blended["q0.5"]).all()
    assert (blended["q0.5"] <= blended["q0.9"]).all()


def test_blend_predictions_returns_empty_frame_for_empty_input():
    merged = pd.DataFrame(columns=["district_id", "iso_week", "target_week", "horizon"])
    blended = blend_predictions(merged, {"a": 1.0})
    assert blended.empty
    assert list(blended.columns) == list(PREDICTION_COLUMNS)


def test_make_ensemble_fitness_on_a_real_panel_returns_a_finite_scalar(panel, search_fold):
    """Uses SeasonalNaive under all three keys as a cheap stand-in for the
    real 3-model roster, so this exercises merge -> blend -> score end to end
    against real panel data without SARIMA/LGBM's cost."""
    predictions = rolling_origin(SeasonalNaive, panel, horizons=(2,), folds=[search_fold], stride=4)
    assert not predictions.empty

    merged = merge_base_predictions(
        {"w_naive": predictions, "w_sarima": predictions.copy(), "w_lgbm": predictions.copy()}
    )
    assert not merged.empty

    fitness_fn = make_ensemble_fitness(panel, merged, fitness_cfg=FitnessConfig())
    value = fitness_fn({"w_naive": 0.2, "w_sarima": 0.3, "w_lgbm": 0.5})
    assert np.isfinite(value)
    assert value < FitnessConfig().penalty_value


def test_make_ensemble_fitness_returns_penalty_value_for_an_empty_merged_frame(panel):
    fitness_fn = make_ensemble_fitness(
        panel, pd.DataFrame(), fitness_cfg=FitnessConfig(penalty_value=7.0)
    )
    assert fitness_fn({"w_naive": 1.0, "w_sarima": 0.0, "w_lgbm": 0.0}) == 7.0
