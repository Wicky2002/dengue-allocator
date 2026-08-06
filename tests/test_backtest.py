"""Backtest-harness tests: fold ordering, leakage boundaries, metric behaviour.

Fold ordering is the thing most worth testing here. If folds silently overlap or
run backwards, every downstream number is optimistic and nothing else in the
repo would notice.
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
import pytest

from dengue import config
from dengue.eval.backtest import (
    Fold,
    default_folds,
    rolling_origin,
    score_predictions,
    validate_fold_ordering,
)
from dengue.eval.metrics import (
    high_risk_metrics,
    interval_coverage,
    mae,
    mape,
    pinball_loss,
)
from dengue.models.baseline import SeasonalNaive
from dengue.utils.synthetic import make_synthetic_panel


def _week(text: str) -> pd.Period:
    return pd.Period(text, freq=config.WEEK_FREQ)


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return make_synthetic_panel(n_districts=5, n_weeks=200, seed=17)


# --------------------------------------------------------------------------
# Fold ordering
# --------------------------------------------------------------------------


def test_default_folds_are_chronological_and_disjoint(panel):
    folds = default_folds(panel)
    assert len(folds) >= 2

    for fold in folds:
        assert fold.train_end < fold.eval_start, f"{fold.name} trains into its own eval window"
        assert fold.eval_start <= fold.eval_end

    for earlier, later in itertools.pairwise(folds):
        assert earlier.eval_end < later.eval_start, "evaluation windows overlap"
        assert earlier.train_end <= later.train_end, "training window must expand"


def test_fold_rejects_train_end_after_eval_start():
    fold = Fold("bad", _week("2024-06-01"), _week("2024-01-01"), _week("2024-12-01"))
    with pytest.raises(ValueError, match="must precede"):
        fold.validate()


def test_fold_rejects_reversed_eval_window():
    fold = Fold("bad", _week("2023-01-01"), _week("2024-12-01"), _week("2024-01-01"))
    with pytest.raises(ValueError, match="after"):
        fold.validate()


def test_validate_fold_ordering_rejects_overlap():
    folds = [
        Fold("a", _week("2022-01-03"), _week("2022-01-10"), _week("2023-01-02")),
        Fold("b", _week("2022-06-06"), _week("2022-06-13"), _week("2023-06-05")),
    ]
    with pytest.raises(ValueError, match="overlapping"):
        validate_fold_ordering(folds)


def test_validate_fold_ordering_rejects_shrinking_training_window():
    folds = [
        Fold("a", _week("2023-01-02"), _week("2023-01-09"), _week("2023-06-05")),
        Fold("b", _week("2022-01-03"), _week("2023-06-12"), _week("2023-12-04")),
    ]
    with pytest.raises(ValueError, match="trains on less data"):
        validate_fold_ordering(folds)


def test_validate_fold_ordering_rejects_empty():
    with pytest.raises(ValueError, match="No folds"):
        validate_fold_ordering([])


def test_default_folds_use_configured_boundaries_when_panel_spans_them():
    """A panel covering 2022-2026 must get the real val/test boundaries."""
    panel = make_synthetic_panel(n_districts=3, n_weeks=250, seed=2, end_week="2026-08-02")
    folds = default_folds(panel)
    names = [f.name for f in folds]
    assert names == ["val", "test"]

    val, test = folds
    # Compare on the week's START date: the last ISO week of a year straddles
    # into the next, so Period.year would report 2025 for the final 2024 week.
    assert val.eval_start.start_time.year == 2024
    assert val.eval_end.start_time.year == 2024
    assert test.eval_start.start_time.year == 2025
    assert test.eval_end.start_time.year >= 2025
    # val trains through 2023, test through 2024.
    assert val.train_end.start_time.year == 2023
    assert test.train_end.start_time.year == 2024


# --------------------------------------------------------------------------
# Rolling origin
# --------------------------------------------------------------------------


def test_rolling_origin_never_predicts_the_past(panel):
    predictions = rolling_origin(SeasonalNaive, panel, horizons=(2, 4), stride=8)
    assert not predictions.empty
    assert (predictions["target_week"] > predictions["iso_week"]).all()

    lead = (predictions["target_week"] - predictions["iso_week"]).apply(lambda x: x.n)
    np.testing.assert_array_equal(lead.to_numpy(), predictions["horizon"].to_numpy())


def test_rolling_origin_origins_stay_inside_their_fold(panel):
    folds = default_folds(panel)
    predictions = rolling_origin(SeasonalNaive, panel, horizons=(2,), folds=folds, stride=4)

    by_name = {f.name: f for f in folds}
    for fold_name, group in predictions.groupby("fold", observed=True):
        fold = by_name[fold_name]
        assert group["iso_week"].min() >= fold.eval_start
        assert group["iso_week"].max() <= fold.eval_end


def test_rolling_origin_is_deterministic(panel):
    a = rolling_origin(SeasonalNaive, panel, horizons=(2,), stride=8)
    b = rolling_origin(SeasonalNaive, panel, horizons=(2,), stride=8)
    pd.testing.assert_frame_equal(a, b)


def test_model_only_ever_sees_data_up_to_the_origin(panel):
    """Directly assert the leakage boundary the harness promises."""
    seen: list[pd.Period] = []

    class SpyModel(SeasonalNaive):
        name = "spy"

        def fit(self, training_panel):
            seen.append(training_panel["iso_week"].max())
            return super().fit(training_panel)

    predictions = rolling_origin(SpyModel, panel, horizons=(2,), stride=12)
    assert seen
    # Every fit's newest training week must be an origin actually forecast from.
    assert set(seen) == set(predictions["iso_week"].unique())


def test_quantiles_are_ordered(panel):
    predictions = rolling_origin(SeasonalNaive, panel, horizons=(2,), stride=12)
    assert (predictions["q0.1"] <= predictions["q0.5"]).all()
    assert (predictions["q0.5"] <= predictions["q0.9"]).all()
    assert (predictions["q0.1"] >= 0).all()


def test_score_predictions_produces_tidy_output(panel):
    predictions = rolling_origin(SeasonalNaive, panel, horizons=(2, 3), stride=12)
    scores = score_predictions(predictions, panel)

    assert {"model", "horizon", "metric", "value"}.issubset(scores.columns)
    assert set(scores["horizon"].unique()) == {2, 3}
    assert "pinball_mean" in set(scores["metric"])


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------


def test_pinball_loss_is_minimised_at_the_true_quantile():
    rng = np.random.default_rng(0)
    y = rng.normal(100, 15, 5000)

    for q in (0.1, 0.5, 0.9):
        truth = float(np.quantile(y, q))
        best = pinball_loss(y, np.full_like(y, truth), q)
        for offset in (-10.0, -3.0, 3.0, 10.0):
            worse = pinball_loss(y, np.full_like(y, truth + offset), q)
            assert worse >= best - 1e-9


def test_pinball_loss_is_asymmetric():
    """Under-predicting the 0.9 quantile must cost more than over-predicting."""
    y = np.array([100.0])
    under = pinball_loss(y, np.array([90.0]), 0.9)
    over = pinball_loss(y, np.array([110.0]), 0.9)
    assert under > over


def test_pinball_loss_rejects_invalid_quantile():
    with pytest.raises(ValueError, match="quantile must be in"):
        pinball_loss(np.array([1.0]), np.array([1.0]), 1.5)


def test_interval_coverage_matches_construction():
    rng = np.random.default_rng(1)
    y = rng.normal(0, 1, 20000)
    lower = np.full_like(y, float(np.quantile(y, 0.1)))
    upper = np.full_like(y, float(np.quantile(y, 0.9)))
    assert interval_coverage(y, lower, upper) == pytest.approx(0.80, abs=0.02)


def test_mae_and_mape_are_zero_for_perfect_forecasts():
    y = np.array([10.0, 20.0, 30.0])
    assert mae(y, y) == 0.0
    assert mape(y, y) == 0.0


def test_mape_survives_zero_case_weeks():
    """Low-burden districts have genuine zero weeks; MAPE must stay finite."""
    y = np.array([0.0, 0.0, 5.0])
    value = mape(y, np.array([1.0, 0.0, 4.0]))
    assert np.isfinite(value)


def test_metrics_ignore_nan_pairs():
    y = np.array([1.0, np.nan, 3.0])
    p = np.array([1.0, 2.0, 3.0])
    assert mae(y, p) == 0.0


def test_high_risk_metrics_return_nan_without_labels(panel):
    unlabelled = panel.copy()
    unlabelled["high_risk_flag"] = pd.NA
    predictions = rolling_origin(SeasonalNaive, unlabelled, horizons=(2,), stride=12)
    result = high_risk_metrics(predictions, unlabelled)
    assert np.isnan(result["high_risk_precision"])
    assert result["n_onsets"] == 0


def test_high_risk_metrics_are_bounded(panel):
    predictions = rolling_origin(SeasonalNaive, panel, horizons=(2, 3, 4), stride=8)
    result = high_risk_metrics(predictions, panel, top_k=2)

    for key in ("high_risk_precision", "high_risk_recall", "high_risk_f1"):
        value = result[key]
        assert np.isnan(value) or 0.0 <= value <= 1.0

    lead = result["mean_lead_time_weeks"]
    assert np.isnan(lead) or 2 <= lead <= 4, "lead time must lie within the evaluated horizons"
