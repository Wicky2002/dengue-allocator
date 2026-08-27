"""Tests for the predicted-vs-actual historical view (dengue.eval.history).

The one thing worth guarding here is the inner join against real outcomes:
every returned row must have a target week that already happened, and the
predicted/actual incidence figures must be computed off the real population
and the real ``q0.5``/``cases`` columns, not silently swapped or misaligned.
"""

from __future__ import annotations

import pandas as pd
import pytest

from dengue import config
from dengue.eval.history import HISTORY_END, HISTORY_START, build_history_predictions
from dengue.models.baseline import SeasonalNaive
from dengue.utils.synthetic import make_synthetic_panel


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    # SeasonalNaive is the injected model in every test below (fast, no
    # LightGBM/GA-tuned lookup needed) -- ends "now", which this project's
    # own clock keeps inside the fixed history window, exactly like
    # test_backtest.py's fixture relies on for the default val/test folds.
    return make_synthetic_panel(n_districts=6, n_weeks=250, seed=41)


def test_returns_rows_inside_the_fixed_window(panel):
    result = build_history_predictions(panel, model=SeasonalNaive)
    assert not result.empty

    origins = pd.PeriodIndex(result["iso_week"].unique(), freq=config.WEEK_FREQ)
    assert origins.min() >= HISTORY_START
    assert origins.max() <= HISTORY_END


def test_every_row_has_a_resolved_actual(panel):
    result = build_history_predictions(panel, model=SeasonalNaive)
    assert not result.empty

    last_observed = pd.Period(panel["iso_week"].max(), freq=config.WEEK_FREQ)
    target_weeks = pd.PeriodIndex(result["target_week"].unique(), freq=config.WEEK_FREQ)
    # The join is inner on (district_id, target_week) against the panel's own
    # actuals, so nothing past the panel's last observed week can appear --
    # this is the guarantee the app's slider relies on to never show a
    # "predicted" map for a week that hasn't happened yet.
    assert target_weeks.max() <= last_observed
    assert result["actual_cases"].notna().all()


def test_incidence_columns_match_a_manual_calculation(panel):
    result = build_history_predictions(panel, model=SeasonalNaive)
    assert not result.empty

    row = result.iloc[0]
    expected_actual = row["actual_cases"] / row["population"] * 100_000.0
    expected_predicted = row["q0.5"] / row["population"] * 100_000.0
    assert row["actual_incidence_per_100k"] == pytest.approx(expected_actual)
    assert row["predicted_incidence_per_100k"] == pytest.approx(expected_predicted)


def test_all_districts_present_at_a_given_origin(panel):
    result = build_history_predictions(panel, model=SeasonalNaive)
    assert not result.empty

    some_origin = result["iso_week"].iloc[0]
    some_horizon = result["horizon"].iloc[0]
    at_origin = result[(result["iso_week"] == some_origin) & (result["horizon"] == some_horizon)]
    assert set(at_origin["district_id"]) == set(panel["district_id"].unique())


def test_empty_when_panel_does_not_reach_the_window():
    short_panel = make_synthetic_panel(
        n_districts=4, n_weeks=60, seed=3, end_week="2024-12-29"
    )
    result = build_history_predictions(short_panel, model=SeasonalNaive)
    assert result.empty
