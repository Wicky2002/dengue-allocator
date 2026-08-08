"""Chart theme and design tokens for the dashboard.

One palette, applied once, so every chart in the app reads as one system.

The values come from a validated categorical palette: the slot ordering is the
colourblind-safety mechanism, not decoration, so hues are assigned **in fixed
order and never cycled**. Sequential (magnitude) encodings use a single blue
ramp light-to-dark; status colours are reserved and never reused as a series.
"""

from __future__ import annotations

import altair as alt

# --- categorical slots, in fixed order -----------------------------------
CATEGORICAL: tuple[str, ...] = (
    "#2a78d6",  # 1 blue
    "#eb6834",  # 2 orange
    "#1baf7a",  # 3 aqua
    "#eda100",  # 4 yellow
    "#e87ba4",  # 5 magenta
    "#008300",  # 6 green
    "#4a3aa7",  # 7 violet
    "#e34948",  # 8 red
)

#: Forms that put every pair on screen at once (scatter, choropleth, small
#: multiples) only validate for the first three slots. Past three, fold to
#: "Other" or facet rather than adding a fourth hue.
CATEGORICAL_ALL_PAIRS_CAP = 3

# --- sequential (magnitude), single hue light -> dark ---------------------
SEQUENTIAL_BLUE: tuple[str, ...] = (
    "#cde2fb",
    "#9ec5f4",
    "#6da7ec",
    "#3987e5",
    "#2a78d6",
    "#256abf",
    "#1c5cab",
    "#184f95",
    "#104281",
)

# --- status, reserved: never a series colour -----------------------------
STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

# --- chrome & ink ---------------------------------------------------------
SURFACE = "#fcfcfb"
PAGE = "#f9f9f7"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"

FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def altair_theme() -> dict:
    """Altair theme config: recessive grid and axes, thin marks, no chart junk."""
    return {
        "config": {
            "background": "transparent",
            "font": FONT,
            "view": {"stroke": "transparent", "continuousHeight": 300},
            "axis": {
                "labelColor": INK_MUTED,
                "titleColor": INK_SECONDARY,
                "labelFontSize": 11,
                "titleFontSize": 11,
                "titleFontWeight": "normal",
                "gridColor": GRIDLINE,
                "gridWidth": 1,
                "domainColor": BASELINE,
                "tickColor": BASELINE,
                "labelPadding": 6,
                "titlePadding": 10,
            },
            "axisX": {"grid": False},
            "legend": {
                "labelColor": INK_SECONDARY,
                "titleColor": INK_SECONDARY,
                "labelFontSize": 11,
                "titleFontSize": 11,
                "titleFontWeight": "normal",
                "symbolType": "circle",
                "symbolSize": 80,
                "orient": "top",
                "direction": "horizontal",
                "offset": 4,
            },
            "title": {
                "color": INK_PRIMARY,
                "fontSize": 13,
                "fontWeight": 600,
                "anchor": "start",
                "offset": 12,
            },
            "range": {"category": list(CATEGORICAL), "heatmap": list(SEQUENTIAL_BLUE)},
            "bar": {"cornerRadiusEnd": 4},
            "line": {"strokeWidth": 2},
            "point": {"size": 64, "filled": True},
        }
    }


def register_theme(name: str = "dengue") -> None:
    """Register and enable the theme, across Altair 4/5 API differences."""
    try:  # Altair 5.5+
        alt.theme.register(name, enable=True)(altair_theme)
        return
    except (AttributeError, TypeError):
        pass
    try:  # Altair 5.0-5.4 / 4.x
        alt.themes.register(name, altair_theme)
        alt.themes.enable(name)
    except Exception:  # - an unthemed chart is still a usable chart
        pass


PAGE_CSS = f"""
<style>
  :root {{
    --surface: {SURFACE};
    --page: {PAGE};
    --ink-1: {INK_PRIMARY};
    --ink-2: {INK_SECONDARY};
    --ink-3: {INK_MUTED};
    --hairline: rgba(11,11,11,0.10);
    --series-1: {CATEGORICAL[0]};
    --critical: {STATUS["critical"]};
    --good: {STATUS["good"]};
    --warning: {STATUS["warning"]};
  }}

  .block-container {{ padding-top: 2.2rem; max-width: 1400px; }}

  /* KPI tiles */
  .kpi-row {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 12px;
    margin: 4px 0 18px 0;
  }}
  .kpi {{
    background: var(--surface);
    border: 1px solid var(--hairline);
    border-radius: 10px;
    padding: 14px 16px;
  }}
  .kpi-label {{
    font-size: 11px;
    letter-spacing: .04em;
    text-transform: uppercase;
    color: var(--ink-3);
    margin-bottom: 6px;
  }}
  .kpi-value {{
    font-size: 26px;
    font-weight: 650;
    color: var(--ink-1);
    line-height: 1.1;
  }}
  .kpi-sub {{ font-size: 11.5px; color: var(--ink-2); margin-top: 5px; }}
  .kpi-accent {{ border-left: 3px solid var(--series-1); }}
  .kpi-critical {{ border-left: 3px solid var(--critical); }}

  .stage-pill {{
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 999px;
    background: rgba(42,120,214,0.12);
    color: #1c5cab;
    margin-right: 8px;
  }}

  section[data-testid="stSidebar"] {{ border-right: 1px solid var(--hairline); }}
  section[data-testid="stSidebar"] > div {{ background: var(--page); }}

  /* Tabs: recessive by default, on-brand underline when active -- the
     default Streamlit look uses its own red-orange accent here regardless of
     [theme].primaryColor, so this has to be set explicitly. */
  .stTabs [data-baseweb="tab"] {{
    font-size: 14px;
    color: var(--ink-2);
  }}
  .stTabs [aria-selected="true"] {{
    color: var(--ink-1) !important;
    font-weight: 600;
  }}
  .stTabs [data-baseweb="tab-highlight"] {{
    background-color: var(--series-1) !important;
    height: 2px;
  }}
  .stTabs [data-baseweb="tab-border"] {{ background-color: var(--hairline); }}

  /* Buttons: match the categorical palette rather than Streamlit's default. */
  .stButton > button {{
    border-radius: 8px;
    border: 1px solid var(--hairline);
    font-weight: 550;
  }}
  .stButton > button[kind="primary"] {{
    background: var(--series-1);
    border-color: var(--series-1);
  }}
  .stButton > button[kind="primary"]:hover {{
    background: #1c5cab;
    border-color: #1c5cab;
  }}

  /* Dataframe / table chrome. */
  div[data-testid="stDataFrame"] {{ border-radius: 8px; border: 1px solid var(--hairline); }}
  div[data-testid="stDataFrame"] [role="columnheader"] {{
    background: var(--page);
    color: var(--ink-2);
    font-weight: 600;
  }}

  /* st.metric: align its default look with the KPI tile system. */
  div[data-testid="stMetric"] {{
    background: var(--surface);
    border: 1px solid var(--hairline);
    border-radius: 10px;
    padding: 12px 14px;
  }}
  div[data-testid="stMetricLabel"] {{ color: var(--ink-3); }}
  div[data-testid="stMetricValue"] {{ color: var(--ink-1); }}

  /* Slider handle/track on brand. */
  div[data-testid="stSlider"] [role="slider"] {{ background-color: var(--series-1); }}

  /* Product header (see app_header() in streamlit_app.py). */
  .app-header {{
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 2px;
  }}
  .app-header .mark {{ font-size: 26px; line-height: 1; }}
  .app-header .title {{
    font-size: 24px;
    font-weight: 700;
    color: var(--ink-1);
    letter-spacing: -.01em;
  }}
  .app-meta {{ font-size: 12.5px; color: var(--ink-3); margin-top: 2px; }}

  /* This is a demo dashboard, not a deployed Streamlit Cloud app -- the
     "Deploy" affordance is noise; [client].toolbarMode = "minimal" in
     .streamlit/config.toml already hides it, this is the CSS-only fallback
     for Streamlit versions where that setting isn't honoured. */
  [data-testid="stToolbarActions"] button[title="Deploy this app"] {{ display: none; }}
</style>
"""


def kpi_html(label: str, value: str, sub: str = "", accent: str = "accent") -> str:
    """One KPI tile. ``accent`` is ``"accent"`` or ``"critical"``."""
    klass = "kpi-critical" if accent == "critical" else "kpi-accent"
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="kpi {klass}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f"{sub_html}</div>"
    )


def app_header(title: str, subtitle: str, meta: str = "") -> str:
    """Product-style page header: mark + title + subtitle, small meta line.

    Replaces a plain ``st.title()`` / ``st.caption()`` stack, which is what
    every default Streamlit app looks like. Reuses the same design tokens as
    the KPI tiles so the header reads as part of one system rather than a
    Streamlit default sitting above custom components.
    """
    meta_html = f'<div class="app-meta">{meta}</div>' if meta else ""
    return (
        '<div class="app-header">'
        '<span class="mark">🦟</span>'
        f'<span class="title">{title}</span>'
        "</div>"
        f'<div class="kpi-sub" style="margin-top:2px;">{subtitle}</div>'
        f"{meta_html}"
    )
