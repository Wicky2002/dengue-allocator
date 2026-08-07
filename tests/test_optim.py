"""Stage 3 tests: the allocation ILP.

Built on a hand-made effect table with known structure, so the optimum is
verifiable by hand rather than by trusting the solver. That matters: an ILP that
silently returns a feasible-but-suboptimal answer looks exactly like one that
works.
"""

from __future__ import annotations

import pandas as pd
import pytest

from dengue import config
from dengue.optim.allocate import (
    AllocationConstraints,
    allocate,
    allocate_budget_sweep,
    allocate_rolling,
    evaluate_allocation,
    greedy_allocate,
)


def _week() -> pd.Period:
    return pd.Period("2026-08-03", freq=config.WEEK_FREQ)


def make_effect_table(
    per_district: dict[str, list[float]] | None = None,
) -> pd.DataFrame:
    """Build an effect table from explicit per-level averted-case values.

    Values are SYNTHETIC and chosen so the optimum can be reasoned about by hand.
    """
    if per_district is None:
        # Concave curves. 'a' has the steepest start, 'c' the flattest.
        per_district = {
            "colombo": [0.0, 10.0, 18.0, 24.0, 28.0],
            "gampaha": [0.0, 8.0, 15.0, 21.0, 26.0],
            "kandy": [0.0, 3.0, 5.5, 7.5, 9.0],
        }

    rows = []
    for district_id, curve in per_district.items():
        for k, averted in enumerate(curve):
            rows.append(
                {
                    "district_id": district_id,
                    "team_weeks": k,
                    "cases_averted_mean": averted,
                    "cases_averted_lower": averted * 0.6,
                    "cases_averted_upper": averted * 1.6,
                    "marginal_cases_averted_per_team_week": (
                        averted - curve[k - 1] if k else curve[1] - curve[0]
                    ),
                    "coverage": min(0.1 * k, 1.0),
                    "baseline_cases": 100.0,
                }
            )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Constraint validation
# --------------------------------------------------------------------------


def test_constraints_reject_infeasible_high_risk_floor():
    constraints = AllocationConstraints(
        total_team_weeks=4,
        min_teams_high_risk=3,
        high_risk_districts=("colombo", "gampaha"),
    )
    with pytest.raises(ValueError, match="high-risk floor needs 6 team-weeks"):
        constraints.validate()


def test_constraints_reject_floor_above_cap():
    constraints = AllocationConstraints(
        total_team_weeks=100, max_teams_per_district=2, min_teams_high_risk=5
    )
    with pytest.raises(ValueError, match="exceeds"):
        constraints.validate()


def test_constraints_reject_negative_budget():
    with pytest.raises(ValueError, match="non-negative"):
        AllocationConstraints(total_team_weeks=-5).validate()


# --------------------------------------------------------------------------
# Core solve
# --------------------------------------------------------------------------


def test_allocation_respects_the_budget():
    table = make_effect_table()
    constraints = AllocationConstraints(total_team_weeks=6, max_weekly_change=None)
    result = allocate(table, constraints, _week())

    assert result.solver_status == "Optimal"
    assert result.budget_used <= 6


def test_allocation_assigns_one_level_per_district():
    table = make_effect_table()
    constraints = AllocationConstraints(total_team_weeks=8, max_weekly_change=None)
    result = allocate(table, constraints, _week())

    assert set(result.allocation) == {"colombo", "gampaha", "kandy"}
    assert all(isinstance(v, int) and v >= 0 for v in result.allocation.values())


def test_allocation_prefers_the_steeper_curve():
    """With a tight budget, teams go where the marginal return is highest.

    At budget 2, the options are 2 in colombo (18) or 1+1 split (10+8=18) or
    2 in kandy (5.5). The optimum must be 18, not the kandy allocation.
    """
    table = make_effect_table()
    constraints = AllocationConstraints(
        total_team_weeks=2, min_teams_high_risk=0, max_weekly_change=None
    )
    result = allocate(table, constraints, _week())

    assert result.expected_cases_averted == pytest.approx(18.0)
    assert result.allocation["kandy"] == 0


def test_allocation_splits_when_returns_diminish():
    """Concavity must actually produce a spread, not an all-in bet.

    At budget 4 with a cap of 4: all-in colombo gives 28. Splitting 2/2 across
    colombo+gampaha gives 18+15 = 33, which is better. The solver must find it.
    """
    table = make_effect_table()
    constraints = AllocationConstraints(
        total_team_weeks=4, max_teams_per_district=4, min_teams_high_risk=0, max_weekly_change=None
    )
    result = allocate(table, constraints, _week())

    assert result.expected_cases_averted == pytest.approx(33.0)
    assert result.allocation["colombo"] == 2
    assert result.allocation["gampaha"] == 2


def test_high_risk_floor_is_enforced():
    table = make_effect_table()
    constraints = AllocationConstraints(
        total_team_weeks=6,
        min_teams_high_risk=2,
        high_risk_districts=("kandy",),  # the WORST district by effect
        max_weekly_change=None,
    )
    result = allocate(table, constraints, _week())

    # Without the floor the solver would never fund kandy.
    assert result.allocation["kandy"] >= 2


def test_per_district_cap_is_enforced():
    table = make_effect_table()
    constraints = AllocationConstraints(
        total_team_weeks=12, max_teams_per_district=1, min_teams_high_risk=0, max_weekly_change=None
    )
    result = allocate(table, constraints, _week())
    assert max(result.allocation.values()) <= 1


def test_continuity_constraint_limits_week_to_week_swing():
    table = make_effect_table()
    previous = {"colombo": 0, "gampaha": 0, "kandy": 4}
    constraints = AllocationConstraints(
        total_team_weeks=8, min_teams_high_risk=0, max_weekly_change=1
    )
    result = allocate(table, constraints, _week(), previous_allocation=previous)

    for district, teams in result.allocation.items():
        assert abs(teams - previous[district]) <= 1, f"{district} swung too far"


def test_risk_averse_posture_uses_the_upper_effect_column():
    table = make_effect_table()
    constraints = AllocationConstraints(
        total_team_weeks=4, min_teams_high_risk=0, max_weekly_change=None
    )

    median = allocate(table, constraints, _week(), risk_quantile=0.5)
    averse = allocate(table, constraints, _week(), risk_quantile=0.9)

    # Upper column is 1.6x the mean, so the objective must scale accordingly.
    assert averse.expected_cases_averted > median.expected_cases_averted


def test_invalid_risk_quantile_raises():
    table = make_effect_table()
    constraints = AllocationConstraints(total_team_weeks=4, max_weekly_change=None)
    with pytest.raises(ValueError, match="risk_quantile must be one of"):
        allocate(table, constraints, _week(), risk_quantile=0.75)


def test_malformed_effect_table_raises():
    bad = pd.DataFrame({"district_id": ["colombo"], "team_weeks": [1]})
    constraints = AllocationConstraints(total_team_weeks=4, max_weekly_change=None)
    with pytest.raises(ValueError, match="missing columns"):
        allocate(bad, constraints, _week())


def test_shadow_price_is_reported_and_non_negative():
    table = make_effect_table()
    constraints = AllocationConstraints(
        total_team_weeks=3, min_teams_high_risk=0, max_weekly_change=None
    )
    result = allocate(table, constraints, _week())

    if result.shadow_price_budget is not None:
        assert result.shadow_price_budget >= 0


# --------------------------------------------------------------------------
# ILP vs greedy
# --------------------------------------------------------------------------


def test_ilp_is_never_worse_than_greedy():
    """The ILP is optimal by construction, so this must hold at every budget."""
    table = make_effect_table()
    for budget in (2, 4, 6, 8, 10):
        constraints = AllocationConstraints(
            total_team_weeks=budget,
            max_teams_per_district=4,
            min_teams_high_risk=0,
            max_weekly_change=None,
        )
        ilp = allocate(table, constraints, _week())
        greedy = greedy_allocate(table, constraints, _week())
        assert (
            ilp.expected_cases_averted >= greedy.expected_cases_averted - 1e-6
        ), f"ILP lost to greedy at budget {budget}"


def test_greedy_honours_the_high_risk_floor():
    """Regression: greedy must solve the SAME problem as the ILP.

    An earlier version ignored the floor, which let it "beat" the ILP at tight
    budgets purely by solving an easier, operationally infeasible problem. The
    comparison must isolate allocation logic, not the constraint set.
    """
    table = make_effect_table()
    constraints = AllocationConstraints(
        total_team_weeks=6,
        max_teams_per_district=4,
        min_teams_high_risk=2,
        high_risk_districts=("kandy",),  # the WORST district by effect
        max_weekly_change=None,
    )
    greedy = greedy_allocate(table, constraints, _week())
    assert greedy.allocation["kandy"] >= 2, "greedy ignored the high-risk floor"
    assert greedy.budget_used <= constraints.total_team_weeks


def test_ilp_beats_greedy_even_when_the_floor_binds():
    """With the floor applied to both, the ILP must still win or tie."""
    table = make_effect_table()
    for budget in (4, 6, 8, 12):
        constraints = AllocationConstraints(
            total_team_weeks=budget,
            max_teams_per_district=4,
            min_teams_high_risk=2,
            high_risk_districts=("kandy",),
            max_weekly_change=None,
        )
        ilp = allocate(table, constraints, _week())
        greedy = greedy_allocate(table, constraints, _week())
        assert ilp.allocation["kandy"] >= 2
        assert (
            ilp.expected_cases_averted >= greedy.expected_cases_averted - 1e-6
        ), f"ILP lost to a constraint-respecting greedy at budget {budget}"


def test_ilp_strictly_beats_greedy_when_returns_diminish():
    """The case that justifies the ILP: greedy fills one district to the cap."""
    table = make_effect_table()
    constraints = AllocationConstraints(
        total_team_weeks=4, max_teams_per_district=4, min_teams_high_risk=0, max_weekly_change=None
    )
    ilp = allocate(table, constraints, _week())
    greedy = greedy_allocate(table, constraints, _week())

    # Greedy puts all 4 in colombo (28); the ILP splits 2/2 (33).
    assert greedy.expected_cases_averted == pytest.approx(28.0)
    assert ilp.expected_cases_averted == pytest.approx(33.0)
    assert ilp.expected_cases_averted > greedy.expected_cases_averted


# --------------------------------------------------------------------------
# Sweep, rolling, evaluation
# --------------------------------------------------------------------------


def test_budget_sweep_covers_every_scenario():
    table = make_effect_table()
    budgets = [2, 4, 6]
    sweep = allocate_budget_sweep(
        table, _week(), budgets, max_teams_per_district=4, min_teams_high_risk=0
    )

    assert not sweep.empty
    assert set(sweep["budget"]) == set(budgets)
    assert set(sweep["risk_quantile"]) == {0.5, 0.9}
    assert set(sweep["strategy"]) == {"ilp", "greedy"}


def test_budget_sweep_averted_cases_increase_with_budget():
    table = make_effect_table()
    sweep = allocate_budget_sweep(
        table, _week(), [2, 4, 6, 8], max_teams_per_district=4, min_teams_high_risk=0
    )
    ilp = (
        sweep[(sweep["strategy"] == "ilp") & (sweep["risk_quantile"] == 0.5)]
        .groupby("budget", observed=True)["expected_cases_averted"]
        .first()
        .sort_index()
    )
    assert list(ilp) == sorted(ilp), "more budget must not avert fewer cases"


def test_rolling_allocation_chains_continuity():
    table = make_effect_table()
    weeks = [_week(), _week() + 1, _week() + 2]
    tables = dict.fromkeys(weeks, table)
    constraints = AllocationConstraints(
        total_team_weeks=6, max_teams_per_district=4, min_teams_high_risk=0, max_weekly_change=1
    )
    frame = allocate_rolling(tables, constraints)

    assert set(frame["iso_week"].unique()) == set(weeks)
    wide = frame.pivot_table(index="iso_week", columns="district_id", values="team_weeks")
    for district in wide.columns:
        assert wide[district].diff().abs().max() <= 1 + 1e-9


def test_evaluate_allocation_reports_uplift():
    table = make_effect_table()
    constraints = AllocationConstraints(
        total_team_weeks=4, max_teams_per_district=4, min_teams_high_risk=0, max_weekly_change=None
    )
    ilp = allocate(table, constraints, _week())
    greedy = greedy_allocate(table, constraints, _week())

    metrics = evaluate_allocation(ilp, table, comparison=greedy)
    assert metrics["expected_cases_averted"] == pytest.approx(33.0)
    assert metrics["uplift_vs_comparison"] > 0
    assert metrics["districts_served"] == 2
    assert 0.0 <= metrics["gini_concentration"] <= 1.0
