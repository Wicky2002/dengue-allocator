"""Reusable UI components: choropleth maps, KPI tiles, provenance badges.

The map is the important one. A district choropleth answers "where is this bad"
in one glance, which a table of 25 rows does not — and every portal needs that
question answered, at different levels of detail.
"""

from __future__ import annotations

from typing import Any

import altair as alt
import pandas as pd
import streamlit as st
from theme import CATEGORICAL, INK_MUTED, SEQUENTIAL_BLUE, STATUS

from dengue.platform.provenance import ProvenanceTier
from dengue.platform.risk import RiskLevel

#: Fill colours for the four risk bands. Reserved status colours — never reused
#: as a categorical series colour anywhere in the app.
RISK_COLOURS = {
    RiskLevel.LOW.value: RiskLevel.LOW.colour,
    RiskLevel.MODERATE.value: RiskLevel.MODERATE.colour,
    RiskLevel.HIGH.value: RiskLevel.HIGH.colour,
    RiskLevel.SEVERE.value: RiskLevel.SEVERE.colour,
}

RISK_ORDER = [
    r.value for r in (RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.SEVERE)
]

CAPACITY_COLOURS = {
    "normal": STATUS["good"],
    "busy": STATUS["warning"],
    "near_capacity": STATUS["serious"],
    "over_capacity": STATUS["critical"],
}


@st.cache_data(show_spinner=False)
def load_geometry() -> dict[str, Any] | None:
    """Load the district GeoJSON, or None if the asset is missing."""
    try:
        from dengue.ingest.boundaries import load_district_geojson

        return load_district_geojson()
    except (FileNotFoundError, ImportError):
        return None


def choropleth(
    values: pd.DataFrame,
    *,
    value_column: str,
    title: str = "",
    categorical: bool = False,
    colour_map: dict[str, str] | None = None,
    domain_order: list[str] | None = None,
    tooltip_columns: list[tuple[str, str, str]] | None = None,
    height: int = 520,
    legend_title: str = "",
) -> alt.Chart | None:
    """District choropleth of Sri Lanka.

    Parameters
    ----------
    values:
        Must contain ``district_id`` plus ``value_column``.
    value_column:
        Column driving the fill.
    categorical:
        True for banded fills (risk level, capacity status), False for a
        continuous magnitude ramp.
    colour_map:
        ``category -> hex`` when ``categorical``.
    tooltip_columns:
        ``(column, title, format)`` triples.

    Returns
    -------
    altair.Chart or None
        None when the geometry asset is unavailable, so the caller can fall back
        to a table rather than rendering an empty pane.
    """
    geometry = load_geometry()
    if geometry is None:
        return None

    lookup_fields = [value_column] + [c for c, _, _ in (tooltip_columns or [])]
    lookup_fields = list(dict.fromkeys(lookup_fields))  # de-dupe, keep order

    if categorical:
        order = domain_order or RISK_ORDER
        present = [v for v in order if v in set(values[value_column].dropna())]
        colours = colour_map or RISK_COLOURS
        colour = alt.Color(
            f"{value_column}:N",
            scale=alt.Scale(domain=present, range=[colours[v] for v in present]),
            legend=alt.Legend(title=legend_title or None, orient="top", direction="horizontal"),
        )
    else:
        colour = alt.Color(
            f"{value_column}:Q",
            scale=alt.Scale(scheme=None, range=list(SEQUENTIAL_BLUE)),
            legend=alt.Legend(title=legend_title or None, orient="right", gradientLength=220),
        )

    tooltips = [alt.Tooltip("properties.name:N", title="District")]
    for column, label, fmt in tooltip_columns or [(value_column, value_column, ".1f")]:
        tooltips.append(
            alt.Tooltip(f"{column}:Q" if fmt else f"{column}:N", title=label, format=fmt)
        )

    chart = (
        alt.Chart(alt.Data(values=geometry, format=alt.DataFormat(property="features")))
        .mark_geoshape(stroke="#fcfcfb", strokeWidth=0.8)
        .transform_lookup(
            lookup="properties.district_id",
            from_=alt.LookupData(values, key="district_id", fields=lookup_fields),
        )
        .encode(color=colour, tooltip=tooltips)
        .project(type="mercator")
        .properties(height=height, title=title or "")
    )
    return chart


def risk_pill(level: RiskLevel) -> str:
    """Inline HTML pill for a risk band."""
    return (
        f'<span style="display:inline-block;padding:3px 12px;border-radius:999px;'
        f"background:{level.colour};color:#fff;font-weight:650;font-size:12px;"
        f'letter-spacing:.02em;">{level.label.upper()}</span>'
    )


def provenance_badge(tier: ProvenanceTier) -> str:
    """Small badge marking what a number is based on."""
    colours = {
        ProvenanceTier.OBSERVED: STATUS["good"],
        ProvenanceTier.MODELLED: CATEGORICAL[0],
        ProvenanceTier.ASSUMED: STATUS["warning"],
        ProvenanceTier.USER_INPUT: CATEGORICAL[6],
    }
    return (
        f'<span title="{tier.description}" style="display:inline-block;padding:1px 7px;'
        f"border-radius:4px;border:1px solid {colours[tier]};color:{colours[tier]};"
        f'font-size:10px;font-weight:650;letter-spacing:.04em;">{tier.badge}</span>'
    )


def estimate_notice(basis: str) -> None:
    """Standard caption beneath a planning estimate."""
    st.caption(f"⚠️ **Planning estimate**, not a measurement — {basis}")


def kpi_grid(tiles: list[str]) -> None:
    """Render KPI tiles in a responsive grid."""
    st.markdown(f'<div class="kpi-row">{"".join(tiles)}</div>', unsafe_allow_html=True)


def trend_chart(
    history: pd.DataFrame,
    *,
    value_column: str = "cases",
    colour: str = CATEGORICAL[0],
    height: int = 260,
    y_title: str = "Weekly cases",
) -> alt.Chart:
    """Single-series weekly trend line. No legend — the title names the series."""
    return (
        alt.Chart(history)
        .mark_line(color=colour, strokeWidth=2)
        .encode(
            x=alt.X("iso_week:T", title=None),
            y=alt.Y(f"{value_column}:Q", title=y_title),
            tooltip=[
                alt.Tooltip("iso_week:T", title="Week"),
                alt.Tooltip(f"{value_column}:Q", title=y_title, format=","),
            ],
        )
        .properties(height=height)
    )


def rainfall_vs_cases(history: pd.DataFrame, height: int = 300) -> alt.Chart:
    """Rainfall and cases as two stacked panels sharing an x-axis.

    Deliberately **not** a dual-axis chart. Two y-scales on one frame let the
    author manufacture any apparent correlation by choosing the scales, which is
    exactly the claim this figure is making. Stacked panels with a shared time
    axis show the same lag relationship without that failure mode.
    """
    base = alt.Chart(history).encode(x=alt.X("iso_week:T", title=None))

    cases = (
        base.mark_line(color=CATEGORICAL[0], strokeWidth=2)
        .encode(
            y=alt.Y("cases:Q", title="Weekly cases"),
            tooltip=[
                alt.Tooltip("iso_week:T", title="Week"),
                alt.Tooltip("cases:Q", title="Cases"),
            ],
        )
        .properties(height=height // 2)
    )

    rain = (
        base.mark_area(color=CATEGORICAL[2], opacity=0.65, line=False)
        .encode(
            y=alt.Y("rain_mm:Q", title="Rainfall (mm)"),
            tooltip=[
                alt.Tooltip("iso_week:T", title="Week"),
                alt.Tooltip("rain_mm:Q", title="Rain (mm)", format=".0f"),
            ],
        )
        .properties(height=height // 2)
    )

    return alt.vconcat(cases, rain, spacing=6).resolve_scale(x="shared")


def recommendation_list(recommendations, limit: int = 6) -> None:
    """Render recommendations with their rationale.

    The rationale is not optional dressing: an instruction from a model that does
    not say why is not actionable, and a planner cannot judge whether it applies.
    """
    urgency_icon = {"urgent": "🔴", "elevated": "🟠", "routine": "🔵"}
    for rec in recommendations[:limit]:
        icon = urgency_icon.get(rec.urgency, "🔵")
        st.markdown(f"{icon} **{rec.action}**")
        st.markdown(
            f'<div style="margin:-6px 0 12px 26px;font-size:12.5px;color:{INK_MUTED};">'
            f"{rec.rationale}</div>",
            unsafe_allow_html=True,
        )


def facility_map(facilities: pd.DataFrame, height: int = 520) -> alt.Chart | None:
    """Health facilities over the district outline."""
    geometry = load_geometry()
    if geometry is None or facilities.empty:
        return None

    outline = (
        alt.Chart(alt.Data(values=geometry, format=alt.DataFormat(property="features")))
        .mark_geoshape(fill="#f0efec", stroke="#c3c2b7", strokeWidth=0.7)
        .project(type="mercator")
        .properties(height=height)
    )

    points = (
        alt.Chart(facilities)
        .mark_circle(opacity=0.75, stroke="#fcfcfb", strokeWidth=0.5)
        .encode(
            longitude="lon:Q",
            latitude="lat:Q",
            size=alt.Size(
                "facility_type:N",
                scale=alt.Scale(domain=["hospital", "clinic"], range=[70, 22]),
                legend=alt.Legend(title="Facility", orient="top"),
            ),
            color=alt.Color(
                "facility_type:N",
                scale=alt.Scale(
                    domain=["hospital", "clinic"], range=[CATEGORICAL[0], CATEGORICAL[2]]
                ),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[
                alt.Tooltip("name:N", title="Name"),
                alt.Tooltip("facility_type:N", title="Type"),
            ],
        )
    )
    return outline + points
