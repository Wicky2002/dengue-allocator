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
    CAPACITY_COLOURS,
    choropleth,
    estimate_notice,
    facility_map,
    history_and_forecast_chart,
    kpi_grid,
    provenance_badge,
    rainfall_cases_overlay,
    rainfall_vs_cases,
    recommendation_list,
    risk_pill,
    trend_chart,
)
from theme import CATEGORICAL, PAGE, kpi_html

from dengue import config
from dengue.platform.alerts import AlertError, save_subscription
from dengue.platform.hospital import ClinicalRatios
from dengue.platform.provenance import SOURCE_REGISTRY, ProvenanceTier, unavailable_reason
from dengue.platform.rbac import Permission, Principal, Role, filter_to_scope
from dengue.platform.risk import (
    RISK_THRESHOLDS,
    RiskLevel,
    assess_all,
    classify,
    national_summary,
)

DISTRICT_NAMES = {d.district_id: d.name for d in config.DISTRICTS}

#: session_state keys for the hospital-portal ratio sliders -> their default
#: value, used both to seed the sliders and to reset them in one click. Kept
#: in sync with ClinicalRatios' own defaults rather than restated as literals.
_HOSPITAL_DEFAULTS = ClinicalRatios()
_RATIO_DEFAULTS = {
    "ratio_hosp": _HOSPITAL_DEFAULTS.hospitalisation_rate,
    "ratio_sev": _HOSPITAL_DEFAULTS.severe_fraction_of_admitted,
    "ratio_icu": _HOSPITAL_DEFAULTS.icu_fraction_of_admitted,
    "ratio_los": _HOSPITAL_DEFAULTS.mean_length_of_stay_days,
    "ratio_plt": _HOSPITAL_DEFAULTS.platelet_units_per_severe_case,
    "ratio_nurse": _HOSPITAL_DEFAULTS.nurses_per_occupied_bed,
}


def _fmt(value: float, digits: int = 0) -> str:
    return "—" if pd.isna(value) else f"{value:,.{digits}f}"


def _first_selected_value(payload: object, field: str) -> str | None:
    """Pull the first value of ``field`` out of a Vega-Lite point-selection payload.

    Streamlit's chart-selection events aren't documented down to the exact
    shape (column-oriented ``{"field": [...]}`` vs. row-oriented
    ``[{"field": ...}, ...]`` both appear in the wild depending on Vega-Lite
    version), so this accepts either rather than assuming one and raising on
    the other. For a dotted ``field`` like ``"properties.district_id"`` it
    also tries the bare trailing segment (``"district_id"``) and the
    backslash-escaped literal Vega-Lite actually emits for a selection
    ``fields`` entry containing a dot (``"properties\\.district_id"``,
    confirmed by inspecting a live click payload) -- this project's own
    choropleth code has already hit one real bug (:func:`components._safe_field`)
    from a dotted field name silently breaking somewhere in this exact
    pipeline, so a nested selection field is exactly the case not to assume
    about.
    """
    if not payload:
        return None
    candidates = [field]
    if "." in field:
        candidates.append(field.rsplit(".", 1)[-1])
        candidates.append(field.replace(".", "\\."))

    if isinstance(payload, list):
        if payload and isinstance(payload[0], dict):
            row = payload[0]
            for key in candidates:
                if key in row:
                    return row[key]
        return None
    if isinstance(payload, dict):
        for key in candidates:
            values = payload.get(key)
            if isinstance(values, list) and values:
                return values[0]
            if isinstance(values, str):
                return values
    return None


def _risk_choropleth(
    frame: pd.DataFrame, *, enable_click: bool = False, highlight_column: str | None = None
) -> alt.Chart | None:
    """The district risk-level choropleth, shared by the National overview and
    the MOH portal's Hotspots tab -- identical encoding, different data scope,
    so this is the one place to change if either needs to."""
    return choropleth(
        frame,
        value_column="risk_level",
        categorical=True,
        tooltip_columns=[
            ("q0.5", "Forecast cases", ".0f"),
            ("incidence_per_100k", "Per 100,000/week", ".1f"),
        ],
        legend_title="Risk level",
        enable_click=enable_click,
        highlight_column=highlight_column,
    )


def _risk_frame(district_risk: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Attach risk bands to the district-risk frame for one horizon."""
    frame = district_risk[district_risk["horizon"] == horizon].copy()
    frame["risk_level"] = frame["incidence_per_100k"].apply(lambda v: classify(float(v or 0)).value)
    frame["district"] = frame["district_id"].map(DISTRICT_NAMES).fillna(frame["district_id"])
    return frame


# ==========================================================================
# National overview -- identical for every role, shown before role content
# ==========================================================================


def national_overview(data: dict[str, pd.DataFrame], horizon: int) -> None:
    """Whole-country picture: heat map, forecast, and trends.

    No ``Principal`` argument and no permission check -- deliberately, since
    this is meant to render exactly the same way no matter who is viewing.
    That is the direct fix for "data looks restricted to part of the
    country": every role sees all 25 districts here, before anything
    role-scoped (a hospital's own facility, an MOH officer's own district)
    might narrow the view further down the page.

    The ranked bar chart next to the map is not a fallback shown only when
    the map fails -- it is always rendered alongside it, so "every district,
    always visible" holds even if a future map regression slips through, and
    so a viewer who prefers a list to a map isn't stuck.
    """
    district_risk = data.get("district_risk")
    if district_risk is None or district_risk.empty:
        st.info("No forecast data available yet. Run `make pipeline`.", icon="ℹ️")
        return

    panel = data.get("panel_recent")
    forecasts = data.get("forecasts")
    frame = _risk_frame(district_risk, horizon)
    assessments = assess_all(district_risk, horizon_weeks=horizon, audience="public")
    summary = national_summary(assessments)

    st.markdown("## National overview")
    st.caption(f"All {summary['n_districts']} districts, {horizon} weeks ahead")

    kpi_grid(
        [
            kpi_html("Districts forecast", str(summary["n_districts"]), "of 25"),
            kpi_html(
                "High risk or above",
                str(summary["n_severe"] + summary["n_high"]),
                "districts",
                "critical",
            ),
            kpi_html(
                "Forecast cases",
                _fmt(summary["total_forecast_cases"]),
                f"Nationwide, {horizon} weeks ahead",
            ),
            kpi_html("Highest risk", summary["worst_district"], summary["worst_level"]),
        ]
    )

    # Both the map and the ranked bars below highlight off this one column
    # rather than each tracking its own click state -- two separate
    # st.altair_chart components each have an independent client-side
    # selection and cannot see each other's, so the only way to keep "click
    # the map" and "click a bar" visually in sync is to have both read the
    # same session_state-derived truth on every rerun.
    remembered = st.session_state.get("selected_district")
    frame = frame.copy()
    frame["is_selected"] = (frame["district"] == remembered) if remembered else True

    map_col, rank_col = st.columns([3, 2])
    with map_col:
        st.markdown("**Risk map**")
        st.caption("Click a district to jump to it in the Public portal's district lookup.")
        chart = _risk_choropleth(frame, enable_click=True, highlight_column="is_selected")
        if chart is None:
            st.info("Map geometry unavailable — see the ranked list.", icon="🗺️")
        else:
            # No use_container_width -- geoshape needs a fixed pixel extent.
            event = st.altair_chart(chart, on_select="rerun", key="national_risk_map")
            clicked_id = _first_selected_value(
                event.selection.get("district_click") if event and event.selection else None,
                "properties.district_id",
            )
            if clicked_id:
                clicked_name = DISTRICT_NAMES.get(clicked_id)
                # `is_selected` above was already computed from the *previous*
                # session_state value, so without an explicit rerun here the
                # bars beside the map wouldn't pick up this click until some
                # unrelated later interaction forced another pass -- the two
                # charts would look out of sync for exactly one click.
                if clicked_name and clicked_name != remembered:
                    st.session_state["selected_district"] = clicked_name
                    st.rerun()

        cols = st.columns(4)
        for col, level in zip(cols, RiskLevel, strict=False):
            col.markdown(risk_pill(level), unsafe_allow_html=True)
            col.caption(f"Above {RISK_THRESHOLDS[level]:g} per 100,000 per week")

    with rank_col:
        st.markdown("**Every district, ranked**")
        ranked = frame.sort_values("incidence_per_100k", ascending=False)
        colours = {level.value: level.colour for level in RiskLevel}
        # This click param only captures the event (on_select="rerun" needs at
        # least one param to fire on); the opacity below is driven by
        # `is_selected`, the same shared column the map uses, not by `click`
        # directly -- that's what keeps the two charts in sync.
        click = alt.selection_point(name="district_pick", fields=["district"], empty=False)
        bars = (
            alt.Chart(ranked)
            .mark_bar(cornerRadiusEnd=3)
            .encode(
                y=alt.Y("district:N", sort="-x", title=None),
                x=alt.X("incidence_per_100k:Q", title="Per 100,000/week"),
                color=alt.Color(
                    "risk_level:N",
                    scale=alt.Scale(domain=list(colours), range=list(colours.values())),
                    legend=None,
                ),
                opacity=alt.condition("datum.is_selected", alt.value(1.0), alt.value(0.55)),
                tooltip=[
                    alt.Tooltip("district:N", title="District"),
                    alt.Tooltip("incidence_per_100k:Q", title="Per 100,000/week", format=".1f"),
                    alt.Tooltip("risk_level:N", title="Risk"),
                ],
            )
            .add_params(click)
            .properties(height=560)
        )
        event = st.altair_chart(
            bars, width="stretch", on_select="rerun", key="national_ranked_bars"
        )
        picked = _first_selected_value(
            event.selection.get("district_pick") if event and event.selection else None,
            "district",
        )
        if picked and picked != remembered:
            st.session_state["selected_district"] = picked
            st.rerun()

    has_observed_history = (
        panel is not None and not panel.empty and "population" in panel.columns
    )
    predictions_history = data.get("predictions_history")
    at_horizon = (
        predictions_history[predictions_history["horizon"] == horizon]
        if predictions_history is not None and not predictions_history.empty
        else None
    )
    has_predicted_history = at_horizon is not None and not at_horizon.empty

    if has_observed_history:
        st.markdown("**View a past week**")
        history = panel.copy()
        history["incidence_per_100k"] = history["cases"] / history["population"] * 100_000.0
        history["risk_level"] = history["incidence_per_100k"].apply(
            lambda v: classify(float(v or 0)).value
        )
        weeks = sorted(history["iso_week"].dropna().unique())
        if weeks:
            # One slider drives both maps below -- it names a single week,
            # and each column answers a different question about it ("what
            # happened" vs. "what the model, looking only at earlier data,
            # thought would happen"). A second, separately-scrubbed slider
            # for the prediction made the two maps hard to compare, since
            # they were then usually showing two different weeks.
            default_week = weeks[-1]
            if has_predicted_history:
                targets = sorted(at_horizon["target_week"].dropna().unique())
                if targets:
                    default_week = targets[-1]
            chosen_week = st.select_slider(
                "Week",
                weeks,
                value=default_week,
                format_func=lambda w: pd.Timestamp(w).strftime("%d %b %Y"),
                key="history_week",
                label_visibility="collapsed",
            )

            observed_col, predicted_col = st.columns(2)

            with observed_col:
                st.caption("Observed")
                week_frame = history[history["iso_week"] == chosen_week]
                past_chart = choropleth(
                    week_frame,
                    value_column="risk_level",
                    categorical=True,
                    tooltip_columns=[
                        ("cases", "Cases", ".0f"),
                        ("incidence_per_100k", "Per 100,000/week", ".1f"),
                    ],
                    legend_title="Risk level",
                    # Half-width column, next to the predicted map -- the
                    # default 620px would overflow it.
                    width=440,
                    height=380,
                )
                if past_chart is None:
                    st.info("Map geometry unavailable.", icon="🗺️")
                else:
                    # A key that varies with the selected week -- otherwise
                    # Streamlit reuses this element's prior client-side
                    # state across weeks the same way the current-week map's
                    # own click selection is deliberately shared (see the
                    # comment above `remembered`), which here would be the
                    # opposite of what's wanted: each week's map must stand
                    # on its own.
                    st.altair_chart(past_chart, key=f"history_map_{chosen_week}")
                if not week_frame.empty:
                    worst = week_frame.sort_values("incidence_per_100k", ascending=False).iloc[0]
                    kpi_grid(
                        [
                            kpi_html(
                                "Cases that week",
                                _fmt(week_frame["cases"].sum()),
                                "Nationwide, observed",
                            ),
                            kpi_html(
                                "Highest risk that week",
                                DISTRICT_NAMES.get(worst["district_id"], worst["district_id"]),
                                classify(float(worst["incidence_per_100k"] or 0)).label,
                            ),
                        ]
                    )
                else:
                    st.info("No observed data for this week.", icon="🗓️")

            with predicted_col:
                st.caption(f"Predicted, {horizon}w ahead")
                # Bounded to a fixed 2026 Jun-Aug window on purpose -- see
                # dengue.eval.history's module docstring. `chosen_week` here
                # is the *target* week (what the map shows), not the origin
                # the model was standing at when it made the call.
                pred_frame = (
                    at_horizon[at_horizon["target_week"] == chosen_week].copy()
                    if has_predicted_history
                    else pd.DataFrame()
                )
                if pred_frame.empty:
                    st.info("No prediction for this week at the current horizon.", icon="🗓️")
                else:
                    pred_frame["risk_level"] = pred_frame["predicted_incidence_per_100k"].apply(
                        lambda v: classify(float(v or 0)).value
                    )
                    pred_chart = choropleth(
                        pred_frame,
                        value_column="risk_level",
                        categorical=True,
                        tooltip_columns=[
                            ("predicted_incidence_per_100k", "Predicted per 100,000/week", ".1f"),
                        ],
                        legend_title="Predicted risk level",
                        width=440,
                        height=380,
                    )
                    if pred_chart is None:
                        st.info("Map geometry unavailable.", icon="🗺️")
                    else:
                        st.altair_chart(
                            pred_chart, key=f"history_pred_map_{chosen_week}_{horizon}"
                        )
                    pred_worst = pred_frame.sort_values(
                        "predicted_incidence_per_100k", ascending=False
                    ).iloc[0]
                    kpi_grid(
                        [
                            kpi_html(
                                "Predicted cases",
                                _fmt(pred_frame["q0.5"].sum()),
                                "Nationwide, that week",
                            ),
                            kpi_html(
                                "Predicted highest risk",
                                DISTRICT_NAMES.get(
                                    pred_worst["district_id"], pred_worst["district_id"]
                                ),
                                classify(
                                    float(pred_worst["predicted_incidence_per_100k"] or 0)
                                ).label,
                            ),
                        ]
                    )

    st.divider()
    trend_col, rain_col = st.columns(2)
    with trend_col:
        st.markdown("**National cases: observed and forecast**")
        if panel is not None and not panel.empty and forecasts is not None and not forecasts.empty:
            national_history = panel.groupby("iso_week", observed=True)["cases"].sum().reset_index()
            national_forecast = (
                forecasts.groupby("target_week", observed=True)[["q0.5", "q0.1", "q0.9"]]
                .sum()
                .reset_index()
            )
            st.altair_chart(
                history_and_forecast_chart(national_history, national_forecast),
                width="stretch",
            )
            st.caption("Solid = observed. Dashed = forecast, summed across districts.")
        else:
            st.info("Not enough data for a trend chart yet.", icon="ℹ️")

    national = None
    with rain_col:
        st.markdown("**Rainfall and dengue cases**")
        if panel is not None and not panel.empty:
            national = (
                panel.groupby("iso_week", observed=True)
                .agg(cases=("cases", "sum"), rain_mm=("rain_mm", "mean"))
                .reset_index()
            )
            st.altair_chart(rainfall_vs_cases(national, height=280), width="stretch")
            st.caption(
                "Cases follow rainfall by roughly 6–8 weeks: rain fills containers, "
                "larvae develop, adult mosquitoes emerge, and only then does "
                "transmission rise."
            )

    if national is not None and not national.empty:
        st.markdown("**Rainfall and cases, overlaid**")
        st.altair_chart(rainfall_cases_overlay(national, height=260), width="stretch")


# ==========================================================================
# Public portal
# ==========================================================================


def public_portal(principal: Principal, data: dict[str, pd.DataFrame], horizon: int) -> None:
    principal.require(Permission.VIEW_PUBLIC_RISK)

    district_risk = data["district_risk"]
    panel = data.get("panel_recent")
    frame = _risk_frame(district_risk, horizon)

    assessments = assess_all(district_risk, horizon_weeks=horizon, audience="public")

    st.subheader("Your district")
    st.caption(
        "Look up a specific district, or check the National overview above for the "
        "whole-country picture."
    )

    tab_district, tab_learn = st.tabs(["My district", "Protect yourself"])

    with tab_district:
        names = sorted(frame["district"].unique())
        remembered = st.session_state.get("selected_district")
        default_name = (
            remembered if remembered in names else ("Colombo" if "Colombo" in names else names[0])
        )
        # Keying on the remembered district (rather than a fixed key) forces a
        # fresh widget -- and therefore a fresh `index` -- exactly when a click
        # on the National overview's ranked chart changes it. A fixed key
        # would make Streamlit keep whatever the user last picked manually and
        # ignore `index` on every subsequent rerun, which is the usual trap.
        chosen = st.selectbox(
            "Choose your district",
            names,
            index=names.index(default_name),
            key=f"district_select_{default_name}",
        )
        if remembered:
            st.caption(f"Jumped here from the National overview map: **{remembered}**.")

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
                    f"(80% interval) · {a.incidence_per_100k:.1f} per 100,000 per week"
                )
            with right:
                st.markdown("**What you should do**")
                recommendation_list(a.recommendations)

        if panel is not None and not panel.empty and match:
            history = panel[panel["district_id"] == match[0].district_id]
            if not history.empty:
                st.markdown("**Recent weekly cases**")
                st.altair_chart(trend_chart(history), width="stretch")

                st.markdown(f"**Rainfall and cases in {chosen}, overlaid**")
                st.altair_chart(rainfall_cases_overlay(history, height=240), width="stretch")
                st.caption(
                    "Both series normalised to their own 0–100 range so the "
                    "rain-to-cases lag is easy to see for this district specifically."
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
            email = st.text_input("Email", key="alert_email", placeholder="you@example.com")
            chosen_names = st.multiselect(
                "Districts", sorted(frame["district"].unique()), key="alert_districts"
            )
            weekly = st.checkbox("Weekly forecast summary", value=True, key="alert_weekly")
            outbreak = st.checkbox("Outbreak warnings only", key="alert_outbreak")
            if st.button("Save preferences", type="primary"):
                name_to_id = {v: k for k, v in DISTRICT_NAMES.items()}
                district_ids = [name_to_id[n] for n in chosen_names if n in name_to_id]
                try:
                    save_subscription(
                        email,
                        district_ids,
                        weekly_summary=weekly,
                        outbreak_only=outbreak,
                    )
                except AlertError as exc:
                    st.error(str(exc), icon="🔒")
                else:
                    st.success("Saved. You'll hear from us at the next weekly refresh.", icon="✅")
            st.caption(
                "Real subscriptions, stored for real (Supabase) -- sent by the same "
                "scheduled job that refreshes the data every week. No account needed; "
                "resubmit this form any time to change your preferences."
            )


# ==========================================================================
# Hospital portal
# ==========================================================================


def hospital_portal(principal: Principal, data: dict[str, pd.DataFrame], horizon: int) -> None:
    principal.require(Permission.VIEW_HOSPITAL_READINESS)

    district_risk = data.get("district_risk")
    capacity = data.get("district_capacity")
    if district_risk is None or district_risk.empty or capacity is None or capacity.empty:
        st.warning("No readiness artifact. Run `make pipeline`.", icon="⚠️")
        return

    from dengue.platform.hospital import build_readiness_table, with_ratio_overrides

    defaults = _HOSPITAL_DEFAULTS
    # Reading these from session_state (rather than the st.slider() calls
    # themselves, which live further down in tab_ratios) is what lets this
    # section render *before* the sliders in the tab order while still
    # reflecting whatever the user last set them to: Streamlit updates
    # session_state for an existing widget key before the script reruns, so
    # the value is already here by the time this line executes.
    try:
        live_ratios = with_ratio_overrides(
            defaults,
            hospitalisation_rate=st.session_state.get("ratio_hosp", defaults.hospitalisation_rate),
            severe_fraction_of_admitted=st.session_state.get(
                "ratio_sev", defaults.severe_fraction_of_admitted
            ),
            icu_fraction_of_admitted=st.session_state.get(
                "ratio_icu", defaults.icu_fraction_of_admitted
            ),
            mean_length_of_stay_days=st.session_state.get(
                "ratio_los", defaults.mean_length_of_stay_days
            ),
            platelet_units_per_severe_case=st.session_state.get(
                "ratio_plt", defaults.platelet_units_per_severe_case
            ),
            nurses_per_occupied_bed=st.session_state.get(
                "ratio_nurse", defaults.nurses_per_occupied_bed
            ),
        )
        ratio_error = None
    except ValueError as exc:
        live_ratios = defaults
        ratio_error = str(exc)
    is_customised = live_ratios != defaults

    # Cheap arithmetic over ~25 rows -- not a model refit or an ILP re-solve --
    # so recomputing this on every rerun does not violate the app's
    # no-compute-at-request-time rule the way retraining Stage 1 or
    # re-solving Stage 3 would.
    full_readiness = build_readiness_table(
        district_risk, capacity, horizon_weeks=horizon, ratios=live_ratios
    )
    readiness = filter_to_scope(full_readiness, principal)
    readiness = readiness.merge(
        capacity[["district_id", "n_facilities", "n_hospitals", "population"]],
        on="district_id",
        how="left",
    )
    readiness["facilities_per_100k"] = (
        readiness["n_facilities"] / readiness["population"] * 100_000.0
    )

    st.subheader("Hospital readiness")
    st.caption(f"Scope: {principal.scope_label()} · {horizon} weeks ahead")

    if principal.role is Role.HOSPITAL_STAFF:
        own_names = {DISTRICT_NAMES.get(d, d) for d in principal.districts}
        other_names = sorted(n for n in DISTRICT_NAMES.values() if n not in own_names)
        with st.expander("🔍 Preview another district"):
            st.caption("Preview only — does not change your account's access.")
            if other_names:
                preview_name = st.selectbox(
                    "District", other_names, key="hospital_preview_district"
                )
                name_to_id = {v: k for k, v in DISTRICT_NAMES.items()}
                preview_id = name_to_id[preview_name]
                preview_row = full_readiness[full_readiness["district_id"] == preview_id]
                preview_capacity = capacity[capacity["district_id"] == preview_id]

                if not preview_row.empty:
                    r = preview_row.iloc[0]
                    p1, p2, p3, p4 = st.columns(4)
                    p1.metric("Forecast cases", _fmt(r["forecast_cases"]))
                    p2.metric("Admissions", _fmt(r["admissions"]))
                    p3.metric("ICU patients", _fmt(r["icu_patients"], 1))
                    p4.metric("Occupancy", f"{r['occupancy_pct']:.0f}%")

                    n_hosp = (
                        int(preview_capacity["n_hospitals"].iloc[0])
                        if not preview_capacity.empty
                        else None
                    )
                    n_fac = (
                        int(preview_capacity["n_facilities"].iloc[0])
                        if not preview_capacity.empty
                        else None
                    )
                    status_label = str(r["capacity_status"]).replace("_", " ").title()
                    st.markdown(
                        f"**Status:** {status_label} &nbsp;·&nbsp; **Hospitals:** "
                        f"{n_hosp if n_hosp is not None else '—'} &nbsp;·&nbsp; "
                        f"**Facilities:** {n_fac if n_fac is not None else '—'}"
                    )

                map_col, facility_col = st.columns(2)
                with map_col:
                    highlight_frame = full_readiness.copy()
                    highlight_frame["is_previewed"] = (
                        highlight_frame["district_id"] == preview_id
                    )
                    preview_chart = choropleth(
                        highlight_frame,
                        value_column="capacity_status",
                        categorical=True,
                        colour_map=CAPACITY_COLOURS,
                        domain_order=list(CAPACITY_COLOURS),
                        highlight_column="is_previewed",
                        tooltip_columns=[
                            ("occupancy_pct", "Occupancy %", ".1f"),
                            ("admissions", "Admissions", ".0f"),
                        ],
                        legend_title="Capacity status",
                        height=320,
                        width=340,
                    )
                    if preview_chart is not None:
                        # No use_container_width -- geoshape needs a fixed pixel extent.
                        st.altair_chart(preview_chart)
                with facility_col:
                    all_facilities = data.get("health_facilities")
                    if all_facilities is not None and not all_facilities.empty:
                        preview_facilities = all_facilities[
                            all_facilities["district_id"] == preview_id
                        ]
                        if not preview_facilities.empty:
                            preview_fmap = facility_map(
                                preview_facilities, height=320, width=340
                            )
                            if preview_fmap is not None:
                                st.altair_chart(preview_fmap)
                            st.caption(f"{len(preview_facilities):,} OSM facilities shown.")
                        else:
                            st.caption("No OpenStreetMap facilities recorded for this district.")
            else:
                st.caption("Your account already covers every district.")

    if ratio_error:
        st.error(
            f"**Ratio combination is invalid** — {ratio_error} Showing the default "
            "ratios below instead; adjust the sliders in **Planning ratios**.",
            icon="⚠️",
        )
    st.warning(
        "**Every figure on this page is a planning estimate, not a measurement.** "
        "No public source publishes Sri Lankan hospital occupancy, ICU census, "
        "platelet stock or staffing. These numbers apply published clinical ratios "
        "to the case forecast — the same arithmetic a planner would do on paper. "
        + (
            "Recomputed live from the ratios you set in **Planning ratios**."
            if is_customised
            else "Adjust the ratios in **Planning ratios** to match your own case mix."
        ),
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
                f"{provenance_badge(ProvenanceTier.ASSUMED)} at "
                f"1:{round(1 / live_ratios.nurses_per_occupied_bed)} ratio",
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
                "n_hospitals",
                "facilities_per_100k",
            ]
        ].copy()
        # Pre-formatted as display strings rather than via st.column_config:
        # every column_config-bearing dataframe in this app crashed the
        # frontend outright (a JS TypeError reading 'vertical', reproducible
        # in a real browser though invisible to any Python-side test) on this
        # Streamlit version, while plain dataframes never did. Formatting the
        # numbers ourselves sidesteps that component entirely rather than
        # chasing the exact trigger under deadline pressure.
        show["forecast_cases"] = show["forecast_cases"].map("{:.0f}".format)
        show["admissions"] = show["admissions"].map("{:.0f}".format)
        show["severe_cases"] = show["severe_cases"].map("{:.1f}".format)
        show["icu_patients"] = show["icu_patients"].map("{:.1f}".format)
        show["paediatric_admissions"] = show["paediatric_admissions"].map("{:.0f}".format)
        show["peak_occupied_beds"] = show["peak_occupied_beds"].map("{:.0f}".format)
        show["occupancy_pct"] = show["occupancy_pct"].map("{:.1f}%".format)
        show["n_hospitals"] = show["n_hospitals"].map("{:.0f}".format)
        show["facilities_per_100k"] = show["facilities_per_100k"].map("{:.1f}".format)
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
                    "n_hospitals": "Hospitals",
                    "facilities_per_100k": "Facilities/100k",
                }
            ),
            hide_index=True,
            width="stretch",
        )
        estimate_notice(
            f"{live_ratios.hospitalisation_rate:.0%} hospitalisation rate, "
            f"{live_ratios.severe_fraction_of_admitted:.0%} severe, "
            f"{live_ratios.icu_fraction_of_admitted:.1%} ICU, "
            f"{live_ratios.mean_length_of_stay_days:.0f}-day mean stay"
            + (" (your ratios)." if is_customised else " (defaults).")
            + " Occupancy is against district beds estimated from World Bank national "
            "bed density, assuming 15% are available for dengue."
        )
        st.caption(
            "**Hospitals** and **Facilities/100k** are real OpenStreetMap counts "
            "(ODbL), not estimates — the same figures already used to set Stage 3's "
            "allocation floor for facility-poor districts, alongside the case-based "
            "high-risk flag."
        )

    with tab_supply:
        supply = readiness[
            ["district", "platelet_units", "iv_fluid_litres", "diagnostic_tests"]
        ].copy()
        supply["platelet_units"] = supply["platelet_units"].map("{:.0f}".format)
        supply["iv_fluid_litres"] = supply["iv_fluid_litres"].map("{:.0f}".format)
        supply["diagnostic_tests"] = supply["diagnostic_tests"].map("{:.0f}".format)
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
            width="stretch",
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
            # No use_container_width -- geoshape needs a fixed pixel extent.
            st.altair_chart(chart)
        if facilities is not None and not facilities.empty:
            st.markdown(f"**{len(facilities):,} health facilities** (OpenStreetMap, ODbL)")
            fmap = facility_map(facilities)
            if fmap is not None:
                st.altair_chart(fmap)
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
            "Lankan measurements. Change them to match your own case mix — the "
            "**Projected load** and **Supplies** tabs recompute live."
        )
        if is_customised:
            st.button(
                "Reset to defaults", on_click=lambda: st.session_state.update(_RATIO_DEFAULTS)
            )
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
            "These ratios recompute the readiness table above on every change. They "
            "do not touch the Stage 1 forecast or Stage 3 allocation — only the "
            "clinical-ratio arithmetic applied on top of it, so this stays well "
            "short of the app's rule against recomputing a model at request time."
        )


# ==========================================================================
# MOH portal
# ==========================================================================


def moh_portal(principal: Principal, data: dict[str, pd.DataFrame], horizon: int) -> None:
    principal.require(Permission.VIEW_DISTRICT_OPERATIONS)

    district_risk = data["district_risk"]
    sweep = data.get("allocation_sweep")
    scenarios = data.get("scenarios")
    capacity = data.get("district_capacity")

    facility_poor: frozenset[str] = frozenset()
    facilities_by_district: dict[str, int] = {}
    if capacity is not None and not capacity.empty:
        from dengue.ingest.health_facilities import facility_poor_districts

        # Same nsmallest-over-25-rows arithmetic pipeline.py runs to set
        # Stage 3's allocation floor -- recomputing it here to label the
        # cards is cheap enough not to violate "never compute at request
        # time" (that rule is about model refits and ILP re-solves).
        facility_poor = frozenset(facility_poor_districts(capacity))
        facilities_by_district = dict(zip(capacity["district_id"], capacity["n_facilities"]))

    st.subheader("District operations")
    st.caption(f"Scope: {principal.scope_label()} · {horizon} weeks ahead")

    all_assessments = assess_all(district_risk, horizon_weeks=horizon, audience="moh")

    def _hotspot_card(a) -> None:
        with st.container(border=True):
            c1, c2 = st.columns([1, 3])
            with c1:
                st.markdown(risk_pill(a.risk_level), unsafe_allow_html=True)
                st.markdown(f"**{a.district_name}**")
                n_fac = facilities_by_district.get(a.district_id)
                fac_line = f" · {n_fac} facilities" if n_fac is not None else ""
                st.caption(
                    f"{_fmt(a.forecast_median)} cases · {a.incidence_per_100k:.1f}/100k · "
                    f"{a.change_pct:+.0f}%{fac_line}"
                )
                if a.district_id in facility_poor:
                    st.caption("🏥 Facility-poor — qualifies for the allocation floor")
            with c2:
                recommendation_list(a.recommendations, limit=3)

    tab_ops, tab_teams, tab_plan, tab_scenario, tab_budget = st.tabs(
        ["Hotspots", "Team deployment", "Intervention plan", "Scenarios", "Budget"]
    )

    with tab_ops:
        own_names = sorted(DISTRICT_NAMES.get(d, d) for d in principal.districts)
        name_to_id = {v: k for k, v in DISTRICT_NAMES.items()}
        if principal.role is Role.MOH_OFFICER:
            # Which districts get a Hotspots card is chooseable -- this is a
            # viewing convenience, not a scope change: Team deployment,
            # Intervention plan and Budget below still run through
            # filter_to_scope() against the account's real districts, so
            # what this account can act on is unaffected by what it looks at
            # here.
            chosen_names = st.multiselect(
                "Districts shown",
                sorted(DISTRICT_NAMES.values()),
                default=own_names,
                key="moh_hotspot_districts",
            )
        else:
            chosen_names = own_names
        chosen_ids = {name_to_id[n] for n in chosen_names}
        shown = [a for a in all_assessments if a.district_id in chosen_ids]
        shown.sort(key=lambda a: a.incidence_per_100k, reverse=True)

        highlight_frame = _risk_frame(district_risk, horizon).copy()
        highlight_frame["is_shown"] = highlight_frame["district_id"].isin(chosen_ids)
        chart = _risk_choropleth(highlight_frame, highlight_column="is_shown")
        if chart is not None:
            # No use_container_width -- geoshape needs a fixed pixel extent.
            st.altair_chart(chart)

        for a in shown:
            _hotspot_card(a)

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
                    width="stretch",
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
                st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
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
                    width="stretch",
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
                    .mark_arc(innerRadius=60, stroke=PAGE, strokeWidth=2)
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
                    width="stretch",
                )
            with c2:
                # See the hospital readiness table for why this formats values
                # to strings rather than using st.column_config.
                table = split[["category", "share_pct", "amount_lkr", "evidence"]].copy()
                table["share_pct"] = table["share_pct"].map("{:.1f}%".format)
                table["amount_lkr"] = table["amount_lkr"].map("{:.0f}".format)
                st.dataframe(
                    table.rename(
                        columns={
                            "category": "Category",
                            "share_pct": "Share %",
                            "amount_lkr": "Amount (LKR)",
                            "evidence": "Evidence",
                        }
                    ),
                    hide_index=True,
                    width="stretch",
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
            width="stretch",
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
            width="stretch",
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
                width="stretch",
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
            width="stretch",
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
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.info(
            "**Authentication is connected (Supabase).** Accounts are provisioned by "
            "an administrator, not self-registered, and each account's role and "
            "district scope is loaded server-side from a `profiles` row (see "
            "`supabase/schema.sql`) — the viewer cannot choose a role, only sign "
            "into whichever account they hold. This matrix documents what each role "
            "is authorized to do once authenticated; it is not the login itself.",
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
