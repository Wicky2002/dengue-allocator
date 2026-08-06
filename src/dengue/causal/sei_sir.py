"""Stage 2 -- mechanistic SEI-SIR model for vector-control effect sizes.

STUB -- typed signatures and design only; no implementation this session.

What this stage is for
----------------------
Stage 1 says where cases are going. Stage 3 needs something Stage 1 cannot
provide: **the counterfactual**. Allocating teams requires knowing how many cases
are averted by sending *k* teams to district *d*, and that is a causal quantity.
A forecasting model fitted on observational data cannot answer it, because
historically teams were sent *to* outbreaks -- so naively regressing cases on
team-weeks recovers a positive coefficient and would tell you that vector control
causes dengue.

The mechanistic route sidesteps that confounding by modelling transmission
explicitly and intervening on the vector parameters.

Model structure
---------------
Coupled vector-host compartments per district:

*Vector (SEI).* ``S_v -> E_v -> I_v``. Mosquitoes do not recover; ``E_v`` is the
extrinsic incubation period, strongly temperature-dependent (roughly 12 days at
25 C, 7 days at 30 C), which is the main channel through which ``tmax``
influences transmission.

*Host (SIR).* ``S_h -> I_h -> R_h``, with reporting fraction ``rho`` mapping
``I_h`` to notified cases. ``rho`` is identifiable only with a serosurvey or a
strong prior; without one, ``R0`` and ``rho`` trade off almost exactly.

*Forcing.* Vector carrying capacity ``K(t)`` is driven by lagged rainfall and
temperature, which is where the climate covariates enter mechanistically rather
than as regression features.

*Intervention.* A control team-week acts by (a) raising adult mortality
``mu_v`` through space spraying and (b) reducing ``K`` through larval source
reduction. These have very different time signatures -- adulticiding gives a
sharp, short-lived drop; source reduction is slower and more durable -- and
separating them is the point of doing this mechanistically.

Estimation
----------
Fit per district by maximum likelihood (negative binomial observation model) or
ABC-SMC where the likelihood is intractable. ``R0`` is decomposed into
climate-driven and residual components so the intervention effect is not
absorbed by seasonality.

Outputs consumed by Stage 3
---------------------------
:func:`intervention_effect` returns the expected cases averted per team-week per
district, with uncertainty. That is exactly the objective coefficient vector the
ILP in :mod:`dengue.optim.allocate` maximises.

References
----------
Newton & Reiter (1992) on SEI-SIR for dengue; Andraud et al. (2012) for a review
of dengue transmission model structures; Mordecai et al. (2017) on
temperature-dependent transmission parameters.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SEISIRParameters:
    """Fitted SEI-SIR parameters for one district.

    Attributes
    ----------
    district_id:
        Canonical district key.
    beta_hv:
        Transmission probability, host to vector, per bite.
    beta_vh:
        Transmission probability, vector to host, per bite.
    biting_rate:
        Bites per mosquito per day.
    mu_v:
        Baseline adult vector mortality rate, per day.
    eip_days:
        Extrinsic incubation period at the district's mean temperature, in days.
    iip_days:
        Host intrinsic infectious period, in days.
    carrying_capacity:
        Baseline vector carrying capacity, mosquitoes per host.
    rainfall_elasticity:
        Elasticity of carrying capacity to lagged rainfall.
    reporting_fraction:
        Fraction of true infections that become notified cases.
    r0_mean:
        Posterior mean basic reproduction number.
    log_likelihood:
        Log-likelihood at the fitted optimum, for model comparison.
    """

    district_id: str
    beta_hv: float
    beta_vh: float
    biting_rate: float
    mu_v: float
    eip_days: float
    iip_days: float
    carrying_capacity: float
    rainfall_elasticity: float
    reporting_fraction: float
    r0_mean: float
    log_likelihood: float


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
        Posterior mean cases averted over the evaluation window.
    cases_averted_lower, cases_averted_upper:
        80% credible interval bounds.
    marginal_cases_averted_per_team_week:
        Derivative of cases averted with respect to team-weeks, at
        ``team_weeks``. This is the Stage 3 objective coefficient. It is
        **decreasing** in ``team_weeks`` -- saturating returns are the whole
        reason allocation is a non-trivial optimisation rather than "send
        everyone to the worst district".
    """

    district_id: str
    team_weeks: float
    cases_averted_mean: float
    cases_averted_lower: float
    cases_averted_upper: float
    marginal_cases_averted_per_team_week: float


def fit_sei_sir(
    panel: pd.DataFrame,
    district_id: str,
    *,
    n_iterations: int = 2000,
    seed: int | None = None,
) -> SEISIRParameters:
    """Fit SEI-SIR parameters for one district. Not implemented.

    Parameters
    ----------
    panel:
        District-week panel conforming to :data:`dengue.config.PANEL_DTYPES`.
    district_id:
        District to fit.
    n_iterations:
        MCMC / ABC-SMC iterations.
    seed:
        Random seed.

    Returns
    -------
    SEISIRParameters
        Fitted parameters with uncertainty.

    Raises
    ------
    NotImplementedError
        Always. Stage 2 is scaffolded only in this session.
    """
    raise NotImplementedError(
        "Stage 2 (SEI-SIR) is not implemented. This session delivers Stage 1 "
        "baselines and the evaluation harness; see the module docstring for the "
        "intended compartmental structure and estimation strategy."
    )


def intervention_effect(
    parameters: SEISIRParameters,
    baseline_forecast: pd.DataFrame,
    team_weeks: float,
    *,
    horizon_weeks: int = 4,
) -> InterventionEffect:
    """Estimate cases averted by a given control intensity. Not implemented.

    Parameters
    ----------
    parameters:
        Fitted parameters from :func:`fit_sei_sir`.
    baseline_forecast:
        Stage 1 forecast for the district, giving the counterfactual trajectory
        under no additional intervention.
    team_weeks:
        Control intensity to evaluate.
    horizon_weeks:
        Window over which averted cases are accumulated.

    Returns
    -------
    InterventionEffect
        Cases averted and the marginal rate Stage 3 optimises against.

    Raises
    ------
    NotImplementedError
        Always.
    """
    raise NotImplementedError("Stage 2 (intervention_effect) is not implemented. See fit_sei_sir.")


def build_effect_table(
    panel: pd.DataFrame,
    forecasts: pd.DataFrame,
    *,
    max_team_weeks: int = 20,
) -> pd.DataFrame:
    """Build the district x intensity effect table Stage 3 consumes. Not implemented.

    Returns
    -------
    pandas.DataFrame
        Columns ``district_id``, ``team_weeks``, ``cases_averted_mean``,
        ``marginal_cases_averted_per_team_week``.

    Raises
    ------
    NotImplementedError
        Always.
    """
    raise NotImplementedError("Stage 2 (build_effect_table) is not implemented.")
