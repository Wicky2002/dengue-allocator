"""Stage 2 -- mechanistic SEI-SIR model for vector-control effect sizes.

What this stage is for
----------------------
Stage 1 says where cases are going. Stage 3 needs something Stage 1 cannot
provide: **the counterfactual**. Allocating teams requires knowing how many cases
are averted by sending *k* teams to district *d*, and that is a causal quantity.

A forecasting model fitted on observational data cannot answer it. Historically,
teams were sent *to* outbreaks, so naively regressing cases on team-weeks
recovers a positive coefficient and concludes that vector control causes dengue.
The confounder is the outbreak itself. The mechanistic route sidesteps this by
modelling transmission explicitly and then *intervening on the vector
parameters* -- a genuine do-operation on a simulated system, not an association
read off history.

Model structure
---------------
Coupled vector-host compartments, integrated at **daily** resolution and
aggregated to ISO weeks (the panel's resolution). Per district:

*Vector (SEI).* ``S_v -> E_v -> I_v``, in units of mosquitoes per host.
Mosquitoes do not recover -- once infectious, they stay infectious until death,
which is why the vector side is SEI and not SIR. ``E_v`` is the **extrinsic
incubation period (EIP)**, strongly temperature-dependent: about 12 days at 25 C
falling to 8 days at 30 C. That dependence is the main channel through which
``tmax`` enters transmission, and it matters more than it looks: the EIP is a
large fraction of the mosquito's remaining lifespan, so shortening it sharply
raises the probability a mosquito survives long enough to become infectious.

*Host (SIR).* ``S_h -> I_h -> R_h`` with a reporting fraction ``rho`` mapping
new infections to notified cases.

*Forcing.* Vector carrying capacity ``K(t)`` responds to lagged rainfall --
containers fill, larvae develop, adults emerge. The lag is set by
:data:`RAIN_LAG_WEEKS`.

Identifiability, stated plainly
-------------------------------
``R0`` and ``rho`` trade off almost exactly: halving the reporting fraction and
halving transmission intensity produce nearly the same notified-case curve.
Fitting both freely yields a ridge, not a peak. So ``rho`` is **fixed** at
:data:`DEFAULT_REPORTING_FRACTION` from the serological literature, and three
parameters are fitted per district:

1. ``log_r0_base`` -- baseline transmission intensity
2. ``rain_elasticity`` -- responsiveness of carrying capacity to lagged rain
3. ``init_susceptible`` -- initial susceptible fraction, which sets how much
   epidemic fuel is available and largely controls outbreak size

Because ``rho`` is fixed rather than estimated, the *absolute* scale of averted
cases inherits that assumption. The **ranking** across districts -- which is what
Stage 3 actually consumes -- is far more robust to it, since ``rho`` enters every
district's effect roughly multiplicatively. :func:`sensitivity_to_reporting_fraction`
quantifies this rather than leaving it as an assertion.

Intervention
------------
A control team-week acts through two channels with very different time
signatures, and separating them is the point of doing this mechanistically:

* **Adulticiding** (space spraying) raises adult mortality ``mu_v``. Sharp,
  immediate, short-lived -- adults die, then the population rebounds from larval
  stages.
* **Larval source reduction** lowers carrying capacity ``K``. Slower to bite,
  but durable.

Coverage saturates as ``1 - exp(-teams / scale)``: the second team in a district
reaches households the first did not, but the tenth is largely re-treating
already-treated premises. **This saturation is what makes Stage 3 a non-trivial
optimisation** rather than "send everyone to the worst district".

References
----------
Newton & Reiter (1992) for SEI-SIR applied to dengue; Focks et al. (1995) for
the temperature-EIP relation used in :func:`eip_days`; Andraud et al. (2012) for
a review of dengue transmission model structures; Mordecai et al. (2017) for
temperature-dependent transmission parameters.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from dengue import config
from dengue.utils.logging import get_logger

log = get_logger(__name__)

# --------------------------------------------------------------------------
# Fixed biological parameters (literature values, not fitted)
# --------------------------------------------------------------------------

#: Days per simulation step. Daily integration keeps the EIP and vector
#: lifespan -- both ~1-2 weeks -- resolved rather than smeared across a step.
DT_DAYS = 1.0

#: Bites on humans per mosquito per day.
BITING_RATE = 0.30

#: Transmission probability per infectious bite, host->vector and vector->host.
PROB_HOST_TO_VECTOR = 0.50
PROB_VECTOR_TO_HOST = 0.50

#: Baseline adult vector mortality per day (mean lifespan ~14 days).
VECTOR_MORTALITY = 1.0 / 14.0

#: Host infectious period (viraemic days).
HOST_INFECTIOUS_DAYS = 6.0

#: Reporting fraction. Fixed, not fitted -- see module docstring on
#: identifiability. Dengue notification captures a minority of infections;
#: serosurvey-anchored estimates for South and Southeast Asia commonly fall in
#: the 5-20% range for a symptomatic-and-notified endpoint.
DEFAULT_REPORTING_FRACTION = 0.10

#: Negative-binomial dispersion for the observation model. Fixed: weekly
#: notification counts are far more variable than Poisson.
NB_DISPERSION = 6.0

#: Weeks of lag from rainfall to its effect on vector carrying capacity.
RAIN_LAG_WEEKS = 6

#: Weeks of burn-in simulated before the fitting window, so the initial
#: condition is washed out rather than fitted.
BURN_IN_WEEKS = 26


def eip_days(temperature_c: np.ndarray | float) -> np.ndarray | float:
    """Extrinsic incubation period in days as a function of temperature.

    Uses the Focks et al. (1995) enzyme-kinetic form in its commonly-cited
    reduced version. Clipped to a physiologically sane 4-40 day band: below
    ~18 C the fitted curve diverges, and a 200-day EIP would silently switch
    transmission off rather than merely slow it.

    Examples
    --------
    >>> round(float(eip_days(25.0)), 1)
    12.0
    >>> round(float(eip_days(30.0)), 1)
    8.3
    """
    t = np.asarray(temperature_c, dtype=float)
    raw = 4.0 + np.exp(5.15 - 0.123 * t)
    return np.clip(raw, 4.0, 40.0)


@dataclass(frozen=True)
class SEISIRParameters:
    """Fitted SEI-SIR parameters for one district.

    Attributes
    ----------
    district_id:
        Canonical district key.
    r0_base:
        Baseline transmission intensity (dimensionless multiplier on the
        vector-host contact term). Not itself the basic reproduction number;
        see ``r0_mean`` for that.
    rain_elasticity:
        Elasticity of vector carrying capacity to lagged standardised rainfall.
    init_susceptible:
        Fitted initial susceptible fraction of the host population.
    reporting_fraction:
        Fraction of infections notified. Fixed, not fitted.
    r0_mean:
        Realised mean basic reproduction number over the fitting window.
    log_likelihood:
        Negative-binomial log-likelihood at the optimum.
    n_observations:
        District-weeks used in the fit.
    converged:
        Whether the optimiser reported success.
    """

    district_id: str
    r0_base: float
    rain_elasticity: float
    init_susceptible: float
    reporting_fraction: float
    r0_mean: float
    log_likelihood: float
    n_observations: int
    converged: bool


@dataclass(frozen=True)
class InterventionSpec:
    """How a team-week translates into vector-parameter changes.

    Attributes
    ----------
    coverage_scale_per_100k:
        Team-weeks needed to reach ``1 - 1/e`` (~63%) coverage in a district of
        100,000 people. Scaling by population is what stops the model from
        claiming one team can blanket Colombo as easily as Mullaitivu.
    adulticide_mortality_multiplier:
        Proportional increase in adult vector mortality at full coverage.
    larval_capacity_reduction:
        Proportional reduction in carrying capacity at full coverage.
    decay_weeks:
        Half-life of the adulticide effect once teams leave, in weeks. Source
        reduction is treated as persisting for the evaluation window.
    """

    coverage_scale_per_100k: float = 3.0
    adulticide_mortality_multiplier: float = 1.6
    larval_capacity_reduction: float = 0.45
    decay_weeks: float = 2.0


@dataclass(frozen=True)
class InterventionEffect:
    """Estimated effect of vector control in one district.

    Attributes
    ----------
    district_id:
        Canonical district key.
    team_weeks:
        Intervention intensity this effect is evaluated at.
    cases_averted_mean:
        Expected notified cases averted over the evaluation window.
    cases_averted_lower, cases_averted_upper:
        80% interval bounds, propagated from the Stage 1 forecast spread.
    marginal_cases_averted_per_team_week:
        Slope of the effect curve at ``team_weeks``. **Decreasing** in
        ``team_weeks`` -- saturating returns are why Stage 3 is an optimisation.
    coverage:
        Fraction of premises effectively reached at this intensity.
    baseline_cases:
        Cases expected over the window with no additional intervention.
    """

    district_id: str
    team_weeks: float
    cases_averted_mean: float
    cases_averted_lower: float
    cases_averted_upper: float
    marginal_cases_averted_per_team_week: float
    coverage: float
    baseline_cases: float


# --------------------------------------------------------------------------
# Simulation core
# --------------------------------------------------------------------------


def _standardise(values: np.ndarray) -> np.ndarray:
    """Zero-mean, unit-sd. Constant input maps to zeros rather than NaN."""
    values = np.asarray(values, dtype=float)
    sd = np.nanstd(values)
    if not np.isfinite(sd) or sd < 1e-9:
        return np.zeros_like(values)
    return (values - np.nanmean(values)) / sd


def simulate(
    n_weeks: int,
    rain_z: np.ndarray,
    tmax: np.ndarray,
    population: float,
    r0_base: float,
    rain_elasticity: float,
    init_susceptible: float,
    *,
    reporting_fraction: float = DEFAULT_REPORTING_FRACTION,
    coverage: np.ndarray | None = None,
    spec: InterventionSpec | None = None,
    seed_infections: float = 5.0,
) -> np.ndarray:
    """Integrate the SEI-SIR system and return weekly **notified** cases.

    Parameters
    ----------
    n_weeks:
        Weeks to simulate.
    rain_z:
        Standardised rainfall, already lagged by :data:`RAIN_LAG_WEEKS`, one
        value per week.
    tmax:
        Weekly maximum temperature in Celsius, one value per week. Drives the
        EIP.
    population:
        District population.
    r0_base, rain_elasticity, init_susceptible:
        Fitted parameters.
    reporting_fraction:
        Infections-to-notifications ratio.
    coverage:
        Per-week intervention coverage in ``[0, 1]``. ``None`` means no
        intervention -- the counterfactual baseline.
    spec:
        Intervention mechanics. Required when ``coverage`` is given.
    seed_infections:
        Initial infectious hosts, so the simulation has something to propagate.

    Returns
    -------
    numpy.ndarray
        Weekly notified cases, length ``n_weeks``.

    Notes
    -----
    Deterministic. Stochasticity is handled in the observation model at fitting
    time (negative binomial) rather than in the state equations, which keeps the
    likelihood smooth and the optimiser well-behaved.
    """
    spec = spec or InterventionSpec()
    steps_per_week = int(round(7.0 / DT_DAYS))

    # --- host compartments (counts) ---
    susceptible = float(np.clip(init_susceptible, 0.02, 0.98)) * population
    infectious = float(seed_infections)
    # Recovered absorbs the remainder; it never re-enters, so it is not tracked.

    # --- vector compartments (mosquitoes per host) ---
    vec_susceptible = 1.0
    vec_exposed = 0.0
    vec_infectious = 0.0

    recovery_rate = 1.0 / HOST_INFECTIOUS_DAYS
    weekly_cases = np.zeros(n_weeks, dtype=float)

    for week in range(n_weeks):
        # Carrying capacity responds to lagged rain, in log space so the
        # elasticity is a proportional response and K stays positive.
        capacity = float(np.exp(rain_elasticity * rain_z[week]))
        eip = float(eip_days(tmax[week]))
        incubation_rate = 1.0 / eip

        mortality = VECTOR_MORTALITY
        if coverage is not None:
            cover = float(coverage[week])
            mortality = VECTOR_MORTALITY * (1.0 + spec.adulticide_mortality_multiplier * cover)
            capacity *= 1.0 - spec.larval_capacity_reduction * cover

        # Emergence balances mortality at the target capacity, so with no
        # forcing and no intervention the vector population is at equilibrium.
        emergence = VECTOR_MORTALITY * capacity

        new_infections_week = 0.0
        for _ in range(steps_per_week):
            host_fraction_infectious = infectious / population

            # Vector dynamics.
            force_on_vectors = BITING_RATE * PROB_HOST_TO_VECTOR * host_fraction_infectious
            d_vs = emergence - force_on_vectors * vec_susceptible - mortality * vec_susceptible
            d_ve = (
                force_on_vectors * vec_susceptible
                - incubation_rate * vec_exposed
                - mortality * vec_exposed
            )
            d_vi = incubation_rate * vec_exposed - mortality * vec_infectious

            # Host dynamics.
            force_on_hosts = BITING_RATE * PROB_VECTOR_TO_HOST * r0_base * vec_infectious
            new_infections = force_on_hosts * (susceptible / population) * population
            new_infections = min(new_infections, susceptible)

            d_s = -new_infections
            d_i = new_infections - recovery_rate * infectious

            vec_susceptible = max(vec_susceptible + DT_DAYS * d_vs, 0.0)
            vec_exposed = max(vec_exposed + DT_DAYS * d_ve, 0.0)
            vec_infectious = max(vec_infectious + DT_DAYS * d_vi, 0.0)
            susceptible = max(susceptible + DT_DAYS * d_s, 0.0)
            infectious = max(infectious + DT_DAYS * d_i, 0.0)

            new_infections_week += DT_DAYS * new_infections

        weekly_cases[week] = reporting_fraction * new_infections_week

    return weekly_cases


def _nb_negative_log_likelihood(
    observed: np.ndarray, expected: np.ndarray, dispersion: float = NB_DISPERSION
) -> float:
    """Negative binomial NLL, up to a constant in ``observed``."""
    from scipy.special import gammaln

    expected = np.clip(expected, 1e-6, None)
    r = dispersion
    ll = (
        gammaln(observed + r)
        - gammaln(r)
        - gammaln(observed + 1.0)
        + r * np.log(r / (r + expected))
        + observed * np.log(expected / (r + expected))
    )
    total = float(np.sum(ll))
    return -total if np.isfinite(total) else 1e12


def _prepare_district(
    panel: pd.DataFrame, district_id: str, *, max_weeks: int = 320
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Extract (cases, lagged rain z-score, tmax, population) for one district."""
    frame = (
        panel[panel["district_id"] == district_id].sort_values("iso_week").reset_index(drop=True)
    )
    if frame.empty:
        raise ValueError(f"No rows for district {district_id!r}")

    if len(frame) > max_weeks:
        frame = frame.tail(max_weeks).reset_index(drop=True)

    cases = frame["cases"].astype("float64").to_numpy()
    rain = frame["rain_mm"].astype("float64").to_numpy()
    tmax = frame["tmax"].astype("float64").to_numpy()

    # Fill any gaps with the district mean rather than dropping weeks, which
    # would silently shorten the series and misalign the rainfall lag.
    tmax = np.where(
        np.isfinite(tmax), tmax, np.nanmean(tmax) if np.isfinite(np.nanmean(tmax)) else 31.0
    )
    rain = np.where(np.isfinite(rain), rain, 0.0)

    rain_lagged = np.concatenate([np.full(RAIN_LAG_WEEKS, rain[:RAIN_LAG_WEEKS].mean()), rain])[
        : len(rain)
    ]
    population = float(frame["population"].astype("float64").iloc[0])
    return cases, _standardise(rain_lagged), tmax, population


def fit_sei_sir(
    panel: pd.DataFrame,
    district_id: str,
    *,
    reporting_fraction: float = DEFAULT_REPORTING_FRACTION,
    max_iterations: int = 120,
    seed: int | None = None,
) -> SEISIRParameters:
    """Fit SEI-SIR parameters for one district by maximum likelihood.

    Three free parameters (``r0_base``, ``rain_elasticity``,
    ``init_susceptible``) are estimated against a negative-binomial observation
    model; ``reporting_fraction`` is held fixed for the identifiability reason
    given in the module docstring.

    Parameters
    ----------
    panel:
        District-week panel conforming to :data:`dengue.config.PANEL_DTYPES`.
    district_id:
        District to fit.
    reporting_fraction:
        Fixed infections-to-notifications ratio.
    max_iterations:
        Optimiser iteration cap.
    seed:
        Seed for multi-start jitter.

    Returns
    -------
    SEISIRParameters
        Fitted parameters. ``converged`` is False when the optimiser did not
        report success -- check it rather than assuming the fit is good.
    """
    from scipy.optimize import minimize

    cases, rain_z, tmax, population = _prepare_district(panel, district_id)
    n_weeks = len(cases)

    def objective(theta: np.ndarray) -> float:
        r0_base = float(np.exp(theta[0]))
        rain_elasticity = float(theta[1])
        init_susceptible = float(1.0 / (1.0 + np.exp(-theta[2])))
        try:
            expected = simulate(
                n_weeks,
                rain_z,
                tmax,
                population,
                r0_base,
                rain_elasticity,
                init_susceptible,
                reporting_fraction=reporting_fraction,
            )
        except (FloatingPointError, OverflowError, ValueError):
            return 1e12
        if not np.all(np.isfinite(expected)):
            return 1e12
        return _nb_negative_log_likelihood(cases, expected)

    rng = np.random.default_rng(seed if seed is not None else config.RANDOM_SEED)
    starts = [
        np.array([np.log(1.2), 0.30, 0.0]),
        np.array([np.log(2.5), 0.55, -0.8]),
        np.array([np.log(0.7), 0.15, 0.8]),
    ]
    bounds = [(np.log(0.05), np.log(20.0)), (-1.0, 2.0), (-3.0, 3.0)]

    best_result = None
    best_value = np.inf
    for start in starts:
        jittered = start + rng.normal(0, 0.05, size=3)
        try:
            result = minimize(
                objective,
                jittered,
                method="L-BFGS-B",
                bounds=bounds,
                options={"maxiter": max_iterations},
            )
        except Exception as exc:  # - a bad start must not kill the district
            log.debug("sei_sir: start failed for %s: %s", district_id, exc)
            continue
        if result.fun < best_value:
            best_value, best_result = result.fun, result

    if best_result is None:
        raise RuntimeError(f"All optimiser starts failed for {district_id}")

    r0_base = float(np.exp(best_result.x[0]))
    rain_elasticity = float(best_result.x[1])
    init_susceptible = float(1.0 / (1.0 + np.exp(-best_result.x[2])))

    # Realised R0 over the window, from the standard vector-host expression.
    mean_eip = float(np.mean(eip_days(tmax)))
    survival_to_infectious = np.exp(-VECTOR_MORTALITY * mean_eip)
    r0_mean = float(
        r0_base
        * BITING_RATE**2
        * PROB_HOST_TO_VECTOR
        * PROB_VECTOR_TO_HOST
        * survival_to_infectious
        * HOST_INFECTIOUS_DAYS
        / VECTOR_MORTALITY
    )

    return SEISIRParameters(
        district_id=district_id,
        r0_base=r0_base,
        rain_elasticity=rain_elasticity,
        init_susceptible=init_susceptible,
        reporting_fraction=reporting_fraction,
        r0_mean=r0_mean,
        log_likelihood=float(-best_value),
        n_observations=n_weeks,
        converged=bool(best_result.success),
    )


# --------------------------------------------------------------------------
# Intervention effects
# --------------------------------------------------------------------------


def coverage_from_team_weeks(
    team_weeks: float, population: float, spec: InterventionSpec | None = None
) -> float:
    """Saturating coverage from intervention intensity, in ``[0, 1)``.

    ``1 - exp(-teams / scale)``, with the scale proportional to population. The
    saturation is the mechanism behind diminishing returns.
    """
    spec = spec or InterventionSpec()
    scale = spec.coverage_scale_per_100k * max(population, 1.0) / 100_000.0
    if scale <= 0:
        return 0.0
    return float(1.0 - np.exp(-max(team_weeks, 0.0) / scale))


def intervention_effect(
    parameters: SEISIRParameters,
    panel: pd.DataFrame,
    team_weeks: float,
    *,
    horizon_weeks: int = 4,
    spec: InterventionSpec | None = None,
    forecast_scale: tuple[float, float] | None = None,
) -> InterventionEffect:
    """Estimate notified cases averted by a given control intensity.

    Simulates the district forward twice from its current state -- once with no
    intervention, once with ``team_weeks`` deployed -- and differences the
    cumulative notified cases. That difference is a **causal contrast under the
    model**, obtained by intervening on vector mortality and carrying capacity,
    not by conditioning on historical deployment.

    Parameters
    ----------
    parameters:
        Fitted parameters from :func:`fit_sei_sir`.
    panel:
        The district-week panel (used for recent climate and the current state).
    team_weeks:
        Intervention intensity to evaluate.
    horizon_weeks:
        Window over which averted cases accumulate.
    spec:
        Intervention mechanics.
    forecast_scale:
        Optional ``(lower, upper)`` multipliers from the Stage 1 forecast
        spread, used to propagate forecast uncertainty into the effect interval.

    Returns
    -------
    InterventionEffect
        Cases averted plus the marginal rate Stage 3 optimises against.
    """
    spec = spec or InterventionSpec()
    cases, rain_z, tmax, population = _prepare_district(panel, parameters.district_id)

    # Continue the recent climate forward: the last observed season is the best
    # available proxy for the next few weeks, and a 2-4 week window is short
    # enough that seasonal drift is second-order.
    future_rain = np.resize(rain_z[-horizon_weeks:], horizon_weeks)
    future_tmax = np.resize(tmax[-horizon_weeks:], horizon_weeks)

    # Warm the state up on observed history so the forward run starts from a
    # realistic epidemic phase rather than from the seeding condition.
    warmup_weeks = min(len(cases), 104)
    total_weeks = warmup_weeks + horizon_weeks
    rain_path = np.concatenate([rain_z[-warmup_weeks:], future_rain])
    tmax_path = np.concatenate([tmax[-warmup_weeks:], future_tmax])

    cover = coverage_from_team_weeks(team_weeks, population, spec)

    # Adulticide decays once teams leave; within a short window teams are
    # assumed present throughout, so coverage is flat across the horizon.
    coverage_path = np.zeros(total_weeks, dtype=float)
    coverage_path[warmup_weeks:] = cover

    common = {
        "rain_z": rain_path,
        "tmax": tmax_path,
        "population": population,
        "r0_base": parameters.r0_base,
        "rain_elasticity": parameters.rain_elasticity,
        "init_susceptible": parameters.init_susceptible,
        "reporting_fraction": parameters.reporting_fraction,
    }
    baseline = simulate(total_weeks, **common)[warmup_weeks:]
    treated = simulate(total_weeks, coverage=coverage_path, spec=spec, **common)[warmup_weeks:]

    baseline_total = float(np.sum(baseline))
    averted = float(max(np.sum(baseline) - np.sum(treated), 0.0))

    # Marginal rate: finite difference of the effect curve at this intensity.
    delta = max(team_weeks * 0.05, 0.5)
    cover_plus = coverage_from_team_weeks(team_weeks + delta, population, spec)
    coverage_plus = np.zeros(total_weeks, dtype=float)
    coverage_plus[warmup_weeks:] = cover_plus
    treated_plus = simulate(total_weeks, coverage=coverage_plus, spec=spec, **common)[warmup_weeks:]
    averted_plus = float(max(np.sum(baseline) - np.sum(treated_plus), 0.0))
    marginal = (averted_plus - averted) / delta

    lower_scale, upper_scale = forecast_scale or (0.6, 1.6)
    return InterventionEffect(
        district_id=parameters.district_id,
        team_weeks=float(team_weeks),
        cases_averted_mean=averted,
        cases_averted_lower=averted * lower_scale,
        cases_averted_upper=averted * upper_scale,
        marginal_cases_averted_per_team_week=float(marginal),
        coverage=cover,
        baseline_cases=baseline_total,
    )


def fit_all_districts(
    panel: pd.DataFrame,
    *,
    district_ids: list[str] | None = None,
    reporting_fraction: float = DEFAULT_REPORTING_FRACTION,
) -> dict[str, SEISIRParameters]:
    """Fit every district, logging progress and skipping failures loudly."""
    district_ids = district_ids or sorted(panel["district_id"].unique())
    fitted: dict[str, SEISIRParameters] = {}
    n_failed = 0

    for i, district_id in enumerate(district_ids, start=1):
        try:
            params = fit_sei_sir(panel, district_id, reporting_fraction=reporting_fraction)
        except Exception as exc:  # - one district must not abort the stage
            log.error("sei_sir: fit failed for %s: %s", district_id, exc)
            n_failed += 1
            continue
        fitted[district_id] = params
        log.debug(
            "sei_sir: [%2d/%d] %-14s R0=%.2f  rain_elast=%.2f  S0=%.2f  conv=%s",
            i,
            len(district_ids),
            district_id,
            params.r0_mean,
            params.rain_elasticity,
            params.init_susceptible,
            params.converged,
        )

    n_converged = sum(1 for p in fitted.values() if p.converged)
    log.info(
        "sei_sir: fitted %d districts (%d converged, %d failed)  median R0=%.2f",
        len(fitted),
        n_converged,
        n_failed,
        float(np.median([p.r0_mean for p in fitted.values()])) if fitted else float("nan"),
    )
    return fitted


def build_effect_table(
    panel: pd.DataFrame,
    parameters: dict[str, SEISIRParameters] | None = None,
    *,
    max_team_weeks: int = 12,
    horizon_weeks: int = 4,
    spec: InterventionSpec | None = None,
    forecasts: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build the district x intensity effect table that Stage 3 consumes.

    Parameters
    ----------
    panel:
        District-week panel.
    parameters:
        Pre-fitted parameters. Fitted here if omitted.
    max_team_weeks:
        Highest intensity level to evaluate. The table covers ``0..max``
        inclusive, which is exactly the domain of the ILP's ``x[d, k]``
        variables.
    horizon_weeks:
        Window over which averted cases accumulate.
    spec:
        Intervention mechanics.
    forecasts:
        Optional Stage 1 forecasts. When supplied, each district's effect is
        rescaled by the ratio of forecast to model-implied baseline cases, so
        the allocation responds to **where cases are heading** (Stage 1) rather
        than only to where transmission is structurally intense (Stage 2). This
        is the join between the two stages.

    Returns
    -------
    pandas.DataFrame
        Columns ``district_id``, ``team_weeks``, ``cases_averted_mean``,
        ``cases_averted_lower``, ``cases_averted_upper``,
        ``marginal_cases_averted_per_team_week``, ``coverage``,
        ``baseline_cases``.
    """
    # `is None` rather than falsiness: an explicitly-passed empty dict means
    # "every district failed to fit", which must raise. Treating it as "not
    # supplied" would silently launch a full refit and hide the failure.
    parameters = fit_all_districts(panel) if parameters is None else parameters
    if not parameters:
        raise RuntimeError("No districts were successfully fitted; cannot build effect table")

    forecast_by_district: dict[str, float] = {}
    if forecasts is not None and not forecasts.empty:
        latest = forecasts[forecasts["iso_week"] == forecasts["iso_week"].max()]
        horizon_slice = latest[latest["horizon"] == latest["horizon"].max()]
        forecast_by_district = dict(
            zip(horizon_slice["district_id"], horizon_slice["q0.5"], strict=False)
        )

    rows: list[dict[str, object]] = []
    for district_id, params in parameters.items():
        # Anchor the effect curve to the Stage 1 forecast where available.
        scale = 1.0
        if district_id in forecast_by_district:
            reference = intervention_effect(
                params, panel, 0.0, horizon_weeks=horizon_weeks, spec=spec
            )
            model_weekly = reference.baseline_cases / max(horizon_weeks, 1)
            forecast_weekly = float(forecast_by_district[district_id])
            if model_weekly > 1e-6:
                # Wide band on purpose. With rho fixed, the mechanistic model's
                # absolute level is not meant to be trusted -- Stage 2's job is
                # the SHAPE of the response curve (concavity, relative district
                # differences), and Stage 1's job is the level. A tight clip
                # here would let an arbitrary bound, rather than the forecast,
                # decide how many cases a district has at stake.
                scale = float(np.clip(forecast_weekly / model_weekly, 0.02, 50.0))

        for k in range(max_team_weeks + 1):
            effect = intervention_effect(
                params, panel, float(k), horizon_weeks=horizon_weeks, spec=spec
            )
            rows.append(
                {
                    "district_id": district_id,
                    "team_weeks": k,
                    "cases_averted_mean": effect.cases_averted_mean * scale,
                    "cases_averted_lower": effect.cases_averted_lower * scale,
                    "cases_averted_upper": effect.cases_averted_upper * scale,
                    "marginal_cases_averted_per_team_week": (
                        effect.marginal_cases_averted_per_team_week * scale
                    ),
                    "coverage": effect.coverage,
                    "baseline_cases": effect.baseline_cases * scale,
                }
            )

    table = pd.DataFrame(rows).sort_values(["district_id", "team_weeks"]).reset_index(drop=True)

    # Enforce monotone non-decreasing averted cases within each district. Tiny
    # numerical non-monotonicity from the ODE solve would otherwise let the ILP
    # exploit a spurious dip and pick a lower intensity for a higher payoff.
    table["cases_averted_mean"] = table.groupby("district_id", observed=True)[
        "cases_averted_mean"
    ].cummax()

    n_districts = table["district_id"].nunique()
    log.info(
        "sei_sir: effect table  districts=%d  levels=0..%d  rows=%d  "
        "max_averted=%.1f  horizon=%dw",
        n_districts,
        max_team_weeks,
        len(table),
        float(table["cases_averted_mean"].max()),
        horizon_weeks,
    )
    return table


def sensitivity_to_reporting_fraction(
    panel: pd.DataFrame,
    district_ids: list[str],
    *,
    fractions: tuple[float, ...] = (0.05, 0.10, 0.20),
    max_team_weeks: int = 6,
) -> pd.DataFrame:
    """Quantify how the district **ranking** moves with the fixed ``rho``.

    The absolute scale of averted cases inherits the ``rho`` assumption. What
    Stage 3 consumes is the ordering, so this reports Spearman correlations
    between the district rankings produced at different ``rho`` values. High
    correlation means the allocation is robust to the assumption even though the
    headline numbers are not.
    """
    rankings: dict[float, pd.Series] = {}
    for rho in fractions:
        params = fit_all_districts(panel, district_ids=district_ids, reporting_fraction=rho)
        table = build_effect_table(panel, params, max_team_weeks=max_team_weeks)
        at_max = table[table["team_weeks"] == max_team_weeks].set_index("district_id")
        rankings[rho] = at_max["cases_averted_mean"].rank(ascending=False)

    frame = pd.DataFrame(rankings)
    rows = []
    for i, a in enumerate(fractions):
        for b in fractions[i + 1 :]:
            rho_corr = frame[a].corr(frame[b], method="spearman")
            rows.append({"rho_a": a, "rho_b": b, "spearman_rank_corr": float(rho_corr)})
    return pd.DataFrame(rows)
