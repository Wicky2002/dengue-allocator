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
# SURFACE and PAGE used to be 3 points apart (#fcfcfb / #f9f9f7) -- close
# enough that white cards on the page background barely registered as
# separate surfaces, and the whole app read as one flat white canvas.
# SURFACE is now true white so cards visibly pop; PAGE and SIDEBAR are two
# deliberately distinct warm-neutral tiers (page background vs. the sidebar
# column) so there is real depth: sidebar > page > card, darkest to lightest.
# The warm-gray undertone matches GRIDLINE/BASELINE below rather than a cool
# gray, so it reads as one family rather than a mismatched patch.
SURFACE = "#ffffff"
PAGE = "#eeece2"
SIDEBAR = "#e5e2d4"
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
    --sidebar: {SIDEBAR};
    --ink-1: {INK_PRIMARY};
    --ink-2: {INK_SECONDARY};
    --ink-3: {INK_MUTED};
    --hairline: rgba(11,11,11,0.10);
    --series-1: {CATEGORICAL[0]};
    --critical: {STATUS["critical"]};
    --good: {STATUS["good"]};
    --warning: {STATUS["warning"]};
  }}

  /* Horizontal padding is pinned to a fixed value here (rather than left at
     whatever Streamlit's internal responsive default is) specifically so the
     header bar below can cancel it out exactly via matching negative
     margins -- Streamlit computes that default at runtime via CSS-in-JS with
     no fixed value exposed in its static CSS, so bleeding the bar to the
     true edge is only reliable against a padding value we set ourselves.
     Top padding is kept small but nonzero (rather than cancelled to 0 the
     same way) so the header bar doesn't collide with Streamlit's own fixed
     toolbar -- the sidebar-collapse arrow and hamburger menu float above the
     page at a height this stylesheet has no reliable way to read. */
  .block-container {{
    padding-top: 1rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 1400px;
  }}

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
  /* Background is a light tint of the same colour as the left border, rather
     than plain white -- a solid-white card with only a thin coloured edge
     reads as barely tinted at a glance; a tinted fill makes the accent/
     critical distinction visible without reading the border. */
  .kpi-accent {{ border-left: 3px solid var(--series-1); background: rgba(42,120,214,0.07); }}
  .kpi-critical {{ border-left: 3px solid var(--critical); background: rgba(208,59,59,0.07); }}

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
  section[data-testid="stSidebar"] > div {{ background: var(--sidebar); }}

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

  /* Product header (see app_header() in streamlit_app.py) -- a full-bleed
     coloured bar flush with the top and both edges of the content column,
     not a floating rounded card, so the app reads as branded from the first
     pixel rather than blending into Streamlit's default page chrome above
     the fold. The negative margins exactly cancel the fixed padding set on
     .block-container above (0 top / 2rem sides) -- that's what lets this
     reach the true top and side edges regardless of Streamlit's own
     (otherwise unknown) responsive padding, since we pinned it ourselves.
     Stays within the content column rather than bleeding under the sidebar:
     .block-container's parent already excludes the sidebar's width in both
     expanded and collapsed states, so there is no viewport-relative (100vw)
     math here that a sidebar could throw off. */
  .app-header-bar {{
    background: linear-gradient(120deg, {CATEGORICAL[0]} 0%, #1c5cab 100%);
    border-radius: 0;
    width: calc(100% + 4rem);
    padding: 26px 2rem 22px;
    margin: 0 -2rem 20px -2rem;
    box-shadow: 0 1px 2px rgba(11,11,11,0.08);
  }}
  .app-header {{
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 2px;
  }}
  /* line-height must leave headroom above the cap line: emoji glyphs render
     TALLER than their em box (Segoe UI Emoji especially), so `line-height: 1`
     on the 26px mark gave it a 26px line box the glyph overflowed, and the
     overflow -- which the bar's top padding does not account for -- read as
     the mosquito being clipped by the top edge of the header bar. Both mark
     and title share the same value so baseline alignment stays predictable. */
  .app-header .mark {{
    font-size: 26px;
    line-height: 1.3;
    filter: drop-shadow(0 1px 1px rgba(0,0,0,0.18));
  }}
  .app-header .title {{
    font-size: 24px;
    line-height: 1.3;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -.01em;
  }}
  .app-header-sub {{
    font-size: 13px;
    color: rgba(255,255,255,0.92);
    margin-top: 2px;
  }}
  .app-meta {{ font-size: 12.5px; color: rgba(255,255,255,0.72); margin-top: 4px; }}

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
    """Product-style page header: a full-width coloured bar with mark, title,
    subtitle, and a small meta line.

    Replaces a plain ``st.title()`` / ``st.caption()`` stack, which is what
    every default Streamlit app looks like. A solid brand-gradient band is
    what actually reads as "branded" above the fold -- coloured title text
    alone still sits on the same white page as everything else and gets lost.
    """
    meta_html = f'<div class="app-meta">{meta}</div>' if meta else ""
    return (
        '<div class="app-header-bar">'
        '<div class="app-header">'
        '<span class="mark">🦟</span>'
        f'<span class="title">{title}</span>'
        "</div>"
        f'<div class="app-header-sub">{subtitle}</div>'
        f"{meta_html}"
        "</div>"
    )
