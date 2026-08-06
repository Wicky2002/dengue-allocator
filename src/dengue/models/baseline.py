"""Baseline forecasters: seasonal naive and per-district SARIMA.

These set the bar any learned model has to clear. That matters more than it
might seem: dengue case series are strongly seasonal and strongly
autocorrelated, so a seasonal naive rule is a genuinely competitive forecaster at
2-4 week leads. A gradient-boosted model that does not beat it is not earning its
complexity.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from dengue import config
from dengue.models import (
    PREDICTION_COLUMNS,
    ForecastModel,
    enforce_quantile_monotonicity,
)
from dengue.utils.logging import get_logger

log = get_logger(__name__)

#: Weeks in a seasonal cycle. 52, not 52.18: ISO weeks are what the data is
#: indexed by, and the quarter-week drift is absorbed by the residual spread.
SEASONAL_PERIOD = 52


class SeasonalNaive(ForecastModel):
    """Predict the same ISO week one year earlier.

    The point forecast for district *d* at target week *w* is the observed count
    at ``w - 52`` weeks. Uncertainty is empirical rather than parametric: during
    :meth:`fit` the model collects the distribution of log-ratio errors

    .. math:: r = \\log\\frac{y_t + 1}{y_{t-52} + 1}

    across all districts and weeks, and the 10th/90th percentiles of that
    distribution are applied multiplicatively to the point forecast. So the
    interval width is learned from how badly last-year-same-week has actually
    done historically, which is exactly the right reference for a naive method.

    Pooling residuals across districts is deliberate: individual districts have
    too few year-over-year pairs to estimate a tail quantile stably.

    Parameters
    ----------
    seasonal_period:
        Lag in weeks. Defaults to 52.
    min_residuals:
        Minimum pooled residuals required before empirical quantiles are trusted;
        below this the model falls back to a wide default spread rather than
        pretending to a precision it does not have.
    """

    name = "seasonal_naive"

    def __init__(self, seasonal_period: int = SEASONAL_PERIOD, min_residuals: int = 50) -> None:
        self.seasonal_period = seasonal_period
        self.min_residuals = min_residuals
        self._history: pd.DataFrame | None = None
        self._log_ratio_quantiles: dict[float, float] = {}

    def fit(self, panel: pd.DataFrame) -> SeasonalNaive:
        frame = panel.sort_values(["district_id", "iso_week"]).reset_index(drop=True)
        self._history = frame[["district_id", "iso_week", "cases"]].copy()

        cases = frame["cases"].astype("float64")
        seasonal_lag = (
            frame.groupby("district_id", observed=True)["cases"]
            .shift(self.seasonal_period)
            .astype("float64")
        )

        with np.errstate(invalid="ignore", divide="ignore"):
            residuals = np.log((cases + 1.0) / (seasonal_lag + 1.0))
        residuals = residuals[np.isfinite(residuals)]

        if len(residuals) >= self.min_residuals:
            self._log_ratio_quantiles = {
                q: float(np.quantile(residuals, q)) for q in config.QUANTILES
            }
        else:
            # Not enough year-over-year pairs. A +/-1 log-unit band (roughly a
            # factor of e either way) is honest about that, rather than
            # extrapolating a tail from a handful of points.
            log.warning(
                "seasonal_naive: only %d seasonal residuals available (need %d); "
                "using a wide default interval",
                len(residuals),
                self.min_residuals,
            )
            self._log_ratio_quantiles = {0.1: -1.0, 0.5: 0.0, 0.9: 1.0}

        log.info(
            "seasonal_naive: fitted on %d rows, residual log-ratio quantiles %s",
            len(frame),
            {k: round(v, 3) for k, v in self._log_ratio_quantiles.items()},
        )
        self._fitted = True
        return self

    def predict(self, panel: pd.DataFrame, horizon: int) -> pd.DataFrame:
        self._check_fitted()
        assert self._history is not None

        frame = panel.sort_values(["district_id", "iso_week"]).reset_index(drop=True)
        lookup = {
            (row.district_id, row.iso_week): row.cases
            for row in self._history.itertuples(index=False)
        }
        # Also index the panel we were handed, so origins beyond the fitted
        # history (later backtest folds) still resolve.
        lookup.update(
            {(row.district_id, row.iso_week): row.cases for row in frame.itertuples(index=False)}
        )

        origins = frame.groupby("district_id", observed=True)["iso_week"].max()

        rows: list[dict[str, object]] = []
        for district_id, origin in origins.items():
            target_week = origin + horizon
            reference_week = target_week - self.seasonal_period
            reference = lookup.get((district_id, reference_week))

            if reference is None or pd.isna(reference):
                # No same-week-last-year observation. Fall back to the district's
                # most recent value rather than dropping the district entirely --
                # a missing forecast is worse than a crude one for allocation.
                recent = frame[frame["district_id"] == district_id]["cases"].dropna()
                if recent.empty:
                    continue
                reference = float(recent.iloc[-1])
                log.debug(
                    "seasonal_naive: no %s observation for %s; using last observed value",
                    reference_week,
                    district_id,
                )

            base = float(reference) + 1.0
            row: dict[str, object] = {
                "district_id": district_id,
                "iso_week": origin,
                "target_week": target_week,
                "horizon": horizon,
            }
            for q in config.QUANTILES:
                row[f"q{q}"] = max(base * np.exp(self._log_ratio_quantiles[q]) - 1.0, 0.0)
            rows.append(row)

        if not rows:
            return self._empty_predictions()

        return enforce_quantile_monotonicity(pd.DataFrame(rows)[list(PREDICTION_COLUMNS)])


class SarimaBaseline(ForecastModel):
    """Per-district SARIMA on ``log1p(cases)`` with Fourier seasonal terms.

    Fitted independently per district with :mod:`statsmodels`' ``SARIMAX``.

    On the seasonal specification: a literal weekly seasonal order
    ``(P,D,Q,s=52)`` is close to unusable here -- it adds 52 lags of state per
    district and takes minutes per fit, times 25 districts times every backtest
    fold. The standard remedy, and the one used here, is to model annual
    seasonality with a small set of **Fourier terms** passed as exogenous
    regressors while keeping the ARIMA part non-seasonal. Four harmonic pairs
    capture the two-peak monsoon structure with eight parameters instead of
    fifty-two, and it fits in milliseconds.

    Prediction intervals come from ``get_forecast(...).conf_int(alpha=0.2)``, so
    the 80% interval is read off the model's own predictive distribution on the
    log scale and back-transformed. That makes the interval genuinely
    model-based, unlike :class:`SeasonalNaive`'s empirical band.

    Parameters
    ----------
    order:
        Non-seasonal ``(p, d, q)``. Defaults to ``(1, 1, 1)``.
    n_fourier:
        Number of Fourier harmonic pairs for annual seasonality.
    min_observations:
        Districts with fewer observations are skipped, with a warning; SARIMAX on
        a very short series produces confident nonsense.
    """

    name = "sarima"

    def __init__(
        self,
        order: tuple[int, int, int] = (1, 1, 1),
        n_fourier: int = 4,
        min_observations: int = 60,
    ) -> None:
        self.order = order
        self.n_fourier = n_fourier
        self.min_observations = min_observations
        self._models: dict[str, object] = {}
        self._series: dict[str, pd.Series] = {}

    def _fourier_terms(self, week_of_year: np.ndarray) -> np.ndarray:
        """Fourier design matrix for annual seasonality."""
        columns = []
        for k in range(1, self.n_fourier + 1):
            angle = 2 * np.pi * k * week_of_year / SEASONAL_PERIOD
            columns.append(np.sin(angle))
            columns.append(np.cos(angle))
        return np.column_stack(columns)

    @staticmethod
    def _week_of_year(periods: pd.PeriodIndex) -> np.ndarray:
        return periods.start_time.isocalendar().week.to_numpy(dtype=float)

    def fit(self, panel: pd.DataFrame) -> SarimaBaseline:
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        frame = panel.sort_values(["district_id", "iso_week"]).reset_index(drop=True)
        self._models.clear()
        self._series.clear()

        n_fitted = n_skipped = 0
        for district_id, group in frame.groupby("district_id", observed=True):
            series = group.set_index("iso_week")["cases"].astype("float64")
            if len(series) < self.min_observations:
                log.warning(
                    "sarima: skipping %s (%d observations < %d required)",
                    district_id,
                    len(series),
                    self.min_observations,
                )
                n_skipped += 1
                continue

            endog = np.log1p(series.to_numpy())
            exog = self._fourier_terms(self._week_of_year(pd.PeriodIndex(series.index)))

            try:
                with warnings.catch_warnings():
                    # Convergence chatter per district would drown the log; a
                    # genuinely failed fit still raises and is handled below.
                    warnings.simplefilter("ignore")
                    model = SARIMAX(
                        endog,
                        exog=exog,
                        order=self.order,
                        trend="c",
                        enforce_stationarity=False,
                        enforce_invertibility=False,
                    ).fit(disp=False)
                self._models[str(district_id)] = model
                self._series[str(district_id)] = series
                n_fitted += 1
            except (ValueError, np.linalg.LinAlgError) as exc:
                log.warning("sarima: fit failed for %s: %s", district_id, exc)
                n_skipped += 1

        log.info(
            "sarima: fitted %d districts, skipped %d  order=%s  fourier_pairs=%d",
            n_fitted,
            n_skipped,
            self.order,
            self.n_fourier,
        )
        self._fitted = True
        return self

    def predict(self, panel: pd.DataFrame, horizon: int) -> pd.DataFrame:
        self._check_fitted()

        rows: list[dict[str, object]] = []
        # alpha=0.2 gives the 80% interval, i.e. the 0.1 and 0.9 quantiles.
        alpha = 1.0 - config.PI_NOMINAL_COVERAGE

        for district_id, model in self._models.items():
            series = self._series[district_id]
            origin = pd.PeriodIndex(series.index)[-1]
            target_week = origin + horizon

            future_weeks = pd.period_range(origin + 1, periods=horizon, freq=config.WEEK_FREQ)
            future_exog = self._fourier_terms(self._week_of_year(future_weeks))

            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    forecast = model.get_forecast(steps=horizon, exog=future_exog)
                    mean_log = float(np.asarray(forecast.predicted_mean)[-1])
                    interval = np.asarray(forecast.conf_int(alpha=alpha))[-1]
            except (ValueError, np.linalg.LinAlgError) as exc:
                log.warning("sarima: forecast failed for %s: %s", district_id, exc)
                continue

            rows.append(
                {
                    "district_id": district_id,
                    "iso_week": origin,
                    "target_week": target_week,
                    "horizon": horizon,
                    "q0.1": max(np.expm1(interval[0]), 0.0),
                    "q0.5": max(np.expm1(mean_log), 0.0),
                    "q0.9": max(np.expm1(interval[1]), 0.0),
                }
            )

        if not rows:
            return self._empty_predictions()

        return enforce_quantile_monotonicity(pd.DataFrame(rows)[list(PREDICTION_COLUMNS)])
