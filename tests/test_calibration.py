"""Tests for ConformalQuantileWrapper: does it actually improve coverage,
and does it respect the leakage-safety rules every other model follows."""

from __future__ import annotations

import pandas as pd
import pytest

from dengue.eval.backtest import rolling_origin
from dengue.eval.metrics import interval_coverage
from dengue.models import PREDICTION_COLUMNS, ForecastModel
from dengue.models.calibration import ConformalQuantileWrapper
from dengue.utils.synthetic import make_synthetic_panel


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return make_synthetic_panel(n_districts=4, n_weeks=180, seed=31)


class _OverconfidentModel(ForecastModel):
    """A model whose intervals are deliberately, consistently too narrow --
    the exact failure mode this wrapper exists to correct."""

    name = "overconfident"

    def fit(self, panel: pd.DataFrame) -> _OverconfidentModel:
        self._last = panel.sort_values("iso_week").groupby("district_id")["cases"].last()
        self._districts = list(self._last.index)
        self._fitted = True
        return self

    def predict(self, panel: pd.DataFrame, horizon: int) -> pd.DataFrame:
        self._check_fitted()
        origins = panel.groupby("district_id")["iso_week"].max()
        rows = []
        for district_id, origin in origins.items():
            level = float(self._last.get(district_id, 1.0))
            rows.append(
                {
                    "district_id": district_id,
                    "iso_week": origin,
                    "target_week": origin + horizon,
                    "horizon": horizon,
                    "q0.1": level * 0.99,
                    "q0.5": level,
                    "q0.9": level * 1.01,
                }
            )
        return pd.DataFrame(rows)[list(PREDICTION_COLUMNS)]


def test_fit_predict_returns_prediction_columns(panel):
    model = ConformalQuantileWrapper(_OverconfidentModel, horizons=(2,), calib_weeks=12)
    model.fit(panel)
    predictions = model.predict(panel, horizon=2)

    assert not predictions.empty
    assert list(predictions.columns) == list(PREDICTION_COLUMNS)
    assert (predictions["q0.1"] <= predictions["q0.5"]).all()
    assert (predictions["q0.5"] <= predictions["q0.9"]).all()


def test_widens_intervals_for_a_deliberately_overconfident_model(panel):
    model = ConformalQuantileWrapper(_OverconfidentModel, horizons=(2,), calib_weeks=12)
    model.fit(panel)
    assert model._correction[2] > 0.0, "an overconfident model must get a positive correction"

    predictions = model.predict(panel, horizon=2)
    baseline = _OverconfidentModel().fit(panel).predict(panel, horizon=2)
    merged = predictions.merge(
        baseline, on=["district_id", "iso_week", "target_week", "horizon"], suffixes=("", "_raw")
    )
    assert (merged["q0.9"] >= merged["q0.9_raw"]).all()
    assert (merged["q0.1"] <= merged["q0.1_raw"]).all()


def test_conformal_coverage_beats_the_uncorrected_model_on_held_out_data(panel):
    """The actual point of this wrapper: does correcting on a calibration
    window generalise to genuinely new data, not just refit the same miss."""
    raw_predictions = rolling_origin(_OverconfidentModel, panel, horizons=(2,), stride=4)
    conformal_predictions = rolling_origin(
        lambda: ConformalQuantileWrapper(_OverconfidentModel, horizons=(2,), calib_weeks=12),
        panel,
        horizons=(2,),
        stride=4,
    )

    def _coverage(predictions: pd.DataFrame) -> float:
        actuals = panel[["district_id", "iso_week", "cases"]].rename(
            columns={"iso_week": "target_week"}
        )
        merged = predictions.merge(actuals, on=["district_id", "target_week"])
        return interval_coverage(
            merged["cases"].to_numpy(), merged["q0.1"].to_numpy(), merged["q0.9"].to_numpy()
        )

    assert _coverage(conformal_predictions) > _coverage(raw_predictions)


def test_zero_correction_when_the_panel_is_too_short():
    tiny_panel = make_synthetic_panel(n_districts=2, n_weeks=20, seed=5)
    model = ConformalQuantileWrapper(
        _OverconfidentModel, horizons=(2,), calib_weeks=12, min_train_weeks=52
    )
    model.fit(tiny_panel)
    assert model._correction == {2: 0.0}


def test_predict_before_fit_raises(panel):
    model = ConformalQuantileWrapper(_OverconfidentModel, horizons=(2,))
    with pytest.raises(RuntimeError, match="must be fitted"):
        model.predict(panel, horizon=2)


def test_rolling_origin_never_predicts_the_past(panel):
    predictions = rolling_origin(
        lambda: ConformalQuantileWrapper(_OverconfidentModel, horizons=(2,), calib_weeks=8),
        panel,
        horizons=(2,),
        stride=8,
    )
    assert not predictions.empty
    assert (predictions["target_week"] > predictions["iso_week"]).all()


def test_calibration_never_uses_data_past_the_outer_origin(panel, monkeypatch):
    """The calibration step must itself respect the origin: it may only see
    weeks already <= the outer backtest origin, same as everything else."""
    seen_max_weeks: list[pd.Period] = []

    class _SpyModel(_OverconfidentModel):
        name = "spy"

        def fit(self, panel):
            seen_max_weeks.append(panel["iso_week"].max())
            return super().fit(panel)

    model = ConformalQuantileWrapper(_SpyModel, horizons=(2,), calib_weeks=12)
    # Simulate what rolling_origin would hand it: panel already truncated at
    # some origin well before the panel's true end.
    origin = sorted(panel["iso_week"].unique())[-30]
    truncated = panel[panel["iso_week"] <= origin]
    model.fit(truncated)

    assert seen_max_weeks
    assert all(w <= origin for w in seen_max_weeks)
