"""Dengue Allocator — national dengue decision-support platform for Sri Lanka.

Four role portals over a three-stage engine:

* **Stage 1** probabilistic district case forecasts
* **Stage 2** mechanistic SEI-SIR intervention effects
* **Stage 3** constrained allocation of vector-control teams

Two rules this app follows without exception
--------------------------------------------
**It never computes at request time.** Every figure comes from a Parquet
artifact written by ``make pipeline``. Sliders index precomputed sweeps rather
than re-solving. A dashboard that recomputes on page load is unusable during an
outbreak, when the cost of a slow page is a delayed decision.

**Every number says what it is based on.** Observed, modelled, or a planning
estimate. The platform mixes notified case counts with model output and with
clinical ratios applied to forecasts; rendered identically, the last would borrow
the credibility of the first. See :mod:`dengue.platform.provenance`.

Run with ``make app``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
for extra in (REPO_ROOT / "src", REPO_ROOT / "app"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from portals import admin_portal, hospital_portal, moh_portal, public_portal
from theme import PAGE_CSS, register_theme

from dengue import config
from dengue.platform.rbac import DEMO_PRINCIPALS, Role

st.set_page_config(
    page_title="Dengue Allocator — Sri Lanka",
    page_icon="🦟",
    layout="wide",
    initial_sidebar_state="expanded",
)
register_theme()
st.markdown(PAGE_CSS, unsafe_allow_html=True)

ARTIFACTS = config.ARTIFACTS_DIR

#: Artifacts the app reads. A missing one degrades a panel, never the whole app.
ARTIFACT_NAMES = (
    "pipeline_meta",
    "district_risk",
    "panel_recent",
    "forecasts",
    "scores",
    "effect_table",
    "allocation_sweep",
    "allocation_summary",
    "sei_sir_params",
    "hospital_readiness",
    "district_capacity",
    "health_facilities",
    "scenarios",
    "budget_sweep",
)


@st.cache_data(show_spinner=False)
def load_all() -> dict[str, pd.DataFrame]:
    """Load every cached artifact that exists."""
    out: dict[str, pd.DataFrame] = {}
    for name in ARTIFACT_NAMES:
        path = ARTIFACTS / f"{name}.parquet"
        if not path.exists():
            continue
        frame = pd.read_parquet(path)
        for column in ("iso_week", "target_week"):
            if column in frame.columns:
                frame[column] = pd.to_datetime(frame[column], errors="coerce")
        out[name] = frame
    return out


data = load_all()

if "district_risk" not in data:
    st.title("Dengue Allocator — Sri Lanka")
    st.warning(
        "**No cached artifacts found.** Build them first:\n\n"
        "```bash\nmake pipeline\n```\n\n"
        f"Artifacts are written to `{ARTIFACTS}`.",
        icon="⚠️",
    )
    st.stop()

meta = data.get("pipeline_meta")
is_synthetic = bool(meta["is_synthetic"].iloc[0]) if meta is not None and not meta.empty else True

# --------------------------------------------------------------------------
# Sidebar: role switcher
# --------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🦟 Dengue Allocator")
    st.caption("National dengue decision support · Sri Lanka")
    st.divider()

    st.markdown("**Viewing as**")
    role = st.radio("Role", list(Role), format_func=lambda r: r.label, label_visibility="collapsed")
    principal = DEMO_PRINCIPALS[role]
    st.caption(principal.role.description)
    st.info(f"**Scope**\n\n{principal.scope_label()}", icon="🔎")

    st.divider()
    horizons = sorted(data["district_risk"]["horizon"].dropna().unique().tolist())
    horizon = st.selectbox(
        "Forecast horizon", horizons, index=0, format_func=lambda h: f"{h} weeks ahead"
    )

    st.divider()
    if meta is not None and not meta.empty:
        row = meta.iloc[0]
        st.caption(
            f"**Pipeline**  \nSource: `{row['panel_source']}`  \n"
            f"Model: `{row['forecast_model']}`  \nOrigin: {row['forecast_origin']}"
        )

    st.divider()
    st.caption(
        "**No authentication is connected.** This switcher demonstrates the access "
        "model; it is not a login and is not a security control."
    )

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------

st.title("Dengue Allocator")
st.caption(
    f"Forecast → causal effect → allocation · **{role.label}** portal · "
    f"{principal.scope_label()}"
)

if is_synthetic:
    st.error(
        "**Simulated data.** This run used the synthetic panel — realistic dynamics, "
        "but not observations. Do not read any figure here as real epidemiology. "
        "Run `make panel && make pipeline` against real sources for live figures.",
        icon="🔬",
    )

# --------------------------------------------------------------------------
# Route
# --------------------------------------------------------------------------

PORTALS = {
    Role.PUBLIC: public_portal,
    Role.HOSPITAL_STAFF: hospital_portal,
    Role.MOH_OFFICER: moh_portal,
    Role.NATIONAL_ADMIN: admin_portal,
}

try:
    PORTALS[role](principal, data, horizon)
except PermissionError as exc:
    # Should be unreachable: portals are built from permissions the role holds.
    # Surfacing it rather than swallowing it means a future RBAC regression shows
    # up as a visible error instead of silently rendering restricted data.
    st.error(f"**Access denied.** {exc}", icon="🔒")

# Public risk information is national and non-sensitive, so operational roles
# keep the citizen-facing view available beneath their own panels.
if role is not Role.PUBLIC:
    st.divider()
    with st.expander("Public view (what citizens see)"):
        public_portal(DEMO_PRINCIPALS[Role.PUBLIC], data, horizon)

st.divider()
st.caption(
    "Boundaries: OCHA/HDX (CC-BY-IGO) · Facilities: © OpenStreetMap contributors "
    "(ODbL) · Weather: Open-Meteo/ERA5 (CC-BY) · Bed density: World Bank (CC-BY) · "
    "Cases: colmozzie (CC0) / Epidemiology Unit, Sri Lanka"
)
