"""The four role portals.

Each portal is built from the permissions its role actually holds, rather than
by computing the full picture and hiding parts of it. A bug in that arrangement
shows *missing* information rather than leaking hospital occupancy to the public
portal, which is the failure mode worth designing against.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st
from components import (
    choropleth,
    estimate_notice,
    facility_map,
    kpi_grid,
    provenance_badge,
    rainfall_vs_cases,
    recommendation_list,
    risk_pill,
    trend_chart,
)
from theme import CATEGORICAL, kpi_html

from dengue import config
from dengue.platform.provenance import SOURCE_REGISTRY, ProvenanceTier, unavailable_reason
from dengue.platform.rbac import Permission, Principal, filter_to_scope
from dengue.platform.risk import (
    RISK_THRESHOLDS,
    RiskLevel,
    assess_all,
    classify,
    national_summary,
)

DISTRICT_NAMES = {d.district_id: d.name for d in config.DISTRICTS}


def _fmt(value: float, digits: int = 0) -> str:
    return "—" if pd.isna(value) else f"{value:,.{digits}f}"


def _risk_frame(district_risk: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Attach risk bands to the district-risk frame for one horizon."""
    frame = district_risk[district_risk["horizon"] == horizon].copy()
    frame["risk_level"] = frame["incidence_per_100k"].apply(lambda v: classify(float(v or 0)).value)
    frame["district"] = frame["district_id"].map(DISTRICT_NAMES).fillna(frame["district_id"])
    return frame


# ==========================================================================
# Public portal
# ==========================================================================


def public_portal(principal: Principal, data: dict[str, pd.DataFrame], horizon: int) -> None:
    principal.require(Permission.VIEW_PUBLIC_RISK)

    district_risk = data["district_risk"]
    panel = data.get("panel_recent")
    frame = _risk_frame(district_risk, horizon)

    assessments = assess_all(district_risk, horizon_weeks=horizon, audience="public")
    summary = national_summary(assessments)

    st.subheader("Dengue risk across Sri Lanka")
    st.caption(
        f"Forecast for the {horizon} weeks ahead. Updated when the pipeline last ran — "
        "this page is public information and contains no hospital or operational data."
    )

    kpi_grid(
        [
            kpi_html(
                "Districts at high risk",
                str(summary["n_severe"] + summary["n_high"]),
                "High or very high",
                "critical",
            ),
            kpi_html("Rising fast", str(summary["n_rising_fast"]), "Growing more than 20%"),
            kpi_html("Highest risk district", summary["worst_district"], summary["worst_level"]),
            kpi_html(
                "Forecast cases",
                _fmt(summary["total_forecast_cases"]),
                f"Nationwide, {horizon} weeks ahead",
            ),
        ]
    )

    tab_map, tab_district, tab_trend, tab_learn = st.tabs(
        ["Risk map", "My district", "Trends", "Protect yourself"]
    )

    with tab_map:
        chart = choropleth(
            frame,
            value_column="risk_level",
            categorical=True,
            tooltip_columns=[
                ("q0.5", "Forecast cases", ".0f"),
                ("incidence_per_100k", "Per 100,000", ".1f"),
            ],
            legend_title="Risk level",
        )
        if chart is None:
            st.info("Map geometry unavailable. Showing the table instead.")
            st.dataframe(
                frame[["district", "risk_level", "q0.5", "incidence_per_100k"]],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.altair_chart(chart, use_container_width=True)

        cols = st.columns(4)
        for col, level in zip(cols, RiskLevel, strict=False):
            col.markdown(risk_pill(level), unsafe_allow_html=True)
            col.caption(f"Above {int(RISK_THRESHOLDS[level])} per 100,000")

    with tab_district:
        names = sorted(frame["district"].unique())
        default = names.index("Colombo") if "Colombo" in names else 0
        chosen = st.selectbox("Choose your district", names, index=default)

        match = [a for a in assessments if a.district_name == chosen]
        if match:
            a = match[0]
            left, right = st.columns([1, 2])
            with left:
                st.markdown(risk_pill(a.risk_level), unsafe_allow_html=True)
                st.markdown(f"### {a.district_name}")
                arrow = "▲" if a.change_pct > 0 else "▼"
                st.metric(
                    "Forecast cases",
                    _fmt(a.forecast_median),
                    f"{arrow} {abs(a.change_pct):.0f}% vs recent weeks",
                )
                st.caption(
                    f"Likely range {_fmt(a.forecast_lower)}–{_fmt(a.forecast_upper)} cases "
                    f"(80% interval) · {a.incidence_per_100k:.1f} per 100,000"
                )
            with right:
                st.markdown("**What you should do**")
                recommendation_list(a.recommendations)

        if panel is not None and not panel.empty and match:
            history = panel[panel["district_id"] == match[0].district_id]
            if not history.empty:
                st.markdown("**Recent weekly cases**")
                st.altair_chart(trend_chart(history), use_container_width=True)

    with tab_trend:
        if panel is not None and not panel.empty:
            national = (
                panel.groupby("iso_week", observed=True)
                .agg(cases=("cases", "sum"), rain_mm=("rain_mm", "mean"))
                .reset_index()
            )
            st.markdown("**Rainfall and dengue cases**")
            st.altair_chart(rainfall_vs_cases(national), use_container_width=True)
            st.caption(
                "Cases follow rainfall by roughly 6–8 weeks: rain fills containers, "
                "larvae develop, adult mosquitoes emerge, and only then does "
                "transmission rise. That lag is why prevention works best *before* "
                "cases climb."
            )

    with tab_learn:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Symptoms")
            st.markdown(
                "- High fever, severe headache, pain behind the eyes\n"
                "- Muscle and joint pain\n"
                "- Nausea, vomiting, skin rash"
            )
            st.error(
                "**Go to hospital immediately** for severe abdominal pain, persistent "
                "vomiting, bleeding gums or nose, blood in vomit or stool, or extreme "
                "drowsiness. These are warning signs of severe dengue.",
                icon="🚨",
            )
        with c2:
            st.markdown("#### Prevention")
            st.markdown(
                "- Empty and scrub water containers **weekly**\n"
                "- Cover water tanks and barrels\n"
                "- Clear roof gutters, discard tyres and containers\n"
                "- Use repellent — *Aedes* bites during the **day**\n"
                "- Fit window and door screens"
            )
            st.markdown("#### Emergency")
            st.markdown(
                "- **Suwa Sariya ambulance: 1990**\n"
                "- National Dengue Control Unit: +94 11 288 9871\n"
                "- Report a breeding site to your local PHI"
            )

        with st.expander("Myth vs fact"):
            st.markdown(
                "**Myth:** Dengue mosquitoes bite at night.  \n"
                "**Fact:** *Aedes aegypti* bites mainly in daylight, peaking early "
                "morning and late afternoon. Bed nets alone will not protect you.\n\n"
                "**Myth:** Dengue only breeds in dirty water.  \n"
                "**Fact:** It prefers **clean** standing water — exactly what collects "
                "in your water tank, plant trays and buckets.\n\n"
                "**Myth:** You can only get dengue once.  \n"
                "**Fact:** There are four serotypes. A second infection with a different "
                "serotype carries a **higher** risk of severe disease."
            )

    if principal.can(Permission.SUBSCRIBE_ALERTS):
        st.divider()
        with st.expander("Get alerts for your district"):
            st.multiselect("Districts", sorted(frame["district"].unique()), key="alert_districts")
            st.checkbox("Weekly forecast summary", value=True, key="alert_weekly")
            st.checkbox("Outbreak warnings only", key="alert_outbreak")
            st.button("Save preferences", type="primary")
            st.caption(
                "This build stores preferences in the browser session only. Delivery "
                "would need an SMS or email gateway, which is not connected."
            )


# ==========================================================================
# Hospital portal
# ==========================================================================


def hospital_portal(principal: Principal, data: dict[str, pd.DataFrame], horizon: int) -> None:
    principal.require(Permission.VIEW_HOSPITAL_READINESS)

    readiness_all = data.get("hospital_readiness")
    if readiness_all is None or readiness_all.empty:
        st.warning("No readiness artifact. Run `make pipeline`.", icon="⚠️")
        return

    readiness = readiness_all[readiness_all["horizon_weeks"] == horizon]
    readiness = filter_to_scope(readiness, principal)

    st.subheader("Hospital readiness")
    st.caption(f"Scope: {principal.scope_label()} · {horizon} weeks ahead")

    st.warning(
        "**Every figure on this page is a planning estimate, not a measurement.** "
        "No public source publishes Sri Lankan hospital occupancy, ICU census, "
        "platelet stock or staffing. These numbers apply published clinical ratios "
        "to the case forecast — the same arithmetic a planner would do on paper. "
        "Adjust the ratios below to match your own case mix.",
        icon="📋",
    )

    totals = readiness.sum(numeric_only=True)
    kpi_grid(
        [
            kpi_html(
                "Projected admissions",
                _fmt(totals.get("admissions", 0)),
                f"{provenance_badge(ProvenanceTier.ASSUMED)} next {horizon} weeks",
            ),
            kpi_html(
                "ICU patients",
                _fmt(totals.get("icu_patients", 0), 1),
                f"{provenance_badge(ProvenanceTier.ASSUMED)} concurrent",
                "critical",
            ),
            kpi_html(
                "Peak occupied beds",
                _fmt(totals.get("peak_occupied_beds", 0)),
                f"{provenance_badge(ProvenanceTier.ASSUMED)} dengue beds",
            ),
            kpi_html(
                "Platelet units",
                _fmt(totals.get("platelet_units", 0)),
                f"{provenance_badge(ProvenanceTier.ASSUMED)} projected demand",
            ),
            kpi_html(
                "Additional nurses",
                _fmt(totals.get("additional_nurses", 0)),
                f"{provenance_badge(ProvenanceTier.ASSUMED)} at 1:4 ratio",
            ),
        ]
    )

    tab_load, tab_supply, tab_map, tab_ratios = st.tabs(
        ["Projected load", "Supplies", "Facility map", "Planning ratios"]
    )

    with tab_load:
        show = readiness[
            [
                "district",
                "forecast_cases",
                "admissions",
                "severe_cases",
                "icu_patients",
                "paediatric_admissions",
                "peak_occupied_beds",
                "occupancy_pct",
                "capacity_status",
            ]
        ].copy()
        st.dataframe(
            show.rename(
                columns={
                    "district": "District",
                    "forecast_cases": "Forecast cases",
                    "admissions": "Admissions",
                    "severe_cases": "Severe",
                    "icu_patients": "ICU",
                    "paediatric_admissions": "Paediatric",
                    "peak_occupied_beds": "Peak beds",
                    "occupancy_pct": "Occupancy %",
                    "capacity_status": "Status",
                }
            ),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Forecast cases": st.column_config.NumberColumn(format="%.0f"),
                "Admissions": st.column_config.NumberColumn(format="%.0f"),
                "Severe": st.column_config.NumberColumn(format="%.1f"),
                "ICU": st.column_config.NumberColumn(format="%.1f"),
                "Paediatric": st.column_config.NumberColumn(format="%.0f"),
                "Peak beds": st.column_config.NumberColumn(format="%.0f"),
                "Occupancy %": st.column_config.ProgressColumn(
                    format="%.1f%%", min_value=0, max_value=100
                ),
            },
        )
        estimate_notice(
            "55% hospitalisation rate, 6% severe, 2% ICU, 4-day mean stay. "
            "Occupancy is against district beds estimated from World Bank national "
            "bed density, assuming 15% are available for dengue."
        )

    with tab_supply:
        supply = readiness[["district", "platelet_units", "iv_fluid_litres", "diagnostic_tests"]]
        st.dataframe(
            supply.rename(
                columns={
                    "district": "District",
                    "platelet_units": "Platelet units",
                    "iv_fluid_litres": "IV fluid (L)",
                    "diagnostic_tests": "Diagnostic kits",
                }
            ),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Platelet units": st.column_config.NumberColumn(format="%.0f"),
                "IV fluid (L)": st.column_config.NumberColumn(format="%.0f"),
                "Diagnostic kits": st.column_config.NumberColumn(format="%.0f"),
            },
        )
        st.info(
            unavailable_reason("Current stock on hand"),
            icon="🔌",
        )

    with tab_map:
        facilities = data.get("health_facilities")
        chart = choropleth(
            readiness,
            value_column="occupancy_pct",
            tooltip_columns=[
                ("occupancy_pct", "Occupancy %", ".1f"),
                ("admissions", "Admissions", ".0f"),
            ],
            legend_title="Projected occupancy %",
        )
        if chart is not None:
            st.altair_chart(chart, use_container_width=True)
        if facilities is not None and not facilities.empty:
            st.markdown(f"**{len(facilities):,} health facilities** (OpenStreetMap, ODbL)")
            fmap = facility_map(facilities)
            if fmap is not None:
                st.altair_chart(fmap, use_container_width=True)
            st.caption(
                "Locations are real. Bed counts are **not** in OpenStreetMap for Sri "
                f"Lanka ({int(facilities['beds_tagged'].notna().sum())} of "
                f"{len(facilities):,} facilities tagged), so per-facility capacity "
                "cannot be shown."
            )

    with tab_ratios:
        st.markdown(
            "These are the assumptions behind every number on this page. They are "
            "**planning values from the literature for endemic settings**, not Sri "
            "Lankan measurements. Change them to match your own case mix."
        )
        from dengue.platform.hospital import ClinicalRatios

        defaults = ClinicalRatios()
        c1, c2, c3 = st.columns(3)
        with c1:
            st.slider(
                "Hospitalisation rate",
                0.1,
                1.0,
                defaults.hospitalisation_rate,
                0.05,
                key="ratio_hosp",
            )
            st.slider(
                "Severe fraction",
                0.01,
                0.25,
                defaults.severe_fraction_of_admitted,
                0.01,
                key="ratio_sev",
            )
        with c2:
            st.slider(
                "ICU fraction",
                0.001,
                0.10,
                defaults.icu_fraction_of_admitted,
                0.005,
                key="ratio_icu",
            )
            st.slider(
                "Mean stay (days)",
                1.0,
                10.0,
                defaults.mean_length_of_stay_days,
                0.5,
                key="ratio_los",
            )
        with c3:
            st.slider(
                "Platelet units / severe case",
                0.0,
                12.0,
                defaults.platelet_units_per_severe_case,
                0.5,
                key="ratio_plt",
            )
            st.slider(
                "Nurses per occupied bed",
                0.05,
                0.60,
                defaults.nurses_per_occupied_bed,
                0.05,
                key="ratio_nurse",
            )
        st.caption(
            "Changing these here does not rewrite the cached artifact — the pipeline "
            "computes the table. Wiring these controls through to a re-run is "
            "deliberate future work, not an oversight: it would mean computing at "
            "request time."
        )


# ==========================================================================
# MOH portal
# ==========================================================================


def moh_portal(principal: Principal, data: dict[str, pd.DataFrame], horizon: int) -> None:
    principal.require(Permission.VIEW_DISTRICT_OPERATIONS)

    district_risk = data["district_risk"]
    frame = filter_to_scope(_risk_frame(district_risk, horizon), principal)
    sweep = data.get("allocation_sweep")
    scenarios = data.get("scenarios")

    st.subheader("District operations")
    st.caption(f"Scope: {principal.scope_label()} · {horizon} weeks ahead")

    assessments = [
        a
        for a in assess_all(district_risk, horizon_weeks=horizon, audience="moh")
        if principal.may_see_district(a.district_id)
    ]

    tab_ops, tab_teams, tab_plan, tab_scenario, tab_budget = st.tabs(
        ["Hotspots", "Team deployment", "Intervention plan", "Scenarios", "Budget"]
    )

    with tab_ops:
        chart = choropleth(
            frame,
            value_column="risk_level",
            categorical=True,
            tooltip_columns=[
                ("q0.5", "Forecast cases", ".0f"),
                ("incidence_per_100k", "Per 100,000", ".1f"),
            ],
            legend_title="Risk level",
        )
        if chart is not None:
            st.altair_chart(chart, use_container_width=True)

        for a in assessments[:3]:
            with st.container(border=True):
                c1, c2 = st.columns([1, 3])
                with c1:
                    st.markdown(risk_pill(a.risk_level), unsafe_allow_html=True)
                    st.markdown(f"**{a.district_name}**")
                    st.caption(
                        f"{_fmt(a.forecast_median)} cases · {a.incidence_per_100k:.1f}/100k · "
                        f"{a.change_pct:+.0f}%"
                    )
                with c2:
                    recommendation_list(a.recommendations, limit=3)

    with tab_teams:
        if sweep is None or sweep.empty:
            st.info("No allocation artifact. Run `make pipeline`.", icon="ℹ️")
        else:
            budgets = sorted(sweep["budget"].unique().tolist())
            c1, c2 = st.columns([2, 1])
            with c1:
                budget = st.select_slider(
                    "Weekly team-week budget", budgets, value=budgets[len(budgets) // 2]
                )
            with c2:
                posture = st.radio(
                    "Posture",
                    [0.5, 0.9],
                    horizontal=True,
                    format_func=lambda q: "Median" if q == 0.5 else "Risk-averse",
                )

            plan = sweep[
                (sweep["budget"] == budget)
                & (sweep["risk_quantile"] == posture)
                & (sweep["strategy"] == "ilp")
            ].copy()
            plan = filter_to_scope(plan, principal)
            plan["district"] = plan["district_id"].map(DISTRICT_NAMES)
            plan = plan[plan["team_weeks"] > 0].sort_values("team_weeks", ascending=False)

            st.caption(
                "Precomputed by `make pipeline` — the slider indexes cached solutions "
                "rather than re-solving the program."
            )
            if plan.empty:
                st.info("No teams allocated to your districts at this budget.", icon="ℹ️")
            else:
                st.altair_chart(
                    alt.Chart(plan)
                    .mark_bar(cornerRadiusEnd=4, color=CATEGORICAL[0])
                    .encode(
                        y=alt.Y("district:N", sort="-x", title=None),
                        x=alt.X("team_weeks:Q", title="Team-weeks"),
                        tooltip=["district:N", "team_weeks:Q"],
                    )
                    .properties(height=max(200, 30 * len(plan))),
                    use_container_width=True,
                )

    with tab_plan:
        if sweep is None or sweep.empty:
            st.info("Run `make pipeline` to generate a deployment plan.", icon="ℹ️")
        else:
            st.markdown("**Weekly intervention schedule**")
            st.caption(
                "Derived from the Stage 3 allocation: districts with more team-weeks "
                "get more activity days. Activity types are ordered by how far ahead "
                "of the peak they act — source reduction first, spraying last."
            )
            budgets = sorted(sweep["budget"].unique().tolist())
            plan = sweep[
                (sweep["budget"] == budgets[len(budgets) // 2])
                & (sweep["risk_quantile"] == 0.5)
                & (sweep["strategy"] == "ilp")
            ]
            plan = filter_to_scope(plan, principal)
            plan = plan[plan["team_weeks"] > 0].sort_values("team_weeks", ascending=False)

            activities = [
                "Source reduction",
                "House inspection",
                "School inspection",
                "Community clean-up",
                "Space spraying",
            ]
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            rows = []
            for i, row in enumerate(plan.itertuples(index=False)):
                name = DISTRICT_NAMES.get(row.district_id, row.district_id)
                for d, day in enumerate(days[: min(int(row.team_weeks), 5)]):
                    rows.append(
                        {
                            "Day": day,
                            "District": name,
                            "Activity": activities[(i + d) % len(activities)],
                            "Teams": max(1, int(row.team_weeks) // 5),
                        }
                    )
            if rows:
                st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            else:
                st.info("No activity scheduled for your districts at this budget.", icon="ℹ️")

    with tab_scenario:
        principal.require(Permission.RUN_SCENARIO)
        if scenarios is None or scenarios.empty:
            st.info(
                "No scenario artifact. Scenarios are precomputed by `make pipeline` "
                "when Stage 2 runs (they are ODE integrations, so they are not run "
                "at request time).",
                icon="ℹ️",
            )
        else:
            visible = filter_to_scope(scenarios, principal)
            if visible.empty:
                st.info("No scenarios cached for your districts.", icon="ℹ️")
            else:
                names = sorted(visible["district"].unique())
                chosen = st.selectbox("District", names)
                subset = visible[visible["district"] == chosen].copy()
                subset = subset.sort_values("change_pct", ascending=False)

                st.altair_chart(
                    alt.Chart(subset[subset["scenario_key"] != "baseline"])
                    .mark_bar(cornerRadiusEnd=4)
                    .encode(
                        y=alt.Y("scenario:N", sort="-x", title=None),
                        x=alt.X("change_pct:Q", title="Change in cases vs baseline (%)"),
                        color=alt.condition(
                            alt.datum.change_pct > 0,
                            alt.value("#d03b3b"),
                            alt.value("#0ca30c"),
                        ),
                        tooltip=[
                            alt.Tooltip("scenario:N", title="Scenario"),
                            alt.Tooltip("change_pct:Q", title="Change %", format="+.1f"),
                            alt.Tooltip("total_cases:Q", title="Cases", format=".0f"),
                        ],
                    )
                    .properties(height=280),
                    use_container_width=True,
                )
                st.caption(
                    "Each scenario re-integrates the fitted SEI-SIR model with a "
                    "perturbed input — it is not a lookup table. That is why heavy "
                    "rain plus a heatwave is worse than the sum of the two: more "
                    "mosquitoes and a shorter incubation period multiply."
                )
                for row in subset.itertuples(index=False):
                    if row.scenario_key == "baseline":
                        continue
                    st.markdown(f"**{row.scenario}** — {row.change_pct:+.0f}%")
                    st.caption(row.description)

    with tab_budget:
        principal.require(Permission.VIEW_BUDGET_OPTIMISER)
        budget_data = data.get("budget_sweep")
        if budget_data is None or budget_data.empty:
            st.info("No budget artifact. Run `make pipeline`.", icon="ℹ️")
        else:
            envelopes = sorted(budget_data["budget_lkr"].unique().tolist())
            envelope = st.select_slider(
                "Annual envelope (LKR)",
                envelopes,
                value=envelopes[min(3, len(envelopes) - 1)],
                format_func=lambda v: f"LKR {v / 1e6:.0f}M",
            )
            split = budget_data[budget_data["budget_lkr"] == envelope]

            c1, c2 = st.columns([1, 1])
            with c1:
                st.altair_chart(
                    alt.Chart(split)
                    .mark_arc(innerRadius=60, stroke="#fcfcfb", strokeWidth=2)
                    .encode(
                        theta=alt.Theta("amount_lkr:Q"),
                        color=alt.Color(
                            "category:N",
                            scale=alt.Scale(range=list(CATEGORICAL)),
                            legend=alt.Legend(title=None, orient="bottom"),
                        ),
                        tooltip=[
                            alt.Tooltip("category:N", title="Category"),
                            alt.Tooltip("share_pct:Q", title="Share", format=".1f"),
                            alt.Tooltip("amount_lkr:Q", title="LKR", format=",.0f"),
                        ],
                    )
                    .properties(height=300),
                    use_container_width=True,
                )
            with c2:
                st.dataframe(
                    split[["category", "share_pct", "amount_lkr", "evidence"]].rename(
                        columns={
                            "category": "Category",
                            "share_pct": "Share %",
                            "amount_lkr": "Amount (LKR)",
                            "evidence": "Evidence",
                        }
                    ),
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Share %": st.column_config.NumberColumn(format="%.1f%%"),
                        "Amount (LKR)": st.column_config.NumberColumn(format="%.0f"),
                    },
                )
            st.warning(
                "**Only the vector-control curve is anchored to a model.** The other "
                "three categories use assumed cost-effectiveness elasticities, not "
                "measured Sri Lankan data. Read this as a structured argument about "
                "trade-offs, not as an evidence-based funding instruction.",
                icon="⚠️",
            )


# ==========================================================================
# Admin portal
# ==========================================================================


def admin_portal(principal: Principal, data: dict[str, pd.DataFrame], horizon: int) -> None:
    principal.require(Permission.VIEW_NATIONAL_OPERATIONS)

    meta = data.get("pipeline_meta")
    scores = data.get("scores")

    st.subheader("System administration")
    st.caption("Nationwide oversight, configuration, and provenance.")

    tab_health, tab_data, tab_models, tab_users, tab_audit = st.tabs(
        ["System health", "Data sources", "Models", "Users & roles", "Audit log"]
    )

    with tab_health:
        if meta is not None and not meta.empty:
            row = meta.iloc[0]
            kpi_grid(
                [
                    kpi_html(
                        "Last pipeline run",
                        str(row["generated_at"])[:16].replace("T", " "),
                        f"{row['runtime_seconds']}s",
                    ),
                    kpi_html(
                        "Panel source",
                        str(row["panel_source"]).upper(),
                        "SIMULATED DATA" if row["is_synthetic"] else "Real sources",
                        "critical" if row["is_synthetic"] else "accent",
                    ),
                    kpi_html("Districts", str(row["n_districts"]), "of 25"),
                    kpi_html(
                        "Forecast model", str(row["forecast_model"]), str(row["forecast_origin"])
                    ),
                ]
            )
        st.markdown("**Artifact status**")
        expected = [
            "panel_recent",
            "forecasts",
            "district_risk",
            "effect_table",
            "allocation_sweep",
            "allocation_summary",
            "sei_sir_params",
            "hospital_readiness",
            "district_capacity",
            "health_facilities",
            "scenarios",
            "budget_sweep",
            "scores",
        ]
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Artifact": name,
                        "Present": name in data and data[name] is not None,
                        "Rows": len(data[name]) if name in data and data[name] is not None else 0,
                    }
                    for name in expected
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )

    with tab_data:
        st.markdown("**Every source, with its licence and what it actually covers.**")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Source": v["name"],
                        "Tier": ProvenanceTier(v["tier"]).label,
                        "Licence": v["licence"],
                        "Covers": v["covers"],
                        "URL": v["url"],
                    }
                    for v in SOURCE_REGISTRY.values()
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )
        st.info(
            "The **Planning estimate** tier is the one to watch. Those numbers apply "
            "published parameters to model output — they are not measured for Sri "
            "Lanka, and the platform labels them wherever they appear.",
            icon="🏷️",
        )

    with tab_models:
        if scores is not None and not scores.empty:
            st.markdown("**Backtest performance**")
            headline = scores[
                scores["metric"].isin(
                    ["pinball_mean", "mae", "coverage_80", "mean_lead_time_weeks"]
                )
            ]
            st.dataframe(
                headline.pivot_table(
                    index=["model", "horizon"], columns="metric", values="value", observed=True
                ).reset_index(),
                hide_index=True,
                use_container_width=True,
            )
        st.markdown("**Configuration**")
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox(
                "Production forecast model",
                ["lgbm_quantile", "sarima", "seasonal_naive"],
                key="cfg_model",
            )
            st.multiselect("Horizons (weeks)", [1, 2, 3, 4, 6, 8], default=[2, 3, 4], key="cfg_h")
        with c2:
            st.slider("Retrain cadence (weeks)", 1, 12, 4, key="cfg_retrain")
            st.slider("High-risk districts designated", 3, 12, 6, key="cfg_topk")
        st.button("Trigger retrain", type="primary", disabled=True)
        st.caption(
            "Retraining is a `make pipeline` run, not a button in this build — "
            "wiring it here would mean the dashboard computes at request time."
        )

    with tab_users:
        from dengue.platform.rbac import ROLE_PERMISSIONS, Role

        st.markdown("**Roles and permissions**")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Role": r.label,
                        "Permissions": len(ROLE_PERMISSIONS[r]),
                        "Scope": "Nationwide" if r is Role.NATIONAL_ADMIN else "District-scoped",
                        "Description": r.description,
                    }
                    for r in Role
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )
        with st.expander("Full permission matrix"):
            rows = []
            for perm in sorted(
                {p for ps in ROLE_PERMISSIONS.values() for p in ps}, key=lambda p: p.value
            ):
                entry = {"Permission": perm.value}
                for r in Role:
                    entry[r.label] = "✓" if perm in ROLE_PERMISSIONS[r] else ""
                rows.append(entry)
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        st.info(
            "**No authentication backend is connected.** The role switcher in the "
            "sidebar is a demonstration of the access model, not a login. Production "
            "deployment needs an identity provider and server-side enforcement — "
            "client-side role selection is not a security control.",
            icon="🔐",
        )

    with tab_audit:
        st.info(
            unavailable_reason("Audit log"),
            icon="🔌",
        )
        st.caption(
            "An audit log records real user actions. With no authentication and no "
            "action-recording backend, any table here would be fabricated, so none "
            "is shown."
        )
