"""Stage 2 tests: SEI-SIR mechanics, fitting, and intervention effects.

The properties tested here are the ones Stage 3 depends on. If the effect curve
is not monotone and concave, the ILP's piecewise-linear representation is
meaningless and its "optimal" answer is not optimal for the real problem.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dengue.causal.sei_sir import (
    DEFAULT_REPORTING_FRACTION,
    InterventionSpec,
    build_effect_table,
    coverage_from_team_weeks,
    eip_days,
    fit_sei_sir,
    intervention_effect,
    simulate,
)
from dengue.utils.synthetic import make_synthetic_panel


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return make_synthetic_panel(n_districts=3, n_weeks=160, seed=41)


@pytest.fixture(scope="module")
def fitted(panel):
    return fit_sei_sir(panel, "colombo")


# --------------------------------------------------------------------------
# Biology
# --------------------------------------------------------------------------


def test_eip_shortens_as_temperature_rises():
    """Warmer mosquitoes become infectious sooner. This drives the tmax channel."""
    assert eip_days(32.0) < eip_days(28.0) < eip_days(24.0)


def test_eip_is_clipped_to_a_physiological_band():
    """A 200-day EIP would silently switch transmission off rather than slow it."""
    assert 4.0 <= float(eip_days(5.0)) <= 40.0
    assert 4.0 <= float(eip_days(45.0)) <= 40.0


def test_eip_matches_published_values():
    assert float(eip_days(25.0)) == pytest.approx(12.0, abs=0.5)
    assert float(eip_days(30.0)) == pytest.approx(8.3, abs=0.5)


# --------------------------------------------------------------------------
# Simulation
# --------------------------------------------------------------------------


def _flat_inputs(n_weeks: int = 52):
    return np.zeros(n_weeks), np.full(n_weeks, 30.0)


def test_simulation_returns_non_negative_finite_cases():
    rain, tmax = _flat_inputs()
    out = simulate(
        52, rain, tmax, 1_000_000, r0_base=1.5, rain_elasticity=0.3, init_susceptible=0.8
    )
    assert len(out) == 52
    assert np.all(np.isfinite(out))
    assert np.all(out >= 0)


def test_higher_transmission_produces_more_cases():
    rain, tmax = _flat_inputs()
    common = {
        "rain_z": rain,
        "tmax": tmax,
        "population": 1_000_000,
        "rain_elasticity": 0.0,
        "init_susceptible": 0.9,
    }
    low = simulate(52, r0_base=0.8, **common).sum()
    high = simulate(52, r0_base=2.5, **common).sum()
    assert high > low


def test_reporting_fraction_scales_notifications_linearly():
    """rho enters multiplicatively -- the basis of the identifiability argument."""
    rain, tmax = _flat_inputs()
    common = {
        "rain_z": rain,
        "tmax": tmax,
        "population": 500_000,
        "r0_base": 1.5,
        "rain_elasticity": 0.0,
        "init_susceptible": 0.9,
    }
    a = simulate(52, reporting_fraction=0.05, **common).sum()
    b = simulate(52, reporting_fraction=0.10, **common).sum()
    assert b == pytest.approx(2 * a, rel=0.02)


def test_intervention_reduces_cases():
    """The core causal claim: intervening on vector parameters lowers incidence."""
    rain, tmax = _flat_inputs()
    common = {
        "rain_z": rain,
        "tmax": tmax,
        "population": 1_000_000,
        "r0_base": 2.0,
        "rain_elasticity": 0.0,
        "init_susceptible": 0.9,
    }
    baseline = simulate(52, **common).sum()
    treated = simulate(52, coverage=np.full(52, 0.8), spec=InterventionSpec(), **common).sum()
    assert treated < baseline


def test_zero_coverage_equals_no_intervention():
    rain, tmax = _flat_inputs()
    common = {
        "rain_z": rain,
        "tmax": tmax,
        "population": 800_000,
        "r0_base": 1.8,
        "rain_elasticity": 0.2,
        "init_susceptible": 0.85,
    }
    baseline = simulate(40, **common)
    zero = simulate(40, coverage=np.zeros(40), spec=InterventionSpec(), **common)
    np.testing.assert_allclose(baseline, zero, rtol=1e-9)


# --------------------------------------------------------------------------
# Coverage
# --------------------------------------------------------------------------


def test_coverage_saturates_and_stays_in_unit_interval():
    population = 1_000_000
    values = [coverage_from_team_weeks(k, population) for k in (0, 1, 5, 20, 100, 1000)]
    assert values[0] == 0.0
    assert all(0.0 <= v < 1.0 for v in values)
    assert values == sorted(values), "coverage must be non-decreasing in team-weeks"

    # Saturating: equal increments buy progressively less.
    first = coverage_from_team_weeks(10, population) - coverage_from_team_weeks(0, population)
    second = coverage_from_team_weeks(20, population) - coverage_from_team_weeks(10, population)
    assert second < first


def test_coverage_scales_with_population():
    """One team covers a small district far better than a large one."""
    small = coverage_from_team_weeks(5, 100_000)
    large = coverage_from_team_weeks(5, 2_500_000)
    assert small > large


# --------------------------------------------------------------------------
# Fitting
# --------------------------------------------------------------------------


def test_fit_returns_parameters_in_bounds(fitted):
    assert fitted.district_id == "colombo"
    assert 0.05 <= fitted.r0_base <= 20.0
    assert -1.0 <= fitted.rain_elasticity <= 2.0
    assert 0.0 < fitted.init_susceptible < 1.0
    assert fitted.reporting_fraction == DEFAULT_REPORTING_FRACTION
    assert np.isfinite(fitted.log_likelihood)
    assert fitted.n_observations > 0


def test_fit_is_deterministic(panel):
    a = fit_sei_sir(panel, "gampaha", seed=7)
    b = fit_sei_sir(panel, "gampaha", seed=7)
    assert a.r0_base == pytest.approx(b.r0_base, rel=1e-6)
    assert a.log_likelihood == pytest.approx(b.log_likelihood, rel=1e-6)


def test_fit_rejects_unknown_district(panel):
    with pytest.raises(ValueError, match="No rows for district"):
        fit_sei_sir(panel, "atlantis")


# --------------------------------------------------------------------------
# Intervention effects -- the properties Stage 3 relies on
# --------------------------------------------------------------------------


def test_zero_teams_averts_nothing(fitted, panel):
    effect = intervention_effect(fitted, panel, 0.0)
    assert effect.cases_averted_mean == pytest.approx(0.0, abs=1e-6)
    assert effect.coverage == 0.0


def test_averted_cases_increase_with_intensity(fitted, panel):
    averted = [
        intervention_effect(fitted, panel, float(k)).cases_averted_mean for k in (0, 2, 6, 12)
    ]
    assert averted == sorted(averted), f"effect curve is not monotone: {averted}"


def test_returns_diminish(fitted, panel):
    """Concavity. Without it the ILP's piecewise-linear form is meaningless."""
    marginals = [
        intervention_effect(fitted, panel, float(k)).marginal_cases_averted_per_team_week
        for k in (1, 5, 10)
    ]
    assert marginals[0] > marginals[-1], f"marginal returns do not diminish: {marginals}"


def test_effect_interval_brackets_the_mean(fitted, panel):
    effect = intervention_effect(fitted, panel, 6.0)
    assert effect.cases_averted_lower <= effect.cases_averted_mean <= effect.cases_averted_upper


# --------------------------------------------------------------------------
# Effect table
# --------------------------------------------------------------------------


def test_effect_table_shape_and_monotonicity(panel):
    districts = sorted(panel["district_id"].unique())
    params = {d: fit_sei_sir(panel, d) for d in districts}
    table = build_effect_table(panel, params, max_team_weeks=4, horizon_weeks=3)

    expected_columns = {
        "district_id",
        "team_weeks",
        "cases_averted_mean",
        "cases_averted_lower",
        "cases_averted_upper",
        "marginal_cases_averted_per_team_week",
        "coverage",
        "baseline_cases",
    }
    assert expected_columns.issubset(table.columns)
    assert len(table) == len(districts) * 5  # levels 0..4 inclusive
    assert set(table["team_weeks"]) == {0, 1, 2, 3, 4}

    for _, group in table.groupby("district_id", observed=True):
        values = group.sort_values("team_weeks")["cases_averted_mean"].to_numpy()
        assert np.all(np.diff(values) >= -1e-9), "effect table must be non-decreasing"
        assert values[0] == pytest.approx(0.0, abs=1e-6), "level 0 must avert nothing"


def test_effect_table_rescales_to_the_stage1_forecast(panel):
    """Stage 1 sets the level; Stage 2 sets the shape. Verify the join happens."""
    districts = sorted(panel["district_id"].unique())
    params = {d: fit_sei_sir(panel, d) for d in districts}

    origin = panel["iso_week"].max()

    def forecast_at(median: float) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "district_id": districts,
                "iso_week": origin,
                "target_week": origin + 4,
                "horizon": 4,
                "q0.1": median * 0.25,
                "q0.5": median,
                "q0.9": median * 2.0,
            }
        )

    # Compare two forecast levels against each other rather than against the
    # unscaled table: the mechanistic model's own level is arbitrary (rho is
    # fixed), so "higher than unscaled" is not a meaningful direction.
    low = build_effect_table(
        panel, params, max_team_weeks=3, horizon_weeks=4, forecasts=forecast_at(20.0)
    )
    high = build_effect_table(
        panel, params, max_team_weeks=3, horizon_weeks=4, forecasts=forecast_at(200.0)
    )

    low_total = low[low["team_weeks"] == 3]["cases_averted_mean"].sum()
    high_total = high[high["team_weeks"] == 3]["cases_averted_mean"].sum()
    assert high_total > low_total, "a higher Stage 1 forecast must raise the cases at stake"
    # A 10x forecast should move the effect substantially. Not asserted as exactly
    # 10x: the anchor ratio is clipped, and for districts whose mechanistic
    # baseline is very low the clip binds, compressing the response.
    assert high_total > 2.0 * low_total


def test_build_effect_table_raises_without_fitted_parameters(panel):
    with pytest.raises(RuntimeError, match="No districts were successfully fitted"):
        build_effect_table(panel, {})
