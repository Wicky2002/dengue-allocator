"""Platform-layer tests: RBAC, provenance, risk bands, readiness, budget.

The RBAC tests matter most. A dashboard that leaks hospital occupancy to the
public portal, or district operations across a regional boundary, is a real
harm â€” and it is the kind of bug that looks fine on screen because you are
logged in as the role that may see everything.
"""

from __future__ import annotations

import itertools

import pandas as pd
import pytest

from dengue import config
from dengue.optim.budget import default_categories, optimise_budget
from dengue.platform.hospital import (
    ClinicalRatios,
    build_readiness_table,
    estimate_readiness,
    supply_shortfalls,
)
from dengue.platform.provenance import ProvenanceTier, Quantity, unavailable_reason
from dengue.platform.rbac import (
    DEMO_PRINCIPALS,
    ROLE_PERMISSIONS,
    Permission,
    Principal,
    Role,
    filter_to_scope,
)
from dengue.platform.risk import RiskLevel, assess_all, classify, national_summary, recommend

# --------------------------------------------------------------------------
# RBAC
# --------------------------------------------------------------------------


def test_public_cannot_see_operational_data():
    """The single most important access rule on the platform."""
    public = DEMO_PRINCIPALS[Role.PUBLIC]
    for forbidden in (
        Permission.VIEW_HOSPITAL_READINESS,
        Permission.VIEW_SUPPLY_PLANNING,
        Permission.VIEW_TEAM_ALLOCATION,
        Permission.VIEW_DISTRICT_OPERATIONS,
        Permission.MANAGE_USERS,
        Permission.VIEW_AUDIT_LOG,
    ):
        assert not public.can(forbidden), f"public must not hold {forbidden.value}"


def test_permissions_are_additive_by_rank():
    """Each role holds a superset of the one below it."""
    order = [Role.PUBLIC, Role.HOSPITAL_STAFF, Role.MOH_OFFICER, Role.NATIONAL_ADMIN]
    for lower, higher in itertools.pairwise(order):
        assert (
            ROLE_PERMISSIONS[lower] <= ROLE_PERMISSIONS[higher]
        ), f"{higher.value} does not include everything {lower.value} has"


def test_hospital_staff_cannot_reach_moh_or_admin_powers():
    staff = DEMO_PRINCIPALS[Role.HOSPITAL_STAFF]
    assert staff.can(Permission.VIEW_HOSPITAL_READINESS)
    assert not staff.can(Permission.VIEW_TEAM_ALLOCATION)
    assert not staff.can(Permission.EDIT_INTERVENTION_PLAN)
    assert not staff.can(Permission.CONFIGURE_MODELS)


def test_moh_officer_cannot_reach_admin_powers():
    moh = DEMO_PRINCIPALS[Role.MOH_OFFICER]
    assert moh.can(Permission.VIEW_TEAM_ALLOCATION)
    assert moh.can(Permission.RUN_SCENARIO)
    assert not moh.can(Permission.MANAGE_USERS)
    assert not moh.can(Permission.TRIGGER_RETRAIN)
    assert not moh.can(Permission.VIEW_NATIONAL_OPERATIONS)


def test_admin_holds_every_permission():
    admin = DEMO_PRINCIPALS[Role.NATIONAL_ADMIN]
    every = {p for ps in ROLE_PERMISSIONS.values() for p in ps}
    assert every <= admin.permissions


def test_district_scope_is_enforced():
    """A regional officer must not see another region's operations."""
    moh = Principal(Role.MOH_OFFICER, "RDHS Gampaha", districts=("gampaha",))
    assert moh.may_see_district("gampaha")
    assert not moh.may_see_district("jaffna")
    assert not moh.may_see_district("colombo")


def test_scoped_roles_must_declare_districts():
    """Guards the worst misconfiguration: empty scope silently meaning national."""
    with pytest.raises(ValueError, match="must be scoped to at least one district"):
        Principal(Role.MOH_OFFICER, "unscoped")
    with pytest.raises(ValueError, match="must be scoped to at least one district"):
        Principal(Role.HOSPITAL_STAFF, "unscoped")


def test_unknown_district_in_scope_raises():
    with pytest.raises(ValueError, match="unknown districts"):
        Principal(Role.MOH_OFFICER, "bad", districts=("atlantis",))


def test_filter_to_scope_restricts_rows():
    frame = pd.DataFrame({"district_id": ["gampaha", "colombo", "jaffna"], "v": [1, 2, 3]})
    moh = Principal(Role.MOH_OFFICER, "RDHS", districts=("gampaha",))
    assert list(filter_to_scope(frame, moh)["district_id"]) == ["gampaha"]

    admin = DEMO_PRINCIPALS[Role.NATIONAL_ADMIN]
    assert len(filter_to_scope(frame, admin)) == 3


def test_require_raises_for_missing_permission():
    public = DEMO_PRINCIPALS[Role.PUBLIC]
    with pytest.raises(PermissionError, match="does not have permission"):
        public.require(Permission.MANAGE_USERS)


# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------


def test_assumed_quantity_must_state_its_basis():
    """An unexplained planning estimate is indistinguishable from a made-up number."""
    with pytest.raises(ValueError, match="must state its basis"):
        Quantity(100.0, ProvenanceTier.ASSUMED, "beds")


def test_observed_quantity_must_name_its_source():
    with pytest.raises(ValueError, match="must name its source"):
        Quantity(100.0, ProvenanceTier.OBSERVED, "cases")


def test_quantity_renders_its_tier():
    q = Quantity(180.0, ProvenanceTier.ASSUMED, "admissions", basis="55% of forecast")
    assert "Planning estimate" in q.render()
    assert "55% of forecast" in q.caveat()


def test_modelled_quantity_needs_no_extra_metadata():
    q = Quantity(42.0, ProvenanceTier.MODELLED, "cases")
    assert q.render(0) == "42 cases (Modelled)"


def test_tiers_requiring_caveats():
    assert ProvenanceTier.ASSUMED.requires_caveat
    assert ProvenanceTier.USER_INPUT.requires_caveat
    assert not ProvenanceTier.OBSERVED.requires_caveat
    assert not ProvenanceTier.MODELLED.requires_caveat


def test_unavailable_reason_refuses_to_invent():
    text = unavailable_reason("Live bed occupancy")
    assert "not available" in text
    assert "will not display an invented figure" in text


# --------------------------------------------------------------------------
# Risk bands
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("incidence", "expected"),
    [
        (0.0, RiskLevel.LOW),
        (1.4, RiskLevel.LOW),
        (1.5, RiskLevel.MODERATE),
        (3.4, RiskLevel.MODERATE),
        (3.5, RiskLevel.HIGH),
        (6.9, RiskLevel.HIGH),
        (7.0, RiskLevel.SEVERE),
        (500.0, RiskLevel.SEVERE),
    ],
)
def test_risk_bands_are_monotone_at_their_boundaries(incidence, expected):
    assert classify(incidence) is expected


def test_risk_levels_have_distinct_colours():
    colours = {level.colour for level in RiskLevel}
    assert len(colours) == 4


def test_public_recommendations_escalate_with_risk():
    low = recommend(RiskLevel.LOW, audience="public")
    severe = recommend(RiskLevel.SEVERE, audience="public")
    assert len(severe) > len(low)
    assert any(r.urgency == "urgent" for r in severe)
    assert not any(r.urgency == "urgent" for r in low)


def test_recommendations_differ_by_audience():
    public = recommend(RiskLevel.SEVERE, audience="public")
    moh = recommend(RiskLevel.SEVERE, audience="moh")
    assert {r.action for r in public}.isdisjoint({r.action for r in moh})


def test_every_recommendation_explains_itself():
    """An instruction from a model without a reason is not actionable."""
    for audience in ("public", "hospital", "moh"):
        for level in RiskLevel:
            for rec in recommend(level, rising_fast=True, audience=audience):
                assert rec.rationale.strip(), f"{rec.action} has no rationale"


def test_unknown_audience_raises():
    with pytest.raises(ValueError, match="Unknown audience"):
        recommend(RiskLevel.HIGH, audience="martians")


# --------------------------------------------------------------------------
# Hospital readiness
# --------------------------------------------------------------------------


def test_readiness_scales_with_cases():
    common = {
        "iso_week": pd.Period("2026-08-03", freq=config.WEEK_FREQ),
        "horizon_weeks": 2,
        "bed_capacity": 5000,
    }
    small = estimate_readiness("colombo", 100.0, **common)
    large = estimate_readiness("colombo", 400.0, **common)

    assert large.admissions == pytest.approx(4 * small.admissions)
    assert large.icu_patients > small.icu_patients
    assert large.occupancy_pct > small.occupancy_pct


def test_icu_is_a_subset_of_severe():
    ratios = ClinicalRatios()
    estimate = estimate_readiness(
        "colombo",
        500.0,
        iso_week=pd.Period("2026-08-03", freq=config.WEEK_FREQ),
        horizon_weeks=2,
        bed_capacity=5000,
        ratios=ratios,
    )
    assert estimate.icu_patients <= estimate.severe_cases


def test_ratios_reject_icu_exceeding_severe():
    with pytest.raises(ValueError, match="ICU care is a subset"):
        ClinicalRatios(severe_fraction_of_admitted=0.02, icu_fraction_of_admitted=0.10).validate()


def test_ratios_reject_out_of_range_fractions():
    with pytest.raises(ValueError, match="fraction in"):
        ClinicalRatios(hospitalisation_rate=1.5).validate()


def test_capacity_status_bands():
    week = pd.Period("2026-08-03", freq=config.WEEK_FREQ)
    low = estimate_readiness("colombo", 10.0, iso_week=week, horizon_weeks=2, bed_capacity=100_000)
    high = estimate_readiness("colombo", 90_000.0, iso_week=week, horizon_weeks=2, bed_capacity=200)
    assert low.capacity_status == "normal"
    assert high.capacity_status == "over_capacity"
    assert high.is_over_capacity


def test_every_readiness_number_is_tagged_as_an_estimate():
    """Nothing on the hospital page may pass itself off as a measurement."""
    estimate = estimate_readiness(
        "colombo",
        200.0,
        iso_week=pd.Period("2026-08-03", freq=config.WEEK_FREQ),
        horizon_weeks=2,
        bed_capacity=5000,
    )
    quantities = estimate.as_quantities()
    assert quantities
    for name, quantity in quantities.items():
        assert quantity.tier is ProvenanceTier.ASSUMED, f"{name} is not tagged as an estimate"
        assert quantity.basis, f"{name} has no stated basis"


def test_supply_shortfalls_are_null_without_stock_data():
    """Without an inventory feed, shortfall must be unknown, not invented."""
    readiness = pd.DataFrame(
        {
            "district_id": ["colombo"],
            "district": ["Colombo"],
            "platelet_units": [100.0],
            "iv_fluid_litres": [500.0],
            "diagnostic_tests": [200.0],
        }
    )
    out = supply_shortfalls(readiness)
    assert out["platelet_units_shortfall"].isna().all()
    assert not out["stock_data_available"].iloc[0]


def test_supply_shortfalls_computed_when_stock_known():
    readiness = pd.DataFrame(
        {
            "district_id": ["colombo"],
            "district": ["Colombo"],
            "platelet_units": [100.0],
            "iv_fluid_litres": [500.0],
            "diagnostic_tests": [200.0],
        }
    )
    out = supply_shortfalls(readiness, {"colombo": {"platelet_units": 60.0}})
    assert float(out["platelet_units_shortfall"].iloc[0]) == pytest.approx(40.0)


# --------------------------------------------------------------------------
# Budget optimiser
# --------------------------------------------------------------------------


def test_budget_allocation_sums_to_the_envelope():
    result = optimise_budget(20e6)
    assert sum(result.allocation_lkr.values()) == pytest.approx(20e6, rel=1e-6)
    assert sum(result.shares.values()) == pytest.approx(1.0, rel=1e-6)


def test_budget_respects_share_bounds():
    categories = default_categories()
    result = optimise_budget(20e6, categories)
    by_key = {c.key: c for c in categories}
    for key, share in result.shares.items():
        assert share >= by_key[key].min_share - 1e-6, f"{key} below its floor"
        assert share <= by_key[key].max_share + 1e-6, f"{key} above its ceiling"


def test_budget_effect_increases_with_envelope():
    small = optimise_budget(5e6)
    large = optimise_budget(50e6)
    assert large.total_effect > small.total_effect


def test_budget_returns_diminish():
    """Doubling the envelope must not double the effect."""
    base = optimise_budget(10e6).total_effect
    double = optimise_budget(20e6).total_effect
    assert double < 2 * base


def test_budget_rejects_non_positive_envelope():
    with pytest.raises(ValueError, match="must be positive"):
        optimise_budget(0)


def test_budget_rejects_infeasible_minimum_shares():
    from dengue.optim.budget import BudgetCategory

    categories = (
        BudgetCategory("a", "A", "", 1e6, 100, min_share=0.7),
        BudgetCategory("b", "B", "", 1e6, 100, min_share=0.7),
    )
    with pytest.raises(ValueError, match="exceeds the budget"):
        optimise_budget(10e6, categories)


def test_category_effect_is_concave():
    category = default_categories()[0]
    first = category.effect(5e6) - category.effect(0)
    second = category.effect(10e6) - category.effect(5e6)
    assert second < first


# --------------------------------------------------------------------------
# End-to-end over the risk frame
# --------------------------------------------------------------------------


def _fake_district_risk() -> pd.DataFrame:
    ids = list(config.DISTRICT_IDS[:6])
    return pd.DataFrame(
        {
            "district_id": ids,
            "horizon": 2,
            "q0.1": [10, 20, 5, 2, 1, 0],
            "q0.5": [400, 200, 50, 20, 5, 1],
            "q0.9": [800, 400, 90, 40, 12, 4],
            "incidence_per_100k": [20.0, 9.0, 4.0, 1.0, 0.4, 0.1],
            "change_vs_recent_pct": [45.0, 10.0, -5.0, 0.0, 2.0, 0.0],
            "target_week": pd.Period("2026-08-03", freq=config.WEEK_FREQ),
        }
    )


def test_assess_all_orders_worst_first():
    assessments = assess_all(_fake_district_risk(), horizon_weeks=2)
    ranks = [a.risk_level.rank for a in assessments]
    assert ranks == sorted(ranks, reverse=True)
    assert assessments[0].risk_level is RiskLevel.SEVERE


def test_national_summary_counts_bands():
    summary = national_summary(assess_all(_fake_district_risk(), horizon_weeks=2))
    assert summary["n_districts"] == 6
    # Fixture incidences [20.0, 9.0, 4.0, 1.0, 0.4, 0.1] against the current
    # thresholds (Moderate 1.5 / High 3.5 / Severe 7.0, see risk.py): 20.0 and
    # 9.0 both clear Severe, 4.0 lands in High, the rest are Low.
    assert summary["n_severe"] == 2
    assert summary["n_rising_fast"] == 1
    assert summary["total_forecast_cases"] == pytest.approx(676.0)


def test_readiness_table_covers_every_district_in_the_frame():
    risk = _fake_district_risk()
    capacity = pd.DataFrame(
        {"district_id": list(config.DISTRICT_IDS[:6]), "estimated_beds": [9000] * 6}
    )
    table = build_readiness_table(risk, capacity, horizon_weeks=2)
    assert len(table) == 6
    assert table["all_values_are_estimates"].all()
    assert (table["occupancy_pct"] >= 0).all()
