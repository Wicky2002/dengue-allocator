"""Split-conformal interval widening, wrapping any quantile ForecastModel.

LightGBM's documented weakness in this project is under-coverage: its 80%
intervals empirically cover ~65-68% of outcomes (see the README's results
table), because independently-fitted quantile regressors have no built-in
calibration guarantee. GA-tuning the hyperparameters (see
:mod:`dengue.tuning`) closes part of that gap by trading pinball loss for
calibration; this wrapper attacks the same problem more directly, by
widening the predicted interval by however much the model has *actually*
been wrong on held-out data.

Hand-rolled rather than a library (e.g. ``mapie``) for the same reason the
GA is hand-rolled (see :mod:`dengue.tuning`'s module docstring): a generic
library's calibration split is a random or simple index split, and this
project's one non-negotiable rule is that nothing is ever calibrated,
selected, or evaluated on anything but a strictly temporal split. Reusing
:func:`dengue.eval.backtest.rolling_origin` for the calibration step, rather
than reimplementing a train/calibration split by hand, is what guarantees
that.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from dengue import config
from dengue.models import ForecastModel, enforce_quantile_monotonicity

_LOWER_QUANTILE = f"q{min(config.QUANTILES)}"
_UPPER_QUANTILE = f"q{max(config.QUANTILES)}"


class ConformalQuantileWrapper(ForecastModel):
    """Widen a base model's prediction interval by its own recent miss size.

    Parameters
    ----------
    base_model_factory:
        A :class:`ForecastModel` instance or zero-argument factory -- same
        contract as :data:`dengue.eval.backtest.ModelLike`. A **fresh**
        instance is fit for the calibration step and again for the final
        deployed model, so a shared, already-fitted instance is never reused
        across the two.
    horizons:
        Forecast horizons.
    calib_weeks:
        Size of the held-out calibration window, taken from the tail of
        whatever panel :meth:`fit` receives (which is itself already
        truncated at the outer backtest origin -- this never sees data past
        that origin either).
    alpha:
        Miscoverage rate the correction targets. Defaults to ``1 -
        PI_NOMINAL_COVERAGE`` (0.20), matching the 80% interval used
        everywhere else in this project.
    min_train_weeks:
        Passed through to the calibration :func:`rolling_origin` call.

    Notes
    -----
    This is a practical empirical-quantile correction, not a finite-sample-
    exact conformal guarantee (which would need the ``ceil((n+1)(1-alpha))``
    order statistic and independence assumptions that a temporally
    autocorrelated series doesn't satisfy anyway). The goal is a real,
    data-driven correction, not a formal proof.
    """

    name = "conformal"

    def __init__(
        self,
        base_model_factory,
        horizons: tuple[int, ...] = config.HORIZONS,
        calib_weeks: int = 12,
        alpha: float = 1.0 - config.PI_NOMINAL_COVERAGE,
        min_train_weeks: int = 52,
    ) -> None:
        self.base_model_factory = base_model_factory
        self.horizons = horizons
        self.calib_weeks = calib_weeks
        self.alpha = alpha
        self.min_train_weeks = min_train_weeks
        self._base_model: ForecastModel | None = None
        self._correction: dict[int, float] = {}

    def fit(self, panel: pd.DataFrame) -> ConformalQuantileWrapper:
        from dengue.eval.backtest import Fold, _instantiate, rolling_origin

        weeks = sorted(panel["iso_week"].unique())
        self._correction = dict.fromkeys(self.horizons, 0.0)

        if len(weeks) > self.calib_weeks + self.min_train_weeks:
            calib_start_idx = len(weeks) - self.calib_weeks
            calib_start = weeks[calib_start_idx]
            train_end = weeks[calib_start_idx - 1]
            calib_fold = Fold(
                name="conformal_calib",
                train_end=train_end,
                eval_start=calib_start,
                eval_end=weeks[-1],
            )
            calib_predictions = rolling_origin(
                self.base_model_factory,
                panel,
                horizons=self.horizons,
                folds=[calib_fold],
                stride=1,
                min_train_weeks=self.min_train_weeks,
            )
            if not calib_predictions.empty:
                actuals = panel[["district_id", "iso_week", "cases"]].rename(
                    columns={"iso_week": "target_week"}
                )
                merged = calib_predictions.merge(
                    actuals, on=["district_id", "target_week"], how="inner"
                )
                merged["score"] = np.maximum(
                    merged[_LOWER_QUANTILE] - merged["cases"],
                    merged["cases"] - merged[_UPPER_QUANTILE],
                )
                for horizon, group in merged.groupby("horizon"):
                    if len(group) == 0:
                        continue
                    self._correction[horizon] = max(
                        0.0, float(np.quantile(group["score"], 1.0 - self.alpha))
                    )

        self._base_model = _instantiate(self.base_model_factory)
        self._base_model.fit(panel)
        self._fitted = True
        return self

    def predict(self, panel: pd.DataFrame, horizon: int) -> pd.DataFrame:
        self._check_fitted()
        assert self._base_model is not None  # set in fit(), which _fitted guarantees ran
        predictions = self._base_model.predict(panel, horizon)
        if predictions.empty:
            return predictions

        correction = self._correction.get(horizon, 0.0)
        if correction <= 0.0:
            return predictions

        predictions = predictions.copy()
        predictions[_LOWER_QUANTILE] = predictions[_LOWER_QUANTILE] - correction
        predictions[_UPPER_QUANTILE] = predictions[_UPPER_QUANTILE] + correction
        return enforce_quantile_monotonicity(predictions)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"ConformalQuantileWrapper(correction={self._correction}, fitted={self._fitted})"
