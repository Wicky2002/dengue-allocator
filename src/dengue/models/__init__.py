"""Stage 1 forecasting models and the interface they all share.

Every model implements :class:`ForecastModel`, so the backtest harness can treat
a seasonal-naive rule and a gradient-boosted quantile ensemble identically.

The prediction contract
-----------------------
``predict(panel, horizon)`` returns one row per ``(district_id, origin_week)``:

===============  ==========================================================
column           meaning
===============  ==========================================================
``district_id``  canonical district key
``iso_week``     **forecast origin** -- the last week whose data was used
``target_week``  the week being predicted, ``iso_week + horizon``
``horizon``      forecast lead time in weeks
``q0.1``         10th percentile of predicted cases
``q0.5``         median predicted cases
``q0.9``         90th percentile of predicted cases
===============  ==========================================================

Quantiles are in **case counts**, not logs, so metrics are interpretable in the
units decision-makers use. They are non-negative and sorted: ``q0.1 <= q0.5 <=
q0.9`` is enforced by :func:`enforce_quantile_monotonicity`, because independently
fitted quantile regressors can otherwise cross and produce a negative-width
interval.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from dengue import config

QUANTILE_COLUMNS: tuple[str, ...] = tuple(f"q{q}" for q in config.QUANTILES)

PREDICTION_COLUMNS: tuple[str, ...] = (
    "district_id",
    "iso_week",
    "target_week",
    "horizon",
    *QUANTILE_COLUMNS,
)


def enforce_quantile_monotonicity(frame: pd.DataFrame) -> pd.DataFrame:
    """Sort quantile columns row-wise so they never cross, and clip at zero.

    Independently fitted quantile regressors have no built-in ordering
    constraint; crossing is common in sparse regions of the feature space. Sorting
    the row is the standard, distribution-free repair and cannot make the pinball
    loss worse.
    """
    out = frame.copy()
    values = out[list(QUANTILE_COLUMNS)].to_numpy(dtype=float)
    values = np.sort(values, axis=1)
    values = np.clip(values, 0.0, None)
    out[list(QUANTILE_COLUMNS)] = values
    return out


class ForecastModel(ABC):
    """Base class for Stage 1 probabilistic forecasters.

    Subclasses implement :meth:`fit` and :meth:`predict`. ``name`` is used as the
    row label in the backtest comparison table.
    """

    name: str = "base"

    #: Set by :meth:`fit`; guards against predicting from an unfitted model.
    _fitted: bool = False

    @abstractmethod
    def fit(self, panel: pd.DataFrame) -> ForecastModel:
        """Fit on a district-week panel.

        The panel passed here must contain **only** data at or before the
        forecast origin. The backtest harness guarantees this; models must not
        attempt to widen it.
        """

    @abstractmethod
    def predict(self, panel: pd.DataFrame, horizon: int) -> pd.DataFrame:
        """Predict ``horizon`` weeks ahead of each district's last observed week.

        Returns a frame with :data:`PREDICTION_COLUMNS`.
        """

    def _check_fitted(self) -> None:
        if not self._fitted:
            raise RuntimeError(f"{type(self).__name__} must be fitted before predicting")

    @staticmethod
    def _empty_predictions() -> pd.DataFrame:
        return pd.DataFrame({c: pd.Series(dtype="object") for c in PREDICTION_COLUMNS})

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"{type(self).__name__}(name={self.name!r}, fitted={self._fitted})"
