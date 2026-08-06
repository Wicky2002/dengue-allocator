"""Synthetic district-week panel with realistic dengue dynamics.

This exists so that the modelling, evaluation, optimisation and app workstreams
can develop in parallel while the real ingest lands, and so that ``make
baseline`` runs end to end with zero network access.

The generated panel has the **identical schema** to the real one
(:data:`dengue.config.PANEL_DTYPES`), so code developed against it works
unchanged on real data.

What is modelled
----------------
*Bimodal seasonality.* Sri Lankan dengue transmission tracks the two monsoons:
the **southwest (Yala)** monsoon breaks in mid-May and drives the larger
June-July peak, mainly in the wet zone; the **northeast (Maha)** monsoon runs
December-February and drives a second peak, relatively more important in the dry
zone (Northern, Eastern, North Central). Each district's two peak amplitudes are
weighted by its climate zone.

*Spatial correlation.* A latent log-risk field is drawn from a Gaussian process
over district centroids with an exponential kernel, then carried through time as
an AR(1). Neighbouring districts therefore share outbreak timing, which is what
makes the neighbour-weighted feature in ``features/build_panel.py`` meaningful
rather than noise.

*Overdispersion.* Weekly counts are negative-binomial around the seasonal mean,
because real notification counts are far more variable than Poisson.

*Climate covariates* are generated from the same monsoon phase that drives
transmission, with rainfall leading cases by roughly 6-8 weeks -- the
approximate lag from breeding-site creation through the vector's aquatic and
extrinsic incubation stages to a notified case.

.. warning::
   Nothing here is real case data. The output is clearly labelled synthetic by
   ``make_synthetic_panel``'s docstring and by the ``synthetic=True`` provenance
   logged when it is used. Never present these numbers as observations.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from dengue import config
from dengue.utils.logging import get_logger

log = get_logger(__name__)

_EARTH_RADIUS_KM = 6371.0

#: Climate-zone weighting of the two monsoon peaks. Values are
#: ``(southwest_weight, northeast_weight)`` multipliers on the seasonal bumps.
_WET_ZONE = frozenset(
    {
        "colombo",
        "gampaha",
        "kalutara",
        "galle",
        "matara",
        "ratnapura",
        "kegalle",
        "kandy",
        "nuwara_eliya",
    }
)
_DRY_ZONE = frozenset(
    {
        "jaffna",
        "kilinochchi",
        "mullaitivu",
        "mannar",
        "vavuniya",
        "anuradhapura",
        "polonnaruwa",
        "trincomalee",
        "batticaloa",
        "ampara",
        "hambantota",
        "monaragala",
        "puttalam",
    }
)


def _zone_weights(district_id: str) -> tuple[float, float]:
    """Return ``(sw_weight, ne_weight)`` monsoon peak weights for a district."""
    if district_id in _WET_ZONE:
        return 1.00, 0.45
    if district_id in _DRY_ZONE:
        return 0.55, 0.95
    return 0.80, 0.70  # intermediate zone


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlam / 2) ** 2
    return float(2 * _EARTH_RADIUS_KM * np.arcsin(np.sqrt(a)))


def _spatial_covariance(
    coords: list[tuple[float, float]], *, length_scale_km: float = 80.0
) -> np.ndarray:
    """Exponential-kernel covariance over district centroids.

    ``k(d) = exp(-d / length_scale)``. The exponential kernel is positive
    definite, and an 80 km length scale means adjacent districts (typically
    50-90 km apart in Sri Lanka) correlate at roughly 0.35-0.55 -- strong enough
    for spatial pooling to help, weak enough that districts stay distinguishable.
    """
    n = len(coords)
    cov = np.empty((n, n), dtype=float)
    for i in range(n):
        for j in range(i, n):
            d = _haversine_km(*coords[i], *coords[j])
            value = np.exp(-d / length_scale_km)
            cov[i, j] = cov[j, i] = value
    # Nugget for numerical stability of the Cholesky factor.
    cov[np.diag_indices(n)] += 1e-6
    return cov


def _correlated_ar1(
    n_weeks: int,
    cov: np.ndarray,
    rng: np.random.Generator,
    *,
    phi: float = 0.72,
    sigma: float = 0.34,
) -> np.ndarray:
    """AR(1)-in-time, spatially-correlated latent field, shape ``(n_weeks, n)``.

    ``phi = 0.72`` gives an epidemic-risk autocorrelation half-life of about two
    weeks, which is roughly what district-level dengue series show once
    seasonality is removed.
    """
    n = cov.shape[0]
    try:
        chol = np.linalg.cholesky(cov)
    except np.linalg.LinAlgError:  # pragma: no cover - defensive
        eigvals, eigvecs = np.linalg.eigh(cov)
        chol = eigvecs @ np.diag(np.sqrt(np.clip(eigvals, 1e-10, None)))

    field = np.empty((n_weeks, n), dtype=float)
    # Start from the AR(1) stationary distribution so there is no burn-in ramp.
    state = (chol @ rng.standard_normal(n)) * sigma / np.sqrt(1 - phi**2)
    for t in range(n_weeks):
        shock = (chol @ rng.standard_normal(n)) * sigma
        state = phi * state + shock
        field[t] = state
    return field


def _seasonal_curve(week_of_year: np.ndarray, sw_weight: float, ne_weight: float) -> np.ndarray:
    """Two-peak annual seasonality on the log scale.

    Peaks are wrapped Gaussians centred on ISO week 26 (late June, following the
    southwest monsoon onset) and ISO week 51 (late December, following the
    northeast monsoon onset).
    """

    def wrapped_bump(centre: float, width: float) -> np.ndarray:
        delta = np.abs(week_of_year - centre)
        delta = np.minimum(delta, 52.0 - delta)  # wrap around the year boundary
        return np.exp(-0.5 * (delta / width) ** 2)

    return sw_weight * wrapped_bump(26.0, 6.5) + ne_weight * wrapped_bump(51.0, 5.0)


def make_synthetic_panel(
    n_districts: int = 25,
    n_weeks: int = 730,
    seed: int = config.RANDOM_SEED,
    *,
    end_week: str | pd.Period | None = None,
    high_risk_top_k: int = 6,
    high_risk_missing_frac: float = 0.15,
) -> pd.DataFrame:
    """Generate a synthetic district-week panel matching the frozen schema.

    Parameters
    ----------
    n_districts:
        How many districts to emit, taken from the head of
        :data:`dengue.config.DISTRICTS`. Defaults to all 25. Values above 25 are
        rejected rather than fabricating districts that do not exist.
    n_weeks:
        Number of consecutive ISO weeks. The default 730 (~14 years) ending in
        the current week spans the default backtest folds comfortably.
    seed:
        Seed for the random generator; the output is exactly reproducible.
    end_week:
        Last week in the panel. Defaults to the most recently completed ISO week.
    high_risk_top_k:
        Number of districts flagged high-risk each week (by incidence rank),
        mimicking the NDCU's designation of high-burden reporting areas.
    high_risk_missing_frac:
        Fraction of district-weeks where ``high_risk_flag`` is left null, mimicking
        the real situation where NDCU designations are unavailable for some weeks.

    Returns
    -------
    pandas.DataFrame
        A panel conforming exactly to :data:`dengue.config.PANEL_DTYPES`, sorted
        by ``(district_id, iso_week)``.

    Notes
    -----
    **This is simulated data, not observations.** It exists for pipeline
    development and offline CI. Never report metrics from it as real-world
    performance.

    Examples
    --------
    >>> panel = make_synthetic_panel(n_districts=5, n_weeks=104, seed=0)
    >>> list(panel.columns) == list(config.PANEL_COLUMNS)
    True
    """
    if n_districts > len(config.DISTRICTS):
        raise ValueError(
            f"n_districts={n_districts} exceeds the {len(config.DISTRICTS)} real districts. "
            "Refusing to invent districts that do not exist."
        )
    if n_weeks < 2:
        raise ValueError("n_weeks must be at least 2")

    rng = np.random.default_rng(seed)
    districts = list(config.DISTRICTS[:n_districts])
    n = len(districts)

    # ---- time index -------------------------------------------------------
    if end_week is None:
        # Most recently *completed* ISO week, so the panel never contains a
        # partially-observed week.
        end_period = pd.Period(pd.Timestamp.today(), freq=config.WEEK_FREQ) - 1
    else:
        end_period = pd.Period(end_week, freq=config.WEEK_FREQ)
    weeks = pd.period_range(end=end_period, periods=n_weeks, freq=config.WEEK_FREQ)
    week_of_year = np.array([w.start_time.isocalendar()[1] for w in weeks], dtype=float)

    # ---- latent spatially-correlated epidemic risk ------------------------
    coords = [(d.lat, d.lon) for d in districts]
    cov = _spatial_covariance(coords)
    latent = _correlated_ar1(n_weeks, cov, rng)  # (n_weeks, n)

    # A slow multi-year cycle: serotype replacement drives 3-4 year epidemic
    # waves in Sri Lanka, which is why single-year seasonality alone underfits.
    t = np.arange(n_weeks, dtype=float)
    multiyear = 0.45 * np.sin(2 * np.pi * t / (52.0 * 3.5) + rng.uniform(0, 2 * np.pi))

    records: list[pd.DataFrame] = []

    for j, d in enumerate(districts):
        sw_w, ne_w = _zone_weights(d.district_id)
        seasonal = _seasonal_curve(week_of_year, sw_w, ne_w)

        # --- climate ------------------------------------------------------
        # Rainfall follows the same monsoon phases; the wet zone gets a heavier
        # southwest signal, the dry zone a heavier northeast one.
        rain_seasonal = 42.0 * _seasonal_curve(week_of_year, sw_w, ne_w * 1.25)
        rain_base = 14.0 if d.district_id in _DRY_ZONE else 24.0
        rain = rng.gamma(shape=np.clip((rain_base + rain_seasonal) / 12.0, 0.25, None), scale=12.0)
        rain = np.round(rain, 1)

        # Temperature: highland districts are markedly cooler. Nuwara Eliya sits
        # at ~1900 m and runs 8-10 C below the coastal lowlands.
        highland_offset = {"nuwara_eliya": -9.0, "kandy": -3.5, "badulla": -4.0, "matale": -2.0}
        offset = highland_offset.get(d.district_id, 0.0)
        annual = np.cos(2 * np.pi * (week_of_year - 14.0) / 52.0)
        tmax = 31.6 + offset + 1.8 * annual - 0.018 * rain + rng.normal(0, 0.85, n_weeks)
        tmin = 24.4 + offset + 1.2 * annual - 0.010 * rain + rng.normal(0, 0.70, n_weeks)
        # Guarantee the physical invariant tmin < tmax after noise.
        tmin = np.minimum(tmin, tmax - 1.5)
        rh = np.clip(74.0 + 0.16 * rain + 2.5 * annual + rng.normal(0, 3.0, n_weeks), 45.0, 99.0)

        # --- lagged rainfall drives transmission ---------------------------
        # ~7 weeks: breeding-site creation -> larval development -> adult vector
        # -> extrinsic incubation -> human infection -> notification.
        rain_lag = np.concatenate([np.full(7, rain[:7].mean()), rain[:-7]])
        rain_effect = 0.0045 * (rain_lag - rain_lag.mean())

        # --- expected counts ----------------------------------------------
        # Urban districts carry structurally higher incidence: Aedes aegypti is
        # strongly container- and city-associated.
        density_term = 0.32 * np.log1p(d.density_per_km2 / 400.0)
        base_rate = np.log(d.population / 100_000.0) - 0.55

        log_mu = base_rate + density_term + 1.15 * seasonal + multiyear + rain_effect + latent[:, j]
        mu = np.exp(np.clip(log_mu, -4.0, 9.0))

        # Negative binomial via Gamma-Poisson mixture; dispersion r=6 gives the
        # heavy weekly variability that real notification series show.
        dispersion = 6.0
        rate = rng.gamma(shape=dispersion, scale=mu / dispersion)
        cases = rng.poisson(rate)

        records.append(
            pd.DataFrame(
                {
                    "district_id": d.district_id,
                    "iso_week": weeks,
                    "cases": cases.astype("int64"),
                    "population": d.population,
                    "rain_mm": rain,
                    "tmax": np.round(tmax, 2),
                    "tmin": np.round(tmin, 2),
                    "rh": np.round(rh, 1),
                }
            )
        )

    panel = pd.concat(records, ignore_index=True)

    # ---- high-risk flag ---------------------------------------------------
    # Mimics the NDCU designating the highest-incidence reporting areas as
    # high-risk each week. Computed from *contemporaneous* incidence, matching
    # how the real designation works (it is a status, not a forecast).
    panel["incidence"] = panel["cases"] / panel["population"] * 100_000.0
    rank = panel.groupby("iso_week", observed=True)["incidence"].rank(
        ascending=False, method="first"
    )
    flag = (rank <= high_risk_top_k).astype("boolean")

    # Null out a fraction of weeks entirely, mirroring gaps in NDCU publication
    # rather than dropping individual districts (which would be unrealistic).
    unique_weeks = panel["iso_week"].unique()
    n_missing_weeks = int(round(len(unique_weeks) * high_risk_missing_frac))
    missing_weeks = set(rng.choice(unique_weeks, size=n_missing_weeks, replace=False))
    flag = flag.mask(panel["iso_week"].isin(missing_weeks), other=pd.NA)

    panel["high_risk_flag"] = flag
    panel = panel.drop(columns=["incidence"])

    from dengue.utils.io import coerce_panel_schema  # local import avoids a cycle

    panel = coerce_panel_schema(panel)

    log.info(
        "synthetic panel generated  synthetic=True  districts=%d  weeks=%d  rows=%d  "
        "range=[%s .. %s]  cases_total=%s  seed=%d",
        n,
        n_weeks,
        len(panel),
        panel["iso_week"].min(),
        panel["iso_week"].max(),
        f"{int(panel['cases'].sum()):,}",
        seed,
    )
    return panel


if __name__ == "__main__":  # pragma: no cover - manual smoke check
    from dengue.utils.io import write_panel

    config.ensure_dirs()
    write_panel(make_synthetic_panel())
