"""Stage 3 -- integer linear program allocating vector-control teams.

STUB -- typed signatures and formulation only; no implementation this session.

The decision problem
--------------------
Each week the National Dengue Control Unit has a fixed number of vector-control
teams. Each team-week can be sent to one district. Where should they go?

The naive answer -- rank districts by forecast cases and fill from the top -- is
wrong for two reasons. First, **returns saturate**: the tenth team in Colombo
averts far fewer cases than the first team in Gampaha, so the objective is
concave in each district's allocation. Second, **there are constraints that make
the greedy solution infeasible**: minimum coverage for high-risk MOH areas,
maximum teams per district, and a limit on how far the allocation may move
week-to-week (teams are people, and reassigning them all every week is not
operationally real).

That combination -- concave objective, integrality, side constraints -- is what
makes this an ILP rather than a sort.

Formulation
-----------
Decision variables
    ``x[d, k] in {0, 1}`` -- district *d* receives intensity level *k* team-weeks.
    Using one binary per (district, level) rather than a single integer variable
    is what lets the **concave** effect curve from Stage 2 be represented
    exactly, as a piecewise-linear function, while keeping the program linear.

Objective
    Maximise total expected cases averted::

        max  sum_{d,k} effect[d, k] * x[d, k]

    where ``effect[d, k]`` comes from
    :func:`dengue.causal.sei_sir.build_effect_table`.

Constraints
    1. *One level per district*: ``sum_k x[d, k] == 1`` for every *d*.
    2. *Budget*: ``sum_{d,k} k * x[d, k] <= total_team_weeks``.
    3. *High-risk floor*: districts containing high-risk MOH areas receive at
       least ``min_teams_high_risk``.
    4. *Per-district cap*: no district exceeds ``max_teams_per_district``, to
       avoid a degenerate all-in allocation.
    5. *Continuity*: ``|allocation[d] - previous_allocation[d]| <=
       max_weekly_change``, keeping the plan operationally deliverable.

Robustness
    The default objective uses the Stage 1 **median** forecast. A risk-averse
    variant maximises against the 0.9 quantile instead, which allocates against
    the plausible worst case rather than the central one -- appropriate when the
    cost of under-responding to an outbreak greatly exceeds the cost of an idle
    team. :func:`allocate` exposes this via ``risk_quantile``.

Solver: CBC via PuLP, which is bundled and needs no external install.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class AllocationConstraints:
    """Operational constraints on a weekly allocation.

    Attributes
    ----------
    total_team_weeks:
        Total budget available this week. The binding constraint.
    max_teams_per_district:
        Per-district cap.
    min_teams_high_risk:
        Floor for districts flagged high-risk.
    max_weekly_change:
        Maximum change in a district's allocation versus the previous week.
        ``None`` disables the continuity constraint.
    high_risk_districts:
        Districts subject to ``min_teams_high_risk``.
    """

    total_team_weeks: int
    max_teams_per_district: int = 20
    min_teams_high_risk: int = 2
    max_weekly_change: int | None = 5
    high_risk_districts: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AllocationResult:
    """Solved allocation for one week.

    Attributes
    ----------
    iso_week:
        Week the allocation applies to.
    allocation:
        ``district_id -> team-weeks assigned``.
    expected_cases_averted:
        Objective value at the optimum.
    budget_used, budget_available:
        Team-weeks consumed and offered.
    solver_status:
        PuLP status string, e.g. ``"Optimal"``. Anything other than ``"Optimal"``
        means the returned allocation should not be acted on.
    shadow_price_budget:
        Dual value on the budget constraint from the LP relaxation: the marginal
        cases averted by one additional team-week. This is the number that
        answers "should we fund more teams?", so it is worth surfacing even
        though it is a by-product.
    """

    iso_week: pd.Period
    allocation: dict[str, int]
    expected_cases_averted: float
    budget_used: int
    budget_available: int
    solver_status: str
    shadow_price_budget: float | None = None


def allocate(
    effect_table: pd.DataFrame,
    constraints: AllocationConstraints,
    iso_week: pd.Period,
    *,
    previous_allocation: dict[str, int] | None = None,
    risk_quantile: float = 0.5,
) -> AllocationResult:
    """Solve the weekly team-allocation ILP. Not implemented.

    Parameters
    ----------
    effect_table:
        Output of :func:`dengue.causal.sei_sir.build_effect_table`: columns
        ``district_id``, ``team_weeks``, ``cases_averted_mean``.
    constraints:
        Operational constraints.
    iso_week:
        Week being allocated.
    previous_allocation:
        Last week's allocation, required if ``max_weekly_change`` is set.
    risk_quantile:
        Forecast quantile to optimise against. 0.5 for the median, 0.9 for a
        risk-averse allocation.

    Returns
    -------
    AllocationResult
        The optimal allocation and its objective value.

    Raises
    ------
    NotImplementedError
        Always. Stage 3 is scaffolded only in this session.
    """
    raise NotImplementedError(
        "Stage 3 (allocate) is not implemented. This session delivers Stage 1 "
        "baselines and the evaluation harness; see the module docstring for the "
        "full ILP formulation, which is ready to implement against PuLP/CBC."
    )


def allocate_rolling(
    effect_tables: dict[pd.Period, pd.DataFrame],
    constraints: AllocationConstraints,
    *,
    risk_quantile: float = 0.5,
) -> pd.DataFrame:
    """Solve the allocation for a sequence of weeks, chaining continuity. Not implemented.

    Returns
    -------
    pandas.DataFrame
        Columns ``iso_week``, ``district_id``, ``team_weeks``,
        ``expected_cases_averted``.

    Raises
    ------
    NotImplementedError
        Always.
    """
    raise NotImplementedError("Stage 3 (allocate_rolling) is not implemented. See allocate.")


def evaluate_allocation(
    allocation: AllocationResult,
    realised_cases: pd.DataFrame,
) -> dict[str, float]:
    """Score a realised allocation against a counterfactual baseline. Not implemented.

    Raises
    ------
    NotImplementedError
        Always.
    """
    raise NotImplementedError("Stage 3 (evaluate_allocation) is not implemented.")
