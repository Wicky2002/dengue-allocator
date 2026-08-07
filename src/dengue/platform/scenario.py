"""Scenario simulator -- "what happens if...".

This is not a lookup table of canned answers. Each scenario perturbs an input to
the **fitted SEI-SIR model** from Stage 2 and re-integrates it, so the answer
comes from the same mechanism that produces the intervention effects. A rainfall
scenario really does propagate through carrying capacity, the vector population,
the extrinsic incubation period and the host compartments.

That matters for a specific reason: the response to "heavy rain next week" is
**not** proportional and **not** immediate. Rain raises carrying capacity, which
raises the adult vector population several weeks later, which raises transmission
after the EIP, which shows up in notified cases later still. A scenario tool
built on a regression coefficient would show an instant bump. This one shows the
lag, because the lag is in the model.

Scenarios
---------
``heavy_rain`` / ``drought``
    Shift lagged rainfall by a number of standard deviations.
``heatwave`` / ``cooler``
    Shift temperature, which acts mainly through the EIP.
``surge_response``
    Deploy additional vector-control teams.
``no_intervention``
    Withdraw all control, for a counterfactual baseline.
``compound``
    Combine several at once, which is where the interesting non-additivity shows
    up: heavy rain plus a heatwave is worse than the sum of the two, because more
    mosquitoes and a shorter EIP multiply rather than add.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from dengue import config
from dengue.causal.sei_sir import (
    InterventionSpec,
    SEISIRParameters,
    _prepare_district,
    coverage_from_team_weeks,
    simulate,
)
from dengue.utils.logging import get_logger

log = get_logger(__name__)


@dataclass(frozen=True)
class Scenario:
    """A perturbation to simulate.

    Attributes
    ----------
    key, name, description:
        Identity and UI copy.
    rain_shift_sd:
        Shift applied to standardised lagged rainfall, in standard deviations.
    temperature_shift_c:
        Shift applied to weekly maximum temperature, in Celsius.
    team_weeks:
        Vector-control intensity deployed during the scenario window.
    horizon_weeks:
        Length of the scenario window.
    """

    key: str
    name: str
    description: str
    rain_shift_sd: float = 0.0
    temperature_shift_c: float = 0.0
    team_weeks: float = 0.0
    horizon_weeks: int = 4


#: Presets offered in the UI. Magnitudes are chosen to be meaningful rather than
#: extreme: +1.5 sd of weekly rainfall is a wet week, not a once-a-decade event.
PRESET_SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        "baseline",
        "Baseline",
        "Recent conditions continue, no additional vector control.",
    ),
    Scenario(
        "heavy_rain",
        "Heavy rain",
        "Sustained heavy rainfall (+1.5 sd) over the scenario window.",
        rain_shift_sd=1.5,
    ),
    Scenario(
        "extreme_rain",
        "Monsoon surge",
        "Exceptional rainfall (+3 sd), as in a monsoon onset week.",
        rain_shift_sd=3.0,
    ),
    Scenario(
        "drought",
        "Dry spell",
        "Well below-average rainfall (-1.5 sd).",
        rain_shift_sd=-1.5,
    ),
    Scenario(
        "heatwave",
        "Heatwave",
        "+2 C on weekly maximum temperature, shortening the extrinsic " "incubation period.",
        temperature_shift_c=2.0,
    ),
    Scenario(
        "surge_response",
        "Surge vector control",
        "Deploy 10 team-weeks of vector control in this district.",
        team_weeks=10.0,
    ),
    Scenario(
        "rain_plus_response",
        "Heavy rain + surge response",
        "Heavy rain, met with 10 team-weeks of vector control.",
        rain_shift_sd=1.5,
        team_weeks=10.0,
    ),
    Scenario(
        "compound_worst",
        "Heavy rain + heatwave, no response",
        "Both drivers push the same way and nothing is deployed against them.",
        rain_shift_sd=1.5,
        temperature_shift_c=2.0,
    ),
)

PRESETS_BY_KEY: dict[str, Scenario] = {s.key: s for s in PRESET_SCENARIOS}


@dataclass(frozen=True)
class ScenarioResult:
    """Outcome of one scenario for one district.

    Attributes
    ----------
    weekly_cases:
        Projected notified cases per week over the horizon.
    total_cases:
        Sum over the horizon.
    baseline_total:
        The same total under the baseline scenario.
    change_pct:
        Percentage change against baseline. The headline number.
    """

    district_id: str
    district_name: str
    scenario: Scenario
    weekly_cases: tuple[float, ...]
    total_cases: float
    baseline_total: float
    change_pct: float
    warmup_weeks: int = 104

    @property
    def direction(self) -> str:
        if self.change_pct > 1:
            return "increase"
        if self.change_pct < -1:
            return "decrease"
        return "little change"

    @property
    def headline(self) -> str:
        return (
            f"{self.scenario.name}: {abs(self.change_pct):.0f}% {self.direction} "
            f"in {self.district_name} over {self.scenario.horizon_weeks} weeks"
        )


def run_scenario(
    parameters: SEISIRParameters,
    panel: pd.DataFrame,
    scenario: Scenario,
    *,
    spec: InterventionSpec | None = None,
    baseline_total: float | None = None,
) -> ScenarioResult:
    """Simulate one scenario for one district.

    The district is warmed up on observed history so the forward run starts from
    a realistic epidemic phase, then the perturbation is applied only to the
    scenario window.
    """
    spec = spec or InterventionSpec()
    _cases, rain_z, tmax, population = _prepare_district(panel, parameters.district_id)

    horizon = scenario.horizon_weeks
    warmup = min(len(rain_z), 104)

    future_rain = np.resize(rain_z[-horizon:], horizon) + scenario.rain_shift_sd
    future_tmax = np.resize(tmax[-horizon:], horizon) + scenario.temperature_shift_c

    rain_path = np.concatenate([rain_z[-warmup:], future_rain])
    tmax_path = np.concatenate([tmax[-warmup:], future_tmax])

    coverage_path = None
    if scenario.team_weeks > 0:
        cover = coverage_from_team_weeks(scenario.team_weeks, population, spec)
        coverage_path = np.zeros(warmup + horizon, dtype=float)
        coverage_path[warmup:] = cover

    projected = simulate(
        warmup + horizon,
        rain_path,
        tmax_path,
        population,
        parameters.r0_base,
        parameters.rain_elasticity,
        parameters.init_susceptible,
        reporting_fraction=parameters.reporting_fraction,
        coverage=coverage_path,
        spec=spec,
    )[warmup:]

    total = float(np.sum(projected))

    if baseline_total is None:
        base_rain = np.concatenate([rain_z[-warmup:], np.resize(rain_z[-horizon:], horizon)])
        base_tmax = np.concatenate([tmax[-warmup:], np.resize(tmax[-horizon:], horizon)])
        baseline_total = float(
            np.sum(
                simulate(
                    warmup + horizon,
                    base_rain,
                    base_tmax,
                    population,
                    parameters.r0_base,
                    parameters.rain_elasticity,
                    parameters.init_susceptible,
                    reporting_fraction=parameters.reporting_fraction,
                )[warmup:]
            )
        )

    change = 100.0 * (total - baseline_total) / baseline_total if baseline_total > 1e-9 else 0.0

    return ScenarioResult(
        district_id=parameters.district_id,
        district_name=config.get_district(parameters.district_id).name,
        scenario=scenario,
        weekly_cases=tuple(float(x) for x in projected),
        total_cases=total,
        baseline_total=baseline_total,
        change_pct=change,
        warmup_weeks=warmup,
    )


def run_all_scenarios(
    parameters: SEISIRParameters,
    panel: pd.DataFrame,
    scenarios: tuple[Scenario, ...] = PRESET_SCENARIOS,
) -> list[ScenarioResult]:
    """Run every scenario for one district, sharing one baseline simulation."""
    baseline_scenario = PRESETS_BY_KEY["baseline"]
    baseline = run_scenario(parameters, panel, baseline_scenario)

    results = [baseline]
    for scenario in scenarios:
        if scenario.key == "baseline":
            continue
        results.append(
            run_scenario(parameters, panel, scenario, baseline_total=baseline.total_cases)
        )
    return results


def build_scenario_table(
    parameters: dict[str, SEISIRParameters],
    panel: pd.DataFrame,
    *,
    district_ids: list[str] | None = None,
    scenarios: tuple[Scenario, ...] = PRESET_SCENARIOS,
) -> pd.DataFrame:
    """Precompute scenarios for the dashboard.

    Cached as an artifact so the Scenario tab is instant and does not integrate
    an ODE at request time.
    """
    district_ids = district_ids or sorted(parameters)
    rows: list[dict[str, object]] = []

    for district_id in district_ids:
        params = parameters.get(district_id)
        if params is None:
            continue
        for result in run_all_scenarios(params, panel, scenarios):
            rows.append(
                {
                    "district_id": result.district_id,
                    "district": result.district_name,
                    "scenario_key": result.scenario.key,
                    "scenario": result.scenario.name,
                    "description": result.scenario.description,
                    "total_cases": result.total_cases,
                    "baseline_total": result.baseline_total,
                    "change_pct": result.change_pct,
                    "horizon_weeks": result.scenario.horizon_weeks,
                    # Comma-separated rather than a list column: Arrow cannot
                    # serialise a nested list cleanly, and Streamlit would warn
                    # and silently coerce it on every render.
                    "weekly_cases": ",".join(f"{x:.2f}" for x in result.weekly_cases),
                }
            )

    frame = pd.DataFrame(rows)
    if not frame.empty:
        log.info(
            "scenario: %d districts x %d scenarios = %d rows",
            frame["district_id"].nunique(),
            frame["scenario_key"].nunique(),
            len(frame),
        )
    return frame
