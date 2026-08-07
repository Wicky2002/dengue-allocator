"""Budget optimiser -- splitting money across intervention categories.

Stage 3 allocates *teams* across districts. This allocates *money* across
activity types, which is a different decision made by different people: the
Stage 3 ILP answers "where do this week's teams go", this answers "how much of
the annual envelope should be vector control versus hospital preparedness".

Structure
---------
Each category has a **concave** return curve — spend-to-effect with diminishing
returns, for the same reason Stage 2's curves bend: the first rupee buys the
easiest wins. Categories also differ in *when* they pay off, which is the part a
single "cases averted" number hides:

===================  =========================================================
Category             Character
===================  =========================================================
Vector control       Fast-acting, well-evidenced, saturates quickly. Anchored
                     to the Stage 2 effect curve, so it is the one category
                     with a mechanistic basis rather than an assumed elasticity.
Public awareness     Cheap per person, slow, and dependent on sustained
                     household behaviour. Saturates hard — the tenth campaign
                     reaches the same people as the ninth.
Hospital preparation Does not prevent a single case. It converts severe cases
                     into survivable ones, so its return is expressed as
                     deaths/complications averted rather than cases averted.
Emergency reserve    Buys nothing in expectation but caps the downside of a
                     forecast miss. Modelled with a floor, because a
                     pure-expectation optimiser always spends it to zero.
===================  =========================================================

Honesty about the elasticities
------------------------------
Only the vector-control curve is anchored to a mechanistic model. The other
three use **assumed elasticities** and are tagged
:attr:`~dengue.platform.provenance.ProvenanceTier.ASSUMED`. They are plausible
planning parameters, not measured cost-effectiveness for Sri Lanka. The
recommended split is therefore best read as *a structured argument about
trade-offs*, not as an evidence-based funding instruction — and the UI says so.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from dengue.platform.provenance import ProvenanceTier, Quantity
from dengue.utils.logging import get_logger

log = get_logger(__name__)


@dataclass(frozen=True)
class BudgetCategory:
    """One spending category and its return curve.

    Attributes
    ----------
    key, name, description:
        Identity and UI copy.
    saturation_lkr:
        Spend at which the category reaches ``1 - 1/e`` (~63%) of its maximum
        achievable effect. Sets how fast returns diminish.
    max_effect:
        Effect at unlimited spend, in cases-averted-equivalents.
    min_share, max_share:
        Policy bounds on this category's share of the envelope.
    evidence_tier:
        Provenance of the return curve.
    """

    key: str
    name: str
    description: str
    saturation_lkr: float
    max_effect: float
    min_share: float = 0.0
    max_share: float = 1.0
    evidence_tier: ProvenanceTier = ProvenanceTier.ASSUMED

    def effect(self, spend_lkr: float) -> float:
        """Cases-averted-equivalent at a given spend. Concave and saturating."""
        if spend_lkr <= 0 or self.saturation_lkr <= 0:
            return 0.0
        return self.max_effect * (1.0 - np.exp(-spend_lkr / self.saturation_lkr))

    def marginal(self, spend_lkr: float) -> float:
        """Derivative of :meth:`effect` -- effect per additional rupee."""
        if self.saturation_lkr <= 0:
            return 0.0
        return (self.max_effect / self.saturation_lkr) * float(
            np.exp(-max(spend_lkr, 0.0) / self.saturation_lkr)
        )


#: Reference envelope used to place the saturation points, in rupees.
#:
#: These curves are **deliberately anchored to an absolute figure, not to the
#: envelope being evaluated**. Scaling saturation with the budget would make the
#: whole problem scale-invariant: doubling the envelope would exactly double the
#: effect and leave the recommended shares unchanged, so the optimiser would
#: answer "twice the money is twice as good" at every budget. That is precisely
#: the answer a budget tool must not give, since diminishing returns are the
#: entire question. Saturation is a property of how much intervention the
#: country can absorb, not of how much money happens to be available.
REFERENCE_ENVELOPE_LKR = 50e6

#: Fallback maximum effect for vector control when no Stage 2 effect table is
#: supplied, in cases-averted-equivalents. Absolute, for the same reason.
DEFAULT_VECTOR_MAX_EFFECT = 1_250.0


def default_categories(
    vector_max_effect: float | None = None,
    *,
    reference_envelope_lkr: float = REFERENCE_ENVELOPE_LKR,
) -> tuple[BudgetCategory, ...]:
    """Standard four-category structure.

    Parameters
    ----------
    vector_max_effect:
        Maximum cases averted by vector control at unlimited spend, ideally the
        total from the Stage 2 effect table. When supplied, vector control is
        the one category with a mechanistic basis; the rest stay assumed.
    reference_envelope_lkr:
        Absolute scale at which the return curves bend. **Not** the envelope
        being optimised -- see :data:`REFERENCE_ENVELOPE_LKR`.
    """
    budget = max(reference_envelope_lkr, 1.0)
    vector_effect = (
        vector_max_effect if vector_max_effect is not None else DEFAULT_VECTOR_MAX_EFFECT
    )

    return (
        BudgetCategory(
            "vector_control",
            "Vector control",
            "Fogging, larviciding, source reduction, and the teams to do it.",
            saturation_lkr=budget * 0.30,
            max_effect=vector_effect,
            min_share=0.20,
            max_share=0.60,
            evidence_tier=(
                ProvenanceTier.MODELLED if vector_max_effect is not None else ProvenanceTier.ASSUMED
            ),
        ),
        BudgetCategory(
            "awareness",
            "Public awareness",
            "Campaigns, school programmes, community mobilisation.",
            saturation_lkr=budget * 0.15,
            max_effect=vector_effect * 0.45,
            min_share=0.10,
            max_share=0.35,
        ),
        BudgetCategory(
            "hospital_preparedness",
            "Hospital preparedness",
            "Surge staffing, platelet and fluid stock, ward readiness. Averts "
            "complications rather than infections.",
            saturation_lkr=budget * 0.25,
            max_effect=vector_effect * 0.55,
            min_share=0.15,
            max_share=0.40,
        ),
        BudgetCategory(
            "emergency_reserve",
            "Emergency reserve",
            "Held against a forecast miss. Buys nothing in expectation; caps the " "downside.",
            saturation_lkr=budget * 0.10,
            max_effect=vector_effect * 0.18,
            min_share=0.10,
            max_share=0.25,
        ),
    )


@dataclass(frozen=True)
class BudgetAllocation:
    """A recommended split of the envelope.

    Attributes
    ----------
    total_budget_lkr:
        The envelope.
    allocation_lkr:
        ``category key -> rupees``.
    shares:
        ``category key -> fraction of the envelope``.
    total_effect:
        Sum of category effects, in cases-averted-equivalents.
    marginal_by_category:
        Effect per additional rupee at the optimum. At an interior optimum these
        equalise -- if they have not, a bound is binding, which is worth
        surfacing rather than hiding.
    binding_constraints:
        Categories sitting on a share bound.
    """

    total_budget_lkr: float
    allocation_lkr: dict[str, float]
    shares: dict[str, float]
    total_effect: float
    marginal_by_category: dict[str, float]
    binding_constraints: tuple[str, ...] = field(default_factory=tuple)

    def to_frame(self, categories: tuple[BudgetCategory, ...]) -> pd.DataFrame:
        by_key = {c.key: c for c in categories}
        return pd.DataFrame(
            [
                {
                    "category": by_key[k].name,
                    "key": k,
                    "amount_lkr": v,
                    "share_pct": 100.0 * self.shares[k],
                    "effect": by_key[k].effect(v),
                    "marginal_per_million_lkr": self.marginal_by_category[k] * 1e6,
                    "evidence": by_key[k].evidence_tier.label,
                    "description": by_key[k].description,
                }
                for k, v in self.allocation_lkr.items()
            ]
        ).sort_values("amount_lkr", ascending=False)

    def as_quantity(self) -> Quantity:
        return Quantity(
            self.total_effect,
            ProvenanceTier.ASSUMED,
            "cases-averted-equivalent",
            basis=(
                "Concave return curves per category; only vector control is anchored "
                "to the mechanistic Stage 2 model, the rest use assumed elasticities"
            ),
        )


def optimise_budget(
    total_budget_lkr: float,
    categories: tuple[BudgetCategory, ...] | None = None,
    *,
    n_steps: int = 400,
) -> BudgetAllocation:
    """Allocate the envelope across categories to maximise total effect.

    Uses **greedy marginal allocation**: repeatedly give the next slice of money
    to whichever category currently has the highest marginal return, subject to
    its share bounds. Because every category's return curve is concave, greedy
    marginal allocation is provably optimal here — the same argument that makes
    the water-filling solution optimal. No solver is needed, so this runs in
    milliseconds and can be swept across budgets for the UI.

    Parameters
    ----------
    total_budget_lkr:
        The envelope in rupees.
    categories:
        Categories and their curves. Defaults to :func:`default_categories`.
    n_steps:
        Allocation granularity. 400 steps on a 20 M envelope is 50,000-rupee
        resolution, far finer than the decision needs.
    """
    if total_budget_lkr <= 0:
        raise ValueError("total_budget_lkr must be positive")

    categories = categories or default_categories()

    total_min = sum(c.min_share for c in categories)
    if total_min > 1.0 + 1e-9:
        raise ValueError(
            f"Category minimum shares sum to {total_min:.0%}, which exceeds the budget. "
            "Lower min_share on one or more categories."
        )

    # Seed every category at its floor, then distribute what is left greedily.
    allocation = {c.key: c.min_share * total_budget_lkr for c in categories}
    remaining = total_budget_lkr - sum(allocation.values())
    step = remaining / n_steps if n_steps else 0.0
    by_key = {c.key: c for c in categories}

    for _ in range(n_steps):
        if remaining <= 1e-9:
            break
        best_key, best_marginal = None, -np.inf
        for category in categories:
            current = allocation[category.key]
            if current + step > category.max_share * total_budget_lkr + 1e-9:
                continue  # would breach the ceiling
            marginal = category.marginal(current)
            if marginal > best_marginal:
                best_key, best_marginal = category.key, marginal
        if best_key is None:
            break
        allocation[best_key] += step
        remaining -= step

    shares = {k: v / total_budget_lkr for k, v in allocation.items()}
    marginals = {k: by_key[k].marginal(v) for k, v in allocation.items()}
    total_effect = float(sum(by_key[k].effect(v) for k, v in allocation.items()))

    binding = tuple(
        k
        for k, share in shares.items()
        if abs(share - by_key[k].min_share) < 1e-6 or abs(share - by_key[k].max_share) < 1e-6
    )

    log.info(
        "budget: LKR %.1fM -> %s  effect=%.1f  binding=%s",
        total_budget_lkr / 1e6,
        {k: f"{100 * s:.0f}%" for k, s in shares.items()},
        total_effect,
        list(binding),
    )

    return BudgetAllocation(
        total_budget_lkr=total_budget_lkr,
        allocation_lkr=allocation,
        shares=shares,
        total_effect=total_effect,
        marginal_by_category=marginals,
        binding_constraints=binding,
    )


def budget_sweep(budgets_lkr: list[float], vector_max_effect: float | None = None) -> pd.DataFrame:
    """Optimise across a grid of envelopes, for the dashboard slider.

    Precomputed for the same reason as the Stage 3 sweep: the UI stays
    interactive without optimising at request time.
    """
    # One category set for the whole sweep: the curves are absolute, so they must
    # not be rebuilt per budget.
    categories = default_categories(vector_max_effect)

    rows: list[dict[str, object]] = []
    for budget in budgets_lkr:
        result = optimise_budget(budget, categories)
        for key, amount in result.allocation_lkr.items():
            category = next(c for c in categories if c.key == key)
            rows.append(
                {
                    "budget_lkr": budget,
                    "category_key": key,
                    "category": category.name,
                    "description": category.description,
                    "amount_lkr": amount,
                    "share_pct": 100.0 * result.shares[key],
                    "category_effect": category.effect(amount),
                    "total_effect": result.total_effect,
                    "evidence": category.evidence_tier.label,
                }
            )
    return pd.DataFrame(rows)
