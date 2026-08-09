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
from theme import BASELINE, CATEGORICAL, INK_MUTED, SEQUENTIAL_BLUE, STATUS

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


@st.cache_data(show_spinner=False)
def _geometry_data_uri() -> str | None:
    """The district GeoJSON as a base64 ``data:`` URI, or None if unavailable.

    Why a data URI instead of passing the parsed geometry as inline
    ``values``: Streamlit's chart component tries to Arrow-serialise inline
    list/dict data for transport, and Arrow's columnar model has no good
    representation for GeoJSON's deeply nested, variable-depth coordinate
    arrays (``Polygon`` vs ``MultiPolygon`` alone differ in nesting depth).
    In testing, that round-trip silently produced geometries with no usable
    coordinates -- the chart *compiled* and the legend rendered, but nothing
    was ever drawn, with no error anywhere. The exact same spec renders
    correctly through a bare Vega-Embed page on the identical Vega-Lite
    version, which is what isolated the bug to Streamlit's data pipeline
    rather than the spec or the map geometry itself.

    A ``data:`` URI sidesteps this entirely: it is a single opaque string in
    the spec, so Streamlit's Arrow conversion never touches it, and the
    browser's own ``fetch()`` (which Vega-Lite uses for any ``url`` data
    source) decodes and parses it directly.
    """
    import base64
    import json

    geometry = load_geometry()
    if geometry is None:
        return None
    payload = json.dumps(geometry).encode("utf-8")
    encoded = base64.b64encode(payload).decode("ascii")
    return f"data:application/json;base64,{encoded}"


def _geometry_source() -> alt.Data | None:
    """Altair data source for the district geometry, routed through the fix
    described in :func:`_geometry_data_uri`."""
    uri = _geometry_data_uri()
    if uri is None:
        return None
    return alt.Data(url=uri, format=alt.DataFormat(type="json", property="features"))


def _safe_field(name: str) -> str:
    """Vega-Lite-safe alias for a column name.

    Vega-Lite treats ``.`` in a field name as nested-property access unless
    escaped, so a column literally called ``"q0.5"`` is read as "property `5`
    inside object `q0`" -- which doesn't exist, and can silently break an
    encoding, a tooltip, or an entire ``transform_lookup`` join depending on
    where it lands in the spec. Several of this project's own columns
    (``q0.1``, ``q0.5``, ``q0.9``) are named exactly this way, so every chart
    built from a DataFrame column must route the field name through this
    function rather than using the raw column name directly.
    """
    return name.replace(".", "_")


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
    width: int = 460,
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
    width:
        A concrete pixel width. Not load-bearing for the rendering bug this
        function works around (see :func:`_geometry_data_uri`) -- that turned
        out to be Streamlit's data pipeline, not sizing -- but geoshape's
        ``.project()`` still reads more predictably from a fixed extent than
        a container-relative one, so this chart is still meant to be called
        with ``st.altair_chart(chart)``, not ``use_container_width=True``.

    Returns
    -------
    altair.Chart or None
        None when the geometry asset is unavailable, so the caller can fall back
        to a table rather than rendering an empty pane.
    """
    geo_source = _geometry_source()
    if geo_source is None:
        return None

    # Route every field name through _safe_field before it reaches Altair.
    # This is the one place that has to get it right -- see _safe_field's
    # docstring for why a raw "q0.5" silently breaks the lookup/encoding.
    tooltip_columns = tooltip_columns or [(value_column, value_column, ".1f")]
    safe_value_column = _safe_field(value_column)
    rename_map = {value_column: safe_value_column}
    rename_map.update({c: _safe_field(c) for c, _, _ in tooltip_columns})

    values = values.rename(columns=rename_map)
    lookup_fields = list(dict.fromkeys(rename_map.values()))

    if categorical:
        order = domain_order or RISK_ORDER
        present = [v for v in order if v in set(values[safe_value_column].dropna())]
        colours = colour_map or RISK_COLOURS
        colour = alt.Color(
            f"{safe_value_column}:N",
            scale=alt.Scale(domain=present, range=[colours[v] for v in present]),
            legend=alt.Legend(title=legend_title or None, orient="top", direction="horizontal"),
        )
    else:
        # scheme and range are mutually exclusive ways to define a Scale;
        # `scheme=None` is not "no scheme", it fails schema validation
        # outright ("'None' is an invalid value for `scheme`"), which broke
        # every numeric (non-categorical) choropleth -- e.g. hospital
        # occupancy -- the same way the dotted-field bug broke categorical
        # ones. Omit the kwarg entirely rather than passing None.
        colour = alt.Color(
            f"{safe_value_column}:Q",
            scale=alt.Scale(range=list(SEQUENTIAL_BLUE)),
            legend=alt.Legend(title=legend_title or None, orient="right", gradientLength=220),
        )

    tooltips = [alt.Tooltip("properties.name:N", title="District")]
    for column, label, fmt in tooltip_columns:
        safe_column = _safe_field(column)
        tooltips.append(
            alt.Tooltip(f"{safe_column}:Q" if fmt else f"{safe_column}:N", title=label, format=fmt)
        )

    # geo_source is a data: URI (see _geometry_data_uri), not inline `values`
    # -- required to avoid Streamlit's Arrow serialisation of the geometry.
    chart = (
        alt.Chart(geo_source)
        .mark_geoshape(stroke="#fcfcfb", strokeWidth=0.8)
        .transform_lookup(
            lookup="properties.district_id",
            from_=alt.LookupData(values, key="district_id", fields=lookup_fields),
        )
        .encode(color=colour, tooltip=tooltips)
        .project(type="mercator")
        .properties(width=width, height=height, title=title or "")
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


def rainfall_cases_overlay(history: pd.DataFrame, height: int = 300) -> alt.Chart:
    """Rainfall and cases on one shared timeline, for direct lag comparison.

    This is a companion to :func:`rainfall_vs_cases`, not a replacement for
    it -- that function's stacked-panel design stays the honest default. This
    one exists because overlaying the two series makes the ~6-8 week lag easy
    to eyeball at a glance, which two separate panels don't give you for free.

    It still avoids a raw dual-axis (two independently chosen y-scales can
    manufacture any apparent correlation): both series are min-max normalised
    to 0-100 over the plotted window and share one axis, so the vertical
    position only ever encodes "how close to this series' own peak", not a
    magnitude comparison between rain and cases.
    """
    frame = history[["iso_week", "cases", "rain_mm"]].dropna().sort_values("iso_week").copy()

    def _normalise(series: pd.Series) -> pd.Series:
        lo, hi = series.min(), series.max()
        if hi <= lo:
            return series * 0.0
        return (series - lo) / (hi - lo) * 100.0

    frame["cases_norm"] = _normalise(frame["cases"])
    frame["rain_norm"] = _normalise(frame["rain_mm"])

    long = pd.concat(
        [
            frame[["iso_week", "cases_norm", "cases"]]
            .rename(columns={"cases_norm": "value", "cases": "raw"})
            .assign(series="Dengue cases"),
            frame[["iso_week", "rain_norm", "rain_mm"]]
            .rename(columns={"rain_norm": "value", "rain_mm": "raw"})
            .assign(series="Rainfall"),
        ],
        ignore_index=True,
    )

    colours = {"Dengue cases": CATEGORICAL[0], "Rainfall": CATEGORICAL[2]}

    lines = (
        alt.Chart(long)
        .mark_line(strokeWidth=2.25, point=alt.OverlayMarkDef(size=35, filled=True))
        .encode(
            x=alt.X("iso_week:T", title=None),
            y=alt.Y("value:Q", title="Relative scale (0-100, each series normalised)"),
            color=alt.Color(
                "series:N",
                scale=alt.Scale(domain=list(colours), range=list(colours.values())),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[
                alt.Tooltip("iso_week:T", title="Week"),
                alt.Tooltip("series:N", title="Series"),
                alt.Tooltip("raw:Q", title="Value", format=",.1f"),
            ],
        )
        .properties(height=height)
    )
    return lines


def history_and_forecast_chart(
    history: pd.DataFrame,
    forecast: pd.DataFrame,
    *,
    height: int = 320,
    history_weeks: int | None = 10,
) -> alt.Chart:
    """One continuous timeline: solid observed history flowing into a dashed
    forecast band.

    Parameters
    ----------
    history:
        Columns ``iso_week`` (datetime), ``cases``.
    forecast:
        Columns ``target_week`` (datetime), ``q0.5``, ``q0.1``, ``q0.9`` --
        already aggregated to whatever level this is called at (e.g. summed
        across districts for a national view). Summing per-district medians
        and per-district interval bounds is a coarse aggregate -- district
        forecast errors are not perfectly correlated, so the summed band is
        somewhat wider than a jointly-modelled national interval would be --
        but it is the right order of magnitude for an at-a-glance overview
        chart, not a number anyone should plan clinical capacity against.
    history_weeks:
        Trim the observed line to this many trailing weeks before charting
        (``None`` keeps the full history passed in). The forecast horizon is
        fixed at 2-4 weeks by the underlying models -- it cannot be extended
        without retraining -- so the way to make the forecast the visual
        focus of a chart that would otherwise be mostly history is to shrink
        the history window, not to invent forecast weeks that don't exist.

    The last observed point is duplicated as the first forecast point (with
    zero-width interval) so the band starts exactly where the solid line
    ends, rather than leaving a visible gap.
    """
    hist = history[["iso_week", "cases"]].rename(columns={"iso_week": "week"}).copy()
    hist["kind"] = "observed"
    hist = hist.sort_values("week")
    if history_weeks is not None and len(hist) > history_weeks:
        hist = hist.tail(history_weeks)

    fc = forecast.rename(
        columns={"target_week": "week", "q0.5": "median", "q0.1": "lower", "q0.9": "upper"}
    )[["week", "median", "lower", "upper"]].copy()
    fc["kind"] = "forecast"

    if not hist.empty:
        bridge = pd.DataFrame(
            {
                "week": [hist["week"].iloc[-1]],
                "median": [hist["cases"].iloc[-1]],
                "lower": [hist["cases"].iloc[-1]],
                "upper": [hist["cases"].iloc[-1]],
                "kind": ["forecast"],
            }
        )
        fc = pd.concat([bridge, fc], ignore_index=True)

    forecast_colour = CATEGORICAL[1]  # orange -- distinct from observed blue, draws the eye

    band = (
        alt.Chart(fc)
        .mark_area(color=forecast_colour, opacity=0.28, line=False)
        .encode(
            x=alt.X("week:T", title=None),
            y=alt.Y("lower:Q", title="Cases"),
            y2="upper:Q",
        )
        .properties(height=height)
    )
    observed_line = (
        alt.Chart(hist)
        .mark_line(color=CATEGORICAL[0], strokeWidth=1.75, opacity=0.75)
        .encode(
            x="week:T",
            y=alt.Y("cases:Q", title="Cases"),
            tooltip=[
                alt.Tooltip("week:T", title="Week"),
                alt.Tooltip("cases:Q", title="Observed cases", format=","),
            ],
        )
    )
    forecast_line = (
        alt.Chart(fc)
        .mark_line(color=forecast_colour, strokeWidth=3.5, strokeDash=[5, 4])
        .encode(
            x="week:T",
            y=alt.Y("median:Q", title="Cases"),
            tooltip=[
                alt.Tooltip("week:T", title="Target week"),
                alt.Tooltip("median:Q", title="Forecast (median)", format=",.0f"),
                alt.Tooltip("lower:Q", title="P10", format=",.0f"),
                alt.Tooltip("upper:Q", title="P90", format=",.0f"),
            ],
        )
    )
    forecast_points = (
        alt.Chart(fc[fc["kind"] == "forecast"])
        .mark_point(color=forecast_colour, size=110, filled=True, stroke="white", strokeWidth=1)
        .encode(x="week:T", y="median:Q")
    )

    layers = [band, observed_line, forecast_line, forecast_points]

    if not hist.empty and not fc.empty:
        boundary = hist["week"].iloc[-1]
        rule = (
            alt.Chart(pd.DataFrame({"week": [boundary]}))
            .mark_rule(color=BASELINE, strokeDash=[2, 2], strokeWidth=1)
            .encode(x="week:T")
        )
        label_row = fc[fc["kind"] == "forecast"].iloc[[-1]].copy()
        label = (
            alt.Chart(label_row)
            .mark_text(
                align="right",
                baseline="bottom",
                dy=-8,
                color=forecast_colour,
                fontWeight="bold",
                fontSize=12,
            )
            .encode(x="week:T", y="upper:Q", text=alt.value("Forecast"))
        )
        layers = [rule, *layers, label]

    return alt.layer(*layers).properties(height=height)


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


def facility_map(facilities: pd.DataFrame, height: int = 520, width: int = 460) -> alt.Chart | None:
    """Health facilities over the district outline.

    Like :func:`choropleth`, ``width`` must be a concrete number -- render with
    ``st.altair_chart(chart)``, not ``use_container_width=True``. See
    :func:`choropleth`'s docstring for why.
    """
    geo_source = _geometry_source()
    if geo_source is None or facilities.empty:
        return None

    outline = (
        alt.Chart(geo_source)
        .mark_geoshape(fill="#f0efec", stroke="#c3c2b7", strokeWidth=0.7)
        .project(type="mercator")
        .properties(width=width, height=height)
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
