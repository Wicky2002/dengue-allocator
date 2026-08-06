"""Streamlit shell for the dengue-allocator dashboard.

**Reads cached artifacts only.** Every figure on this page comes from a Parquet
file written by ``make baseline``; no model is fitted and no data is fetched at
request time. That is a hard constraint, not an optimisation: a dashboard that
retrains on page load is unusable during an outbreak, when the people who need it
are refreshing it constantly and the cost of a slow page is a delayed decision.

Run with ``make app``. If no artifacts exist, the page says so and tells you
which command produces them, rather than silently rendering an empty table.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Make `dengue` importable when Streamlit runs this file directly.
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dengue import config  # noqa: E402

st.set_page_config(page_title="Dengue Allocator - Sri Lanka", page_icon=":mosquito:", layout="wide")

ARTIFACTS = config.ARTIFACTS_DIR


@st.cache_data(show_spinner=False)
def load_artifact(name: str) -> pd.DataFrame | None:
    """Load ``artifacts/<name>.parquet``, or None if it has not been built yet."""
    path = ARTIFACTS / f"{name}.parquet"
    if not path.exists():
        return None
    frame = pd.read_parquet(path)
    for column in ("iso_week", "target_week"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce")
    return frame


def district_display_names() -> dict[str, str]:
    return {d.district_id: d.name for d in config.DISTRICTS}


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------

st.title("Dengue Allocator - Sri Lanka")
st.caption(
    "Stage 1 (forecast) -> Stage 2 (causal effect) -> Stage 3 (allocation). "
    "This dashboard reads cached artifacts; it never runs a model at request time."
)

risk = load_artifact("district_risk")
scores = load_artifact("scores")
panel = load_artifact("panel_recent")

if risk is None:
    st.warning(
        "No cached artifacts found. Build them first:\n\n"
        "```\nmake baseline\n```\n\n"
        f"Artifacts are written to `{ARTIFACTS}`."
    )
    st.stop()

# Loud provenance banner: the default pipeline runs on simulated data, and a
# dashboard that does not say so is actively misleading.
st.error(
    "**Provenance check.** If these figures were produced by `make baseline`, they come "
    "from the **synthetic panel** - simulated data for pipeline development, not "
    "observations. Run `make panel && make baseline-real` for figures from real sources.",
    icon=":material/warning:",
)

names = district_display_names()

# ---- controls -------------------------------------------------------------
horizons = sorted(risk["horizon"].dropna().unique().tolist())
col_a, col_b = st.columns([1, 3])
with col_a:
    horizon = st.selectbox("Forecast horizon (weeks)", horizons, index=0)

view = risk[risk["horizon"] == horizon].copy()
view["district"] = view["district_id"].map(names).fillna(view["district_id"])

origin = view["iso_week"].max()
target = view["target_week"].max()
with col_b:
    st.metric(
        "Forecast origin -> target week",
        f"{origin:%Y-%m-%d} -> {target:%Y-%m-%d}" if pd.notna(origin) else "n/a",
    )

# ---- headline numbers -----------------------------------------------------
c1, c2, c3 = st.columns(3)
c1.metric("Districts forecast", f"{view['district_id'].nunique()}")
c2.metric("Total median forecast (cases)", f"{view['q0.5'].sum():,.0f}")
c3.metric(
    "Widest 80% interval (cases)",
    f"{(view['q0.9'] - view['q0.1']).max():,.0f}",
    help="Largest forecast uncertainty across districts. Wide intervals mark "
    "districts where the model is least sure - often the ones worth watching.",
)

# ---- risk table -----------------------------------------------------------
st.subheader(f"District risk table - {horizon} weeks ahead")

table = view[["district", "q0.1", "q0.5", "q0.9", "incidence_per_100k", "population"]].sort_values(
    "incidence_per_100k", ascending=False
)
table = table.rename(
    columns={
        "district": "District",
        "q0.1": "P10",
        "q0.5": "Median",
        "q0.9": "P90",
        "incidence_per_100k": "Incidence /100k",
        "population": "Population",
    }
)

st.dataframe(
    table,
    hide_index=True,
    width="stretch",
    column_config={
        "P10": st.column_config.NumberColumn(format="%.0f"),
        "Median": st.column_config.NumberColumn(format="%.0f"),
        "P90": st.column_config.NumberColumn(format="%.0f"),
        "Incidence /100k": st.column_config.NumberColumn(format="%.1f"),
        "Population": st.column_config.NumberColumn(format="%d"),
    },
)

st.bar_chart(table.set_index("District")["Incidence /100k"], height=340)

# ---- observed history -----------------------------------------------------
if panel is not None and not panel.empty:
    st.subheader("Observed weekly cases")
    options = sorted(panel["district_id"].map(names).dropna().unique())
    default = [d for d in ("Colombo", "Gampaha", "Kandy") if d in options][:3]
    chosen = st.multiselect("Districts", options, default=default or options[:3])

    if chosen:
        inverse = {v: k for k, v in names.items()}
        ids = [inverse[c] for c in chosen]
        history = panel[panel["district_id"].isin(ids)].copy()
        history["district"] = history["district_id"].map(names)
        wide = history.pivot_table(
            index="iso_week", columns="district", values="cases", observed=True
        )
        st.line_chart(wide, height=340)

# ---- model comparison -----------------------------------------------------
if scores is not None and not scores.empty:
    st.subheader("Model comparison")
    headline = scores[
        scores["metric"].isin(
            ["pinball_mean", "mae", "mape", "coverage_80", "mean_lead_time_weeks"]
        )
    ]
    fold_options = sorted(headline["fold"].dropna().unique()) if "fold" in headline else []
    if fold_options:
        fold = st.radio("Fold", fold_options, horizontal=True, index=len(fold_options) - 1)
        headline = headline[headline["fold"] == fold]

    pivot = headline.pivot_table(
        index=["model", "horizon"], columns="metric", values="value", observed=True
    ).reset_index()
    st.dataframe(pivot, hide_index=True, width="stretch")
    st.caption(
        "pinball_mean is the headline metric (lower is better). "
        f"coverage_80 should sit near {config.PI_NOMINAL_COVERAGE:.2f}."
    )

# ---- stages not yet built -------------------------------------------------
st.divider()
st.subheader("Stages 2 and 3")
st.info(
    "**Stage 2 (SEI-SIR intervention effects)** and **Stage 3 (ILP team allocation)** "
    "are scaffolded with typed signatures and full design notes but not yet implemented. "
    "See `src/dengue/causal/sei_sir.py` and `src/dengue/optim/allocate.py`.",
    icon=":material/construction:",
)
