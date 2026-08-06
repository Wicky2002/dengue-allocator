"""Pooled LightGBM quantile regression across districts.

Three independent LightGBM regressors per horizon, one per quantile
(``objective="quantile"`` with ``alpha`` in 0.1 / 0.5 / 0.9), trained on all
districts jointly with ``district_id`` as a native categorical.

Why pooled rather than per-district
-----------------------------------
Sri Lanka's smaller districts (Mullaitivu, Mannar, Kilinochchi) see fewer than a
hundred cases in a typical week. Fitting a separate boosted model on each would
overfit badly. Pooling lets the model learn the shared climate-to-transmission
response from the high-volume districts while ``district_id`` and
``log_pop_density`` absorb level differences. This is the standard approach for
panel forecasting and it is why the model can be competitive at the district
level despite sparse local data.

Targets are ``log1p(cases)``; predictions are back-transformed with ``expm1``.
Because the model is fitted on the log scale, the predicted quantiles map to
case-scale quantiles exactly -- quantiles are equivariant under monotone
transforms, which means no smearing correction is needed here (unlike a mean
forecast, which would need one).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from dengue import config
from dengue.features.build_panel import (
    TARGET_PREFIX,
    build_features,
    categorical_columns,
    feature_columns,
)
from dengue.models import (
    PREDICTION_COLUMNS,
    ForecastModel,
    enforce_quantile_monotonicity,
)
from dengue.utils.logging import get_logger

log = get_logger(__name__)

#: Conservative defaults for a panel of ~10k rows and ~50 features. Shallow
#: trees and strong regularisation because the effective sample size is much
#: smaller than the row count: adjacent weeks are highly autocorrelated.
DEFAULT_PARAMS: dict[str, Any] = {
    "objective": "quantile",
    "n_estimators": 400,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "max_depth": 6,
    "min_child_samples": 30,
    "subsample": 0.8,
    "subsample_freq": 1,
    "colsample_bytree": 0.8,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "verbose": -1,
    "n_jobs": -1,
}


class LGBMQuantile(ForecastModel):
    """LightGBM quantile forecaster, pooled across districts.

    Parameters
    ----------
    horizons:
        Horizons to train for. One model per (horizon, quantile) pair, so the
        default 3 horizons x 3 quantiles is 9 boosters.
    params:
        Overrides merged into :data:`DEFAULT_PARAMS`.
    random_state:
        Seed for reproducibility.

    Notes
    -----
    :meth:`fit` rebuilds features internally from the raw panel, rather than
    accepting a pre-built matrix. That is intentional: it makes it impossible for
    the backtest harness to accidentally hand the model a feature matrix that was
    computed over the full series (including the test period), which is the most
    common way panel forecasting pipelines leak.
    """

    name = "lgbm_quantile"

    def __init__(
        self,
        horizons: tuple[int, ...] = config.HORIZONS,
        params: dict[str, Any] | None = None,
        random_state: int = config.RANDOM_SEED,
    ) -> None:
        self.horizons = horizons
        self.params = {**DEFAULT_PARAMS, **(params or {})}
        self.random_state = random_state
        self._models: dict[tuple[int, float], Any] = {}
        self._feature_names: list[str] = []
        self._categoricals: list[str] = []
        self._district_categories: list[str] = []
        self._train_panel: pd.DataFrame | None = None

    def _prepare_matrix(self, matrix: pd.DataFrame) -> pd.DataFrame:
        """Select feature columns and align categorical levels with training."""
        features = matrix[self._feature_names].copy()
        for column in self._categoricals:
            if column == "district_id":
                features[column] = pd.Categorical(
                    features[column].astype("string"), categories=self._district_categories
                )
            else:
                features[column] = features[column].astype("category")
        return features

    def fit(self, panel: pd.DataFrame) -> LGBMQuantile:
        from lightgbm import LGBMRegressor

        self._train_panel = panel.copy()
        matrix = build_features(panel, horizons=self.horizons)

        self._feature_names = feature_columns(matrix)
        self._categoricals = categorical_columns(matrix)
        self._district_categories = sorted(matrix["district_id"].astype("string").unique())

        self._models.clear()
        n_fitted = 0

        for horizon in self.horizons:
            target_column = f"{TARGET_PREFIX}{horizon}"
            usable = matrix[matrix[target_column].notna()]
            if usable.empty:
                log.warning("lgbm: no usable rows for horizon %d", horizon)
                continue

            X = self._prepare_matrix(usable)
            y = usable[target_column].astype("float64")

            for quantile in config.QUANTILES:
                model = LGBMRegressor(
                    **{**self.params, "alpha": quantile, "random_state": self.random_state}
                )
                model.fit(X, y, categorical_feature=self._categoricals)
                self._models[(horizon, quantile)] = model
                n_fitted += 1

            log.debug("lgbm: horizon %d trained on %d rows", horizon, len(usable))

        log.info(
            "lgbm: fitted %d boosters  horizons=%s  quantiles=%s  features=%d  districts=%d",
            n_fitted,
            list(self.horizons),
            list(config.QUANTILES),
            len(self._feature_names),
            len(self._district_categories),
        )
        self._fitted = True
        return self

    def predict(self, panel: pd.DataFrame, horizon: int) -> pd.DataFrame:
        self._check_fitted()

        if horizon not in self.horizons:
            raise ValueError(f"Horizon {horizon} was not trained. Available: {list(self.horizons)}")

        matrix = build_features(panel, horizons=self.horizons)

        # Forecast from each district's most recent week: that is the origin.
        origins = matrix.groupby("district_id", observed=True)["iso_week"].transform("max")
        latest = matrix[matrix["iso_week"] == origins]
        if latest.empty:
            return self._empty_predictions()

        # Districts unseen during training have no learned level; excluding them
        # is more honest than mapping them to an arbitrary category.
        known = latest["district_id"].astype("string").isin(self._district_categories)
        if not known.all():
            unknown = sorted(latest.loc[~known, "district_id"].astype("string").unique())
            log.warning("lgbm: skipping districts unseen in training: %s", unknown)
            latest = latest[known]
            if latest.empty:
                return self._empty_predictions()

        X = self._prepare_matrix(latest)

        result = pd.DataFrame(
            {
                "district_id": latest["district_id"].astype("string").to_numpy(),
                "iso_week": latest["iso_week"].to_numpy(),
                "target_week": (latest["iso_week"] + horizon).to_numpy(),
                "horizon": horizon,
            }
        )

        for quantile in config.QUANTILES:
            model = self._models.get((horizon, quantile))
            if model is None:
                raise RuntimeError(f"No model for horizon={horizon}, quantile={quantile}")
            predicted_log = model.predict(X)
            result[f"q{quantile}"] = np.clip(np.expm1(predicted_log), 0.0, None)

        return enforce_quantile_monotonicity(result[list(PREDICTION_COLUMNS)])

    def feature_importances(self, horizon: int = 2, quantile: float = 0.5) -> pd.DataFrame:
        """Gain-based feature importances for one fitted booster.

        Useful for the write-up: it shows whether the model is leaning on the
        climate lags (mechanistically plausible) or purely on case
        autocorrelation (which would mean the weather data is not earning its
        place).
        """
        self._check_fitted()
        model = self._models.get((horizon, quantile))
        if model is None:
            raise ValueError(f"No fitted model for horizon={horizon}, quantile={quantile}")
        return (
            pd.DataFrame(
                {"feature": self._feature_names, "gain": model.booster_.feature_importance("gain")}
            )
            .sort_values("gain", ascending=False)
            .reset_index(drop=True)
        )
