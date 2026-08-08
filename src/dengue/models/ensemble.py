"""Blend the three base Stage 1 models using GA-tuned weights.

``make tune`` already searches for good blend weights across
``SeasonalNaive``/``SarimaBaseline``/``LGBMQuantile`` (see
:mod:`dengue.tuning.fitness`'s ``make_ensemble_fitness``), but until now those
weights were only ever written to ``tuned_hyperparams.json`` and never used
by anything -- the search's own result was dead weight. :class:`EnsembleBlend`
is the model that actually consumes it: a normal :class:`ForecastModel` that
fits all three base models and blends their quantile predictions, so it can
sit in :func:`dengue.eval.backtest.build_default_models`'s roster exactly like
any other entry.

Reuses :func:`dengue.tuning.fitness.merge_base_predictions` and
:func:`~dengue.tuning.fitness.blend_predictions` directly rather than
reimplementing the join/blend logic -- ``tuning`` already depends on
``models``, so importing the other way (here, lazily inside the methods that
need it) avoids a circular import at module load time.
"""

from __future__ import annotations

import pandas as pd

from dengue import config
from dengue.models import ForecastModel

#: Equal-weight fallback when no tuned weights exist yet (`make tune` has
#: never been run) -- same never-raises contract as `load_tuned_params`.
_EQUAL_WEIGHTS: dict[str, float] = {"w_naive": 1 / 3, "w_sarima": 1 / 3, "w_lgbm": 1 / 3}


class EnsembleBlend(ForecastModel):
    """Weighted blend of SeasonalNaive, SarimaBaseline and LGBMQuantile.

    Parameters
    ----------
    horizons:
        Forecast horizons, passed through to the LGBM sub-model.
    weights:
        Override the tuned weights (mainly for tests). When omitted, loaded
        from :data:`dengue.config.TUNED_PARAMS_PATH` at predict time via
        :func:`dengue.tuning.runner.load_tuned_params`; falls back to equal
        weights if that file doesn't have an ``"ensemble"`` entry yet.
    random_state:
        Passed through to the LGBM sub-model.
    """

    name = "ensemble"

    def __init__(
        self,
        horizons: tuple[int, ...] = config.HORIZONS,
        weights: dict[str, float] | None = None,
        random_state: int = config.RANDOM_SEED,
    ) -> None:
        self.horizons = horizons
        self.weights = weights
        self.random_state = random_state
        self._models: dict[str, ForecastModel] = {}

    def _resolve_weights(self) -> dict[str, float]:
        if self.weights is not None:
            return self.weights
        from dengue.tuning.runner import load_tuned_params

        tuned = load_tuned_params("ensemble")
        return tuned["weights"] if tuned else _EQUAL_WEIGHTS

    def fit(self, panel: pd.DataFrame) -> EnsembleBlend:
        from dengue.models.baseline import SarimaBaseline, SeasonalNaive
        from dengue.models.lgbm_quantile import LGBMQuantile

        self._models = {
            "w_naive": SeasonalNaive(),
            "w_sarima": SarimaBaseline(),
            "w_lgbm": LGBMQuantile(horizons=self.horizons, random_state=self.random_state),
        }
        for model in self._models.values():
            model.fit(panel)
        self._fitted = True
        return self

    def predict(self, panel: pd.DataFrame, horizon: int) -> pd.DataFrame:
        self._check_fitted()
        from dengue.tuning.fitness import blend_predictions, merge_base_predictions

        predictions: dict[str, pd.DataFrame] = {}
        for key, model in self._models.items():
            try:
                predictions[key] = model.predict(panel, horizon)
            except Exception:  # - a sub-model's own failure mode, not ours
                predictions[key] = self._empty_predictions()

        merged = merge_base_predictions(predictions)
        if merged.empty:
            return self._empty_predictions()
        return blend_predictions(merged, self._resolve_weights())

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        weights = self.weights or "<tuned, loaded lazily>"
        return f"EnsembleBlend(weights={weights}, fitted={self._fitted})"
