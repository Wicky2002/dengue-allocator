"""Stage 3 -- integer linear program allocating vector-control teams.

The decision problem
--------------------
Each week the National Dengue Control Unit has a fixed number of vector-control
teams. Each team-week can be sent to one district. Where should they go?

The tempting answer -- rank districts by forecast cases and fill from the top --
is wrong for two reasons:

1. **Returns saturate.** From Stage 2, the tenth team in Colombo averts far
   fewer cases than the first team in Gampaha. The objective is concave in each
   district's allocation, so the greedy top-of-list fill overshoots.
2. **There are constraints that make the greedy answer infeasible.** Minimum
   coverage for high-risk districts, a per-district cap, and a limit on how far
   the plan may move week-to-week -- teams are people, and reassigning all of
   them every week is not operationally real.

Concave objective + integrality + side constraints is what makes this an ILP
rather than a sort.

Formulation
-----------
**Decision variables.** ``x[d, k] in {0, 1}`` -- district *d* receives exactly
*k* team-weeks. One binary per (district, intensity level) rather than a single
integer variable per district, because that is what represents the **concave**
effect curve from Stage 2 *exactly*, as a piecewise-linear function, while
keeping the program linear. A single integer variable would force a linear
effect assumption and throw away the diminishing returns that make the problem
interesting.

**Objective.** Maximise total expected cases averted::

    max  sum_{d,k} effect[d, k] * x[d, k]

**Constraints.**

1. *One level per district*: ``sum_k x[d, k] == 1`` for every *d*.
2. *Budget*: ``sum_{d,k} k * x[d, k] <= total_team_weeks``.
3. *High-risk floor*: flagged districts receive at least
   ``min_teams_high_risk``.
4. *Per-district cap*: no district exceeds ``max_teams_per_district``, which
   stops a degenerate all-in allocation.
5. *Continuity*: ``|alloc[d] - previous_alloc[d]| <= max_weekly_change``.

Because constraint 1 makes the ``x[d, ·]`` a special-ordered set and the effect
curve is concave, the LP relaxation is tight in practice -- CBC typically solves
these to proven optimality in milliseconds, which is what makes the precomputed
budget sweep in :func:`allocate_budget_sweep` cheap enough to ship to the UI.

**Robustness.** The default objective uses the Stage 1 *median* forecast. A
risk-averse variant optimises against the 0.9 quantile instead, allocating
against the plausible worst case rather than the central one -- appropriate when
the cost of under-responding to an outbreak greatly exceeds the cost of an idle
team. Exposed as ``risk_quantile`` on :func:`allocate`.

Solver: CBC via PuLP, which is bundled with PuLP and needs no external install.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from dengue.utils.logging import get_logger

log = get_logger(__name__)

#: Effect-table column used for each risk posture.
_QUANTILE_COLUMN = {
    0.1: "cases_averted_lower",
    0.5: "cases_averted_mean",
    0.9: "cases_averted_upper",
}


@dataclass(frozen=True)
class AllocationConstraints:
    """Operational constraints on a weekly allocation.

    Attributes
    ----------
    total_team_weeks:
        Total budget available this week. Normally the binding constraint.
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
    max_teams_per_district: int = 12
    min_teams_high_risk: int = 2
    max_weekly_change: int | None = 5
    high_risk_districts: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        """Raise if the constraint set is internally contradictory."""
        if self.total_team_weeks < 0:
            raise ValueError("total_team_weeks must be non-negative")
        if self.max_teams_per_district < 0:
            raise ValueError("max_teams_per_district must be non-negative")
        if self.min_teams_high_risk > self.max_teams_per_district:
            raise ValueError(
                f"min_teams_high_risk ({self.min_teams_high_risk}) exceeds "
                f"max_teams_per_district ({self.max_teams_per_district}); no allocation "
                "can satisfy both."
            )
        required = self.min_teams_high_risk * len(self.high_risk_districts)
        if required > self.total_team_weeks:
            raise ValueError(
                f"The high-risk floor needs {required} team-weeks "
                f"({len(self.high_risk_districts)} districts x {self.min_teams_high_risk}) "
                f"but the budget is only {self.total_team_weeks}. Either raise the budget "
                "or lower the floor."
            )


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
        PuLP status string. Anything other than ``"Optimal"`` means the result
        should not be acted on.
    shadow_price_budget:
        Marginal cases averted per additional team-week, from the LP
        relaxation's dual on the budget constraint. This is the number that
        answers "should we fund more teams?", so it is surfaced even though it
        is a by-product.
    risk_quantile:
        Forecast quantile the allocation was optimised against.
    """

    iso_week: pd.Period
    allocation: dict[str, int]
    expected_cases_averted: float
    budget_used: int
    budget_available: int
    solver_status: str
    shadow_price_budget: float | None = None
    risk_quantile: float = 0.5

    def to_frame(self) -> pd.DataFrame:
        """Tidy one-row-per-district view of the allocation."""
        return (
            pd.DataFrame(
                {
                    "district_id": list(self.allocation.keys()),
                    "team_weeks": list(self.allocation.values()),
                }
            )
            .assign(iso_week=self.iso_week, risk_quantile=self.risk_quantile)
            .sort_values("team_weeks", ascending=False)
            .reset_index(drop=True)
        )


def _effect_lookup(
    effect_table: pd.DataFrame, value_column: str
) -> tuple[dict[tuple[str, int], float], list[str], int]:
    """Build ``(district, k) -> averted`` plus the district list and max level."""
    required = {"district_id", "team_weeks", value_column}
    missing = required - set(effect_table.columns)
    if missing:
        raise ValueError(f"Effect table is missing columns: {sorted(missing)}")

    lookup: dict[tuple[str, int], float] = {}
    for row in effect_table.itertuples(index=False):
        lookup[(str(row.district_id), int(row.team_weeks))] = float(getattr(row, value_column))

    districts = sorted({d for d, _ in lookup})
    max_level = max(k for _, k in lookup)
    return lookup, districts, max_level


def allocate(
    effect_table: pd.DataFrame,
    constraints: AllocationConstraints,
    iso_week: pd.Period,
    *,
    previous_allocation: dict[str, int] | None = None,
    risk_quantile: float = 0.5,
    compute_shadow_price: bool = True,
) -> AllocationResult:
    """Solve the weekly team-allocation ILP.

    Parameters
    ----------
    effect_table:
        Output of :func:`dengue.causal.sei_sir.build_effect_table`.
    constraints:
        Operational constraints.
    iso_week:
        Week being allocated.
    previous_allocation:
        Last week's allocation. Required if ``max_weekly_change`` is set;
        ignored (with a debug note) otherwise.
    risk_quantile:
        Which effect column to optimise: 0.5 for the median, 0.9 for a
        risk-averse allocation.
    compute_shadow_price:
        Also solve the LP relaxation to recover the budget dual.

    Returns
    -------
    AllocationResult

    Raises
    ------
    ValueError
        If the constraints are contradictory or the effect table is malformed.
    RuntimeError
        If the solver fails to find an optimal solution.
    """
    import pulp

    constraints.validate()
    if risk_quantile not in _QUANTILE_COLUMN:
        raise ValueError(
            f"risk_quantile must be one of {sorted(_QUANTILE_COLUMN)}, got {risk_quantile}"
        )

    value_column = _QUANTILE_COLUMN[risk_quantile]
    lookup, districts, max_level = _effect_lookup(effect_table, value_column)
    cap = min(constraints.max_teams_per_district, max_level)

    def build(binary: bool) -> tuple[pulp.LpProblem, dict]:
        problem = pulp.LpProblem("dengue_team_allocation", pulp.LpMaximize)
        category = "Binary" if binary else "Continuous"
        x = {
            (d, k): pulp.LpVariable(f"x_{d}_{k}", lowBound=0, upBound=1, cat=category)
            for d in districts
            for k in range(cap + 1)
        }

        # Objective: total expected cases averted.
        problem += pulp.lpSum(
            lookup.get((d, k), 0.0) * x[(d, k)] for d in districts for k in range(cap + 1)
        )

        # 1. Exactly one intensity level per district.
        for d in districts:
            problem += pulp.lpSum(x[(d, k)] for k in range(cap + 1)) == 1, f"one_level_{d}"

        # 2. Budget. Named so the dual can be recovered by name.
        problem += (
            pulp.lpSum(k * x[(d, k)] for d in districts for k in range(cap + 1))
            <= constraints.total_team_weeks,
            "budget",
        )

        # 3. High-risk floor.
        for d in constraints.high_risk_districts:
            if d not in set(districts):
                continue
            problem += (
                pulp.lpSum(k * x[(d, k)] for k in range(cap + 1))
                >= constraints.min_teams_high_risk,
                f"high_risk_floor_{d}",
            )

        # 5. Week-to-week continuity.
        if constraints.max_weekly_change is not None and previous_allocation:
            for d in districts:
                previous = int(previous_allocation.get(d, 0))
                assigned = pulp.lpSum(k * x[(d, k)] for k in range(cap + 1))
                problem += (
                    assigned - previous <= constraints.max_weekly_change,
                    f"continuity_up_{d}",
                )
                problem += (
                    previous - assigned <= constraints.max_weekly_change,
                    f"continuity_down_{d}",
                )

        return problem, x

    problem, x = build(binary=True)
    problem.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus[problem.status]

    if status != "Optimal":
        raise RuntimeError(
            f"Allocation ILP did not solve to optimality for {iso_week}: status={status}. "
            "The constraint set is likely infeasible -- check the high-risk floor against "
            "the budget."
        )

    allocation: dict[str, int] = {}
    for d in districts:
        chosen = [k for k in range(cap + 1) if x[(d, k)].value() and x[(d, k)].value() > 0.5]
        allocation[d] = int(chosen[0]) if chosen else 0

    objective = float(pulp.value(problem.objective) or 0.0)
    budget_used = int(sum(allocation.values()))

    # Shadow price from the LP relaxation: the ILP has no meaningful duals.
    shadow_price: float | None = None
    if compute_shadow_price:
        try:
            relaxed, _ = build(binary=False)
            relaxed.solve(pulp.PULP_CBC_CMD(msg=False))
            if pulp.LpStatus[relaxed.status] == "Optimal":
                budget_constraint = relaxed.constraints.get("budget")
                if budget_constraint is not None and budget_constraint.pi is not None:
                    shadow_price = abs(float(budget_constraint.pi))
        except Exception as exc:  # - the dual is a nice-to-have
            log.debug("allocate: shadow price unavailable: %s", exc)

    log.info(
        "allocate[%s]: status=%s  averted=%.1f  budget=%d/%d  districts_served=%d  "
        "shadow_price=%s  q=%.1f",
        iso_week,
        status,
        objective,
        budget_used,
        constraints.total_team_weeks,
        sum(1 for v in allocation.values() if v > 0),
        f"{shadow_price:.3f}" if shadow_price is not None else "n/a",
        risk_quantile,
    )

    return AllocationResult(
        iso_week=iso_week,
        allocation=allocation,
        expected_cases_averted=objective,
        budget_used=budget_used,
        budget_available=constraints.total_team_weeks,
        solver_status=status,
        shadow_price_budget=shadow_price,
        risk_quantile=risk_quantile,
    )


def greedy_allocate(
    effect_table: pd.DataFrame,
    constraints: AllocationConstraints,
    iso_week: pd.Period,
    *,
    risk_quantile: float = 0.5,
) -> AllocationResult:
    """Rank-and-fill baseline: the policy the ILP has to beat.

    Assigns the whole per-district cap to districts in descending order of total
    cases averted at the cap, until the budget runs out. This stands in for "send
    teams to the worst districts", and comparing against it is how the ILP's
    value is demonstrated rather than asserted.

    **It honours the same constraints as the ILP** -- the high-risk floor is
    satisfied first, then the remainder is filled by rank, and the per-district
    cap is respected throughout. That fairness matters: an earlier version
    ignored the floor, which let it beat the ILP at tight budgets purely by
    solving an easier, operationally infeasible problem. Any margin reported now
    comes from allocation logic, not from a different constraint set.

    The one constraint it does not model is week-to-week continuity, which is
    meaningless for a single-shot baseline.
    """
    value_column = _QUANTILE_COLUMN[risk_quantile]
    lookup, districts, max_level = _effect_lookup(effect_table, value_column)
    cap = min(constraints.max_teams_per_district, max_level)

    allocation = dict.fromkeys(districts, 0)
    remaining = constraints.total_team_weeks

    # Satisfy the high-risk floor first, exactly as the ILP must.
    for d in constraints.high_risk_districts:
        if d not in allocation or remaining <= 0:
            continue
        take = min(constraints.min_teams_high_risk, cap, remaining)
        allocation[d] = take
        remaining -= take

    # Then fill by rank, topping districts up to the cap.
    ranked = sorted(districts, key=lambda d: lookup.get((d, cap), 0.0), reverse=True)
    for d in ranked:
        if remaining <= 0:
            break
        take = min(cap - allocation[d], remaining)
        if take <= 0:
            continue
        allocation[d] += take
        remaining -= take

    objective = float(sum(lookup.get((d, k), 0.0) for d, k in allocation.items()))
    return AllocationResult(
        iso_week=iso_week,
        allocation=allocation,
        expected_cases_averted=objective,
        budget_used=int(sum(allocation.values())),
        budget_available=constraints.total_team_weeks,
        solver_status="Greedy",
        risk_quantile=risk_quantile,
    )


def allocate_budget_sweep(
    effect_table: pd.DataFrame,
    iso_week: pd.Period,
    budgets: list[int],
    *,
    max_teams_per_district: int = 12,
    min_teams_high_risk: int = 2,
    high_risk_districts: tuple[str, ...] = (),
    risk_quantiles: tuple[float, ...] = (0.5, 0.9),
    include_greedy: bool = True,
) -> pd.DataFrame:
    """Solve the allocation across a grid of budgets and risk postures.

    This is what makes the dashboard interactive without ever running a solver
    at request time: every budget the user can select is precomputed here and
    cached to a Parquet artifact.

    Returns
    -------
    pandas.DataFrame
        Long frame: ``budget``, ``risk_quantile``, ``strategy``, ``district_id``,
        ``team_weeks``, ``expected_cases_averted`` (total for that scenario),
        ``shadow_price_budget``, ``solver_status``.
    """
    rows: list[dict[str, object]] = []

    for budget in budgets:
        for q in risk_quantiles:
            constraints = AllocationConstraints(
                total_team_weeks=budget,
                max_teams_per_district=max_teams_per_district,
                min_teams_high_risk=min_teams_high_risk,
                # The sweep is a standalone planning view, so continuity against
                # a previous week does not apply.
                max_weekly_change=None,
                high_risk_districts=high_risk_districts,
            )
            try:
                constraints.validate()
            except ValueError as exc:
                log.warning("allocate_sweep: skipping budget=%d q=%.1f (%s)", budget, q, exc)
                continue

            strategies: list[tuple[str, AllocationResult]] = []
            try:
                strategies.append(
                    ("ilp", allocate(effect_table, constraints, iso_week, risk_quantile=q))
                )
            except (RuntimeError, ValueError) as exc:
                log.warning("allocate_sweep: ILP failed at budget=%d q=%.1f: %s", budget, q, exc)
                continue

            if include_greedy:
                strategies.append(
                    (
                        "greedy",
                        greedy_allocate(effect_table, constraints, iso_week, risk_quantile=q),
                    )
                )

            for strategy, result in strategies:
                for district_id, team_weeks in result.allocation.items():
                    rows.append(
                        {
                            "budget": budget,
                            "risk_quantile": q,
                            "strategy": strategy,
                            "district_id": district_id,
                            "team_weeks": team_weeks,
                            "expected_cases_averted": result.expected_cases_averted,
                            "shadow_price_budget": result.shadow_price_budget,
                            "solver_status": result.solver_status,
                        }
                    )

    frame = pd.DataFrame(rows)
    if not frame.empty:
        log.info(
            "allocate_sweep: %d scenarios (%d budgets x %d quantiles x %d strategies)",
            frame.groupby(["budget", "risk_quantile", "strategy"], observed=True).ngroups,
            frame["budget"].nunique(),
            frame["risk_quantile"].nunique(),
            frame["strategy"].nunique(),
        )
    return frame


def allocate_rolling(
    effect_tables: dict[pd.Period, pd.DataFrame],
    constraints: AllocationConstraints,
    *,
    risk_quantile: float = 0.5,
) -> pd.DataFrame:
    """Solve a sequence of weeks, chaining the continuity constraint.

    Each week's allocation is constrained against the previous week's solution,
    so the plan is deliverable rather than a sequence of unrelated optima.
    """
    previous: dict[str, int] | None = None
    frames: list[pd.DataFrame] = []

    for iso_week in sorted(effect_tables):
        result = allocate(
            effect_tables[iso_week],
            constraints,
            iso_week,
            previous_allocation=previous,
            risk_quantile=risk_quantile,
        )
        frame = result.to_frame()
        frame["expected_cases_averted"] = result.expected_cases_averted
        frames.append(frame)
        previous = result.allocation

    return (
        pd.concat(frames, ignore_index=True)
        if frames
        else pd.DataFrame(columns=["iso_week", "district_id", "team_weeks"])
    )


def evaluate_allocation(
    allocation: AllocationResult,
    effect_table: pd.DataFrame,
    *,
    comparison: AllocationResult | None = None,
) -> dict[str, float]:
    """Score an allocation, optionally against a comparison strategy.

    Returns
    -------
    dict
        ``expected_cases_averted``, ``budget_used``, ``budget_utilisation``,
        ``districts_served``, ``gini_concentration`` and, when ``comparison`` is
        given, ``uplift_vs_comparison`` and ``uplift_pct``.
    """
    values = np.array(list(allocation.allocation.values()), dtype=float)
    served = int((values > 0).sum())

    # Gini of the allocation: 0 = spread evenly, 1 = all teams in one district.
    if values.sum() > 0:
        sorted_values = np.sort(values)
        n = len(sorted_values)
        index = np.arange(1, n + 1)
        gini = float(
            (2 * np.sum(index * sorted_values)) / (n * np.sum(sorted_values)) - (n + 1) / n
        )
    else:
        gini = 0.0

    metrics = {
        "expected_cases_averted": allocation.expected_cases_averted,
        "budget_used": float(allocation.budget_used),
        "budget_utilisation": (
            allocation.budget_used / allocation.budget_available
            if allocation.budget_available
            else 0.0
        ),
        "districts_served": float(served),
        "gini_concentration": gini,
    }

    if comparison is not None:
        uplift = allocation.expected_cases_averted - comparison.expected_cases_averted
        metrics["uplift_vs_comparison"] = float(uplift)
        metrics["uplift_pct"] = float(
            100.0 * uplift / comparison.expected_cases_averted
            if comparison.expected_cases_averted
            else 0.0
        )

    return metrics
