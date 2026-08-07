"""Dengue Allocator dashboard -- Sri Lanka.

**Reads cached artifacts only.** Every figure comes from a Parquet file written
by ``make pipeline``. No model is fitted, no program is solved, and no data is
fetched at request time.

That is a hard constraint, not an optimisation. A dashboard that recomputes on
page load is unusable during an outbreak, when the people who need it are
refreshing constantly and the cost of a slow page is a delayed decision. The
budget slider on the Allocation tab looks like it re-solves the ILP; it does not.
``dengue.pipeline`` solves the program across a grid of budgets ahead of time and
the slider indexes the cached result.

Run with ``make app``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(REPO_ROOT / "app") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "app"))

from theme import (
    CATEGORICAL,
    PAGE_CSS,
    SEQUENTIAL_BLUE,
    STATUS,
    kpi_html,
    register_theme,
)

from dengue import config

st.set_page_config(
    page_title="Dengue Allocator — Sri Lanka",
    page_icon="🦟",
    layout="wide",
    initial_sidebar_state="expanded",
)
register_theme()
st.markdown(PAGE_CSS, unsafe_allow_html=True)

ARTIFACTS = config.ARTIFACTS_DIR
DISTRICT_NAMES = {d.district_id: d.name for d in config.DISTRICTS}
NAME_TO_ID = {v: k for k, v in DISTRICT_NAMES.items()}


@st.cache_data(show_spinner=False)
def load(name: str) -> pd.DataFrame | None:
    """Load ``artifacts/<name>.parquet``, or None if it has not been built."""
    path = ARTIFACTS / f"{name}.parquet"
    if not path.exists():
        return None
    frame = pd.read_parquet(path)
    for column in ("iso_week", "target_week"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce")
    if "district_id" in frame.columns:
        frame["district"] = frame["district_id"].map(DISTRICT_NAMES).fillna(frame["district_id"])
    return frame


def fmt(value: float, digits: int = 0) -> str:
    return "—" if pd.isna(value) else f"{value:,.{digits}f}"


# --------------------------------------------------------------------------
# Load
# --------------------------------------------------------------------------

meta = load("pipeline_meta")
risk = load("district_risk")
panel = load("panel_recent")
scores = load("scores")
effects = load("effect_table")
sweep = load("allocation_sweep")
summary = load("allocation_summary")
params = load("sei_sir_params")

if risk is None:
    st.title("Dengue Allocator — Sri Lanka")
    st.warning(
        "**No cached artifacts found.** Build them first:\n\n"
        "```bash\nmake pipeline\n```\n\n"
        f"Artifacts are written to `{ARTIFACTS}`.",
        icon="⚠️",
    )
    st.stop()

is_synthetic = bool(meta["is_synthetic"].iloc[0]) if meta is not None and not meta.empty else True

# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### Dengue Allocator")
    st.caption("Forecast → causal effect → allocation")

    horizons = sorted(risk["horizon"].dropna().unique().tolist())
    horizon = st.selectbox(
        "Forecast horizon", horizons, index=0, format_func=lambda h: f"{h} weeks ahead"
    )

    st.divider()
    if meta is not None and not meta.empty:
        row = meta.iloc[0]
        st.markdown("**Pipeline run**")
        st.caption(
            f"Source: `{row['panel_source']}`  \n"
            f"Model: `{row['forecast_model']}`  \n"
            f"Origin: {row['forecast_origin']}  \n"
            f"Districts: {row['n_districts']}  \n"
            f"Runtime: {row['runtime_seconds']}s"
        )
    st.divider()
    st.caption(
        "This dashboard reads **cached artifacts**. It never fits a model or "
        "solves the allocation program at request time."
    )

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------

st.title("Dengue Allocator — Sri Lanka")
st.caption(
    "A 3-stage decision system for vector-control team deployment: "
    "probabilistic district forecasts, mechanistic intervention effects, and a "
    "constrained allocation program."
)

if is_synthetic:
    st.error(
        "**These figures come from the SYNTHETIC panel** — simulated data for pipeline "
        "development, not observations. Do not read them as real epidemiology. "
        "Run `make panel && make pipeline` for figures from real sources.",
        icon="🔬",
    )

view = risk[risk["horizon"] == horizon].copy()
origin = view["iso_week"].max()
target = view["target_week"].max()

tab_overview, tab_forecast, tab_effect, tab_alloc, tab_perf = st.tabs(
    ["Overview", "① Forecast", "② Intervention effect", "③ Allocation", "Model performance"]
)

# ==========================================================================
# Overview
# ==========================================================================
with tab_overview:
    total_median = float(view["q0.5"].sum())
    n_high_risk = int(view["high_risk"].sum()) if "high_risk" in view else 0
    worst = view.nlargest(1, "incidence_per_100k")
    worst_name = worst["district"].iloc[0] if not worst.empty else "—"
    worst_rate = float(worst["incidence_per_100k"].iloc[0]) if not worst.empty else float("nan")

    tiles = [
        kpi_html("Forecast horizon", f"{horizon} weeks", f"Target week {target:%d %b %Y}"),
        kpi_html("Total forecast cases", fmt(total_median), "Median across all districts"),
        kpi_html("High-risk districts", str(n_high_risk), "By forecast incidence rank", "critical"),
        kpi_html("Highest incidence", worst_name, f"{fmt(worst_rate, 1)} per 100k"),
    ]

    if summary is not None and not summary.empty:
        ilp = summary[(summary["strategy"] == "ilp") & (summary["risk_quantile"] == 0.5)]
        if not ilp.empty:
            mid = ilp.iloc[len(ilp) // 2]
            tiles.append(
                kpi_html(
                    "Cases averted",
                    fmt(mid["expected_cases_averted"]),
                    f"At {int(mid['budget'])} team-weeks (Stage 3)",
                )
            )

    st.markdown(f'<div class="kpi-row">{"".join(tiles)}</div>', unsafe_allow_html=True)

    left, right = st.columns([3, 2])

    with left:
        st.markdown("**National weekly cases — observed**")
        if panel is not None and not panel.empty:
            national = panel.groupby("iso_week", observed=True)["cases"].sum().reset_index()
            chart = (
                alt.Chart(national)
                .mark_line(color=CATEGORICAL[0], strokeWidth=2)
                .encode(
                    x=alt.X("iso_week:T", title=None),
                    y=alt.Y("cases:Q", title="Cases per week"),
                    tooltip=[
                        alt.Tooltip("iso_week:T", title="Week"),
                        alt.Tooltip("cases:Q", title="Cases", format=","),
                    ],
                )
                .properties(height=280)
            )
            st.altair_chart(chart, use_container_width=True)
            st.caption("Two peaks a year track the southwest (Yala) and northeast (Maha) monsoons.")

    with right:
        st.markdown("**Top districts by forecast incidence**")
        top = view.nlargest(10, "incidence_per_100k")
        bars = (
            alt.Chart(top)
            .mark_bar(cornerRadiusEnd=4, color=CATEGORICAL[0])
            .encode(
                y=alt.Y("district:N", sort="-x", title=None),
                x=alt.X("incidence_per_100k:Q", title="Forecast cases per 100k"),
                tooltip=[
                    alt.Tooltip("district:N", title="District"),
                    alt.Tooltip("incidence_per_100k:Q", title="Per 100k", format=".1f"),
                    alt.Tooltip("q0.5:Q", title="Median cases", format=".0f"),
                ],
            )
            .properties(height=280)
        )
        st.altair_chart(bars, use_container_width=True)

    st.divider()
    st.markdown("**How the three stages fit together**")
    s1, s2, s3 = st.columns(3)
    s1.markdown(
        '<span class="stage-pill">Stage 1</span> **Forecast**  \n'
        "Probabilistic district-week case forecasts at 2–4 weeks, with calibrated "
        "prediction intervals. Answers *where are cases going*.",
        unsafe_allow_html=True,
    )
    s2.markdown(
        '<span class="stage-pill">Stage 2</span> **Causal effect**  \n'
        "A mechanistic SEI-SIR model, intervened on directly. Answers *how many cases "
        "does a team actually avert* — which a forecast cannot tell you.",
        unsafe_allow_html=True,
    )
    s3.markdown(
        '<span class="stage-pill">Stage 3</span> **Allocation**  \n'
        "An integer program over the concave effect curves. Answers *where do the "
        "teams go*, subject to budget, high-risk floors and week-to-week continuity.",
        unsafe_allow_html=True,
    )

# ==========================================================================
# Stage 1 — Forecast
# ==========================================================================
with tab_forecast:
    st.markdown(
        f"**District risk table** — forecast origin {origin:%d %b %Y}, "
        f"target week {target:%d %b %Y}"
    )

    columns = ["district", "q0.1", "q0.5", "q0.9", "incidence_per_100k", "population"]
    if "change_vs_recent_pct" in view.columns:
        columns.insert(5, "change_vs_recent_pct")

    table = view[columns].sort_values("incidence_per_100k", ascending=False)
    renames = {
        "district": "District",
        "q0.1": "P10",
        "q0.5": "Median",
        "q0.9": "P90",
        "incidence_per_100k": "Per 100k",
        "change_vs_recent_pct": "vs recent 4w",
        "population": "Population",
    }
    st.dataframe(
        table.rename(columns=renames),
        hide_index=True,
        use_container_width=True,
        column_config={
            "P10": st.column_config.NumberColumn(format="%.0f"),
            "Median": st.column_config.NumberColumn(
                format="%.0f", help="Median forecast — the central estimate"
            ),
            "P90": st.column_config.NumberColumn(format="%.0f"),
            "Per 100k": st.column_config.NumberColumn(format="%.1f"),
            "vs recent 4w": st.column_config.NumberColumn(
                format="%+.0f%%", help="Change against the last 4 observed weeks"
            ),
            "Population": st.column_config.NumberColumn(format="%d"),
        },
    )

    st.markdown("**Forecast with 80% prediction interval**")
    interval_source = view.nlargest(15, "incidence_per_100k")
    base = alt.Chart(interval_source).encode(y=alt.Y("district:N", sort="-x", title=None))
    rule = base.mark_rule(color="#c3c2b7", strokeWidth=2).encode(
        x=alt.X("q0.1:Q", title="Forecast cases"), x2="q0.9:Q"
    )
    dot = base.mark_point(
        size=90, filled=True, color=CATEGORICAL[0], stroke="#fcfcfb", strokeWidth=2
    ).encode(
        x="q0.5:Q",
        tooltip=[
            alt.Tooltip("district:N", title="District"),
            alt.Tooltip("q0.1:Q", title="P10", format=".0f"),
            alt.Tooltip("q0.5:Q", title="Median", format=".0f"),
            alt.Tooltip("q0.9:Q", title="P90", format=".0f"),
        ],
    )
    st.altair_chart((rule + dot).properties(height=420), use_container_width=True)
    st.caption(
        "The bar is the 80% prediction interval; the dot is the median. Wide bars mark "
        "districts the model is least sure about — often the ones worth watching."
    )

    if panel is not None and not panel.empty:
        st.divider()
        st.markdown("**Observed history**")
        options = sorted(panel["district"].dropna().unique())
        default = [d for d in ("Colombo", "Gampaha", "Kandy") if d in options]
        chosen = st.multiselect(
            "Districts", options, default=default or options[:3], max_selections=8
        )
        if chosen:
            history = panel[panel["district"].isin(chosen)]
            line = (
                alt.Chart(history)
                .mark_line(strokeWidth=2)
                .encode(
                    x=alt.X("iso_week:T", title=None),
                    y=alt.Y("cases:Q", title="Weekly cases"),
                    color=alt.Color(
                        "district:N",
                        title=None,
                        scale=alt.Scale(range=list(CATEGORICAL)),
                    ),
                    tooltip=[
                        alt.Tooltip("district:N", title="District"),
                        alt.Tooltip("iso_week:T", title="Week"),
                        alt.Tooltip("cases:Q", title="Cases"),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(line, use_container_width=True)

# ==========================================================================
# Stage 2 — Intervention effect
# ==========================================================================
with tab_effect:
    if effects is None or effects.empty:
        st.info("No effect table found. Run `make pipeline` to build Stage 2.", icon="ℹ️")
    else:
        st.markdown("**Dose–response: cases averted by intervention intensity**")
        st.caption(
            "Each curve is a district's response to vector control, from the mechanistic "
            "SEI-SIR model with the vector parameters intervened on directly. The curves "
            "**bend** — that concavity is the whole reason Stage 3 is an optimisation and "
            "not a sorted list."
        )

        top_districts = (
            effects[effects["team_weeks"] == effects["team_weeks"].max()]
            .nlargest(6, "cases_averted_mean")["district"]
            .tolist()
        )
        picked = st.multiselect(
            "Districts",
            sorted(effects["district"].unique()),
            default=top_districts,
            max_selections=8,
        )
        subset = effects[effects["district"].isin(picked)] if picked else effects

        curve = (
            alt.Chart(subset)
            .mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=45, filled=True))
            .encode(
                x=alt.X("team_weeks:Q", title="Team-weeks deployed"),
                y=alt.Y("cases_averted_mean:Q", title="Cases averted (4-week window)"),
                color=alt.Color("district:N", title=None, scale=alt.Scale(range=list(CATEGORICAL))),
                tooltip=[
                    alt.Tooltip("district:N", title="District"),
                    alt.Tooltip("team_weeks:Q", title="Team-weeks"),
                    alt.Tooltip("cases_averted_mean:Q", title="Averted", format=".1f"),
                    alt.Tooltip("coverage:Q", title="Coverage", format=".1%"),
                ],
            )
            .properties(height=360)
        )
        st.altair_chart(curve, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Marginal return per additional team-week**")
            marginal = (
                alt.Chart(subset)
                .mark_line(strokeWidth=2)
                .encode(
                    x=alt.X("team_weeks:Q", title="Team-weeks already deployed"),
                    y=alt.Y(
                        "marginal_cases_averted_per_team_week:Q",
                        title="Extra cases averted by one more team",
                    ),
                    color=alt.Color(
                        "district:N", title=None, scale=alt.Scale(range=list(CATEGORICAL))
                    ),
                    tooltip=[
                        alt.Tooltip("district:N", title="District"),
                        alt.Tooltip("team_weeks:Q", title="Team-weeks"),
                        alt.Tooltip(
                            "marginal_cases_averted_per_team_week:Q",
                            title="Marginal",
                            format=".2f",
                        ),
                    ],
                )
                .properties(height=300)
            )
            st.altair_chart(marginal, use_container_width=True)
            st.caption("Downward slope = diminishing returns. This is what the ILP exploits.")

        with col_b:
            st.markdown("**Coverage achieved**")
            cov = (
                alt.Chart(subset)
                .mark_line(strokeWidth=2)
                .encode(
                    x=alt.X("team_weeks:Q", title="Team-weeks deployed"),
                    y=alt.Y("coverage:Q", title="Premises coverage", axis=alt.Axis(format="%")),
                    color=alt.Color(
                        "district:N", title=None, scale=alt.Scale(range=list(CATEGORICAL))
                    ),
                    tooltip=[
                        alt.Tooltip("district:N", title="District"),
                        alt.Tooltip("coverage:Q", title="Coverage", format=".1%"),
                    ],
                )
                .properties(height=300)
            )
            st.altair_chart(cov, use_container_width=True)
            st.caption(
                "Coverage saturates as `1 − exp(−teams/scale)`, scaled by population — "
                "one team cannot blanket Colombo as easily as Mullaitivu."
            )

        if params is not None and not params.empty:
            st.divider()
            st.markdown("**Fitted SEI-SIR parameters**")
            show = params.copy()
            show["district"] = show["district_id"].map(DISTRICT_NAMES).fillna(show["district_id"])
            cols = [
                "district",
                "r0_mean",
                "rain_elasticity",
                "init_susceptible",
                "reporting_fraction",
                "log_likelihood",
                "converged",
            ]
            st.dataframe(
                show[[c for c in cols if c in show.columns]].rename(
                    columns={
                        "district": "District",
                        "r0_mean": "R₀",
                        "rain_elasticity": "Rain elasticity",
                        "init_susceptible": "Initial susceptible",
                        "reporting_fraction": "Reporting fraction ρ",
                        "log_likelihood": "Log-likelihood",
                        "converged": "Converged",
                    }
                ),
                hide_index=True,
                use_container_width=True,
                column_config={
                    "R₀": st.column_config.NumberColumn(format="%.2f"),
                    "Rain elasticity": st.column_config.NumberColumn(format="%.2f"),
                    "Initial susceptible": st.column_config.NumberColumn(format="%.2f"),
                    "Reporting fraction ρ": st.column_config.NumberColumn(format="%.2f"),
                    "Log-likelihood": st.column_config.NumberColumn(format="%.0f"),
                },
            )
            st.caption(
                "**ρ is fixed, not fitted.** R₀ and ρ trade off almost exactly, so fitting "
                "both yields a ridge rather than a peak. The absolute scale of averted cases "
                "inherits that assumption; the district *ranking* — which is what Stage 3 "
                "consumes — is far more robust to it."
            )

# ==========================================================================
# Stage 3 — Allocation
# ==========================================================================
with tab_alloc:
    if sweep is None or sweep.empty:
        st.info("No allocation found. Run `make pipeline` to build Stage 3.", icon="ℹ️")
    else:
        budgets = sorted(sweep["budget"].unique().tolist())
        c1, c2 = st.columns([2, 1])
        with c1:
            budget = st.select_slider(
                "Weekly budget (team-weeks)", options=budgets, value=budgets[len(budgets) // 2]
            )
        with c2:
            posture = st.radio(
                "Risk posture",
                [0.5, 0.9],
                format_func=lambda q: "Median (q0.5)" if q == 0.5 else "Risk-averse (q0.9)",
                horizontal=False,
            )

        st.caption(
            "The slider does **not** re-solve the program. Every budget shown here was "
            "solved ahead of time by `make pipeline` and cached; the slider indexes a lookup."
        )

        scenario = sweep[
            (sweep["budget"] == budget)
            & (sweep["risk_quantile"] == posture)
            & (sweep["strategy"] == "ilp")
        ]
        greedy = sweep[
            (sweep["budget"] == budget)
            & (sweep["risk_quantile"] == posture)
            & (sweep["strategy"] == "greedy")
        ]

        if scenario.empty:
            st.warning("No solution cached for that combination.", icon="⚠️")
        else:
            averted = float(scenario["expected_cases_averted"].iloc[0])
            greedy_averted = (
                float(greedy["expected_cases_averted"].iloc[0])
                if not greedy.empty
                else float("nan")
            )
            shadow = scenario["shadow_price_budget"].iloc[0]
            served = int((scenario["team_weeks"] > 0).sum())
            uplift = averted - greedy_averted if pd.notna(greedy_averted) else float("nan")

            tiles = [
                kpi_html("Cases averted", fmt(averted, 1), f"Over a {4}-week window"),
                kpi_html(
                    "Districts served", str(served), f"of {scenario['district_id'].nunique()}"
                ),
                kpi_html(
                    "Marginal value of a team",
                    fmt(float(shadow), 2) if pd.notna(shadow) else "—",
                    "Cases averted per extra team-week",
                ),
                kpi_html(
                    "Uplift vs rank-and-fill",
                    f"+{fmt(uplift, 1)}" if pd.notna(uplift) else "—",
                    "Cases averted above the greedy baseline",
                    "critical" if pd.notna(uplift) and uplift <= 0 else "accent",
                ),
            ]
            st.markdown(f'<div class="kpi-row">{"".join(tiles)}</div>', unsafe_allow_html=True)

            st.markdown("**Recommended deployment**")
            plan = scenario[scenario["team_weeks"] > 0].sort_values("team_weeks", ascending=False)
            alloc_chart = (
                alt.Chart(plan)
                .mark_bar(cornerRadiusEnd=4)
                .encode(
                    y=alt.Y("district:N", sort="-x", title=None),
                    x=alt.X("team_weeks:Q", title="Team-weeks assigned"),
                    color=alt.Color(
                        "team_weeks:Q",
                        title="Team-weeks",
                        scale=alt.Scale(range=list(SEQUENTIAL_BLUE)),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("district:N", title="District"),
                        alt.Tooltip("team_weeks:Q", title="Team-weeks"),
                    ],
                )
                .properties(height=max(240, 22 * len(plan)))
            )
            st.altair_chart(alloc_chart, use_container_width=True)

            st.divider()
            st.markdown("**Efficiency frontier — is another team worth funding?**")
            if summary is not None and not summary.empty:
                frontier = summary[summary["risk_quantile"] == posture]
                front_chart = (
                    alt.Chart(frontier)
                    .mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=45, filled=True))
                    .encode(
                        x=alt.X("budget:Q", title="Weekly budget (team-weeks)"),
                        y=alt.Y("expected_cases_averted:Q", title="Expected cases averted"),
                        color=alt.Color(
                            "strategy:N",
                            title=None,
                            scale=alt.Scale(
                                domain=["ilp", "greedy"],
                                range=[CATEGORICAL[0], CATEGORICAL[1]],
                            ),
                            legend=alt.Legend(
                                labelExpr="datum.label == 'ilp' ? 'ILP (optimal)' : 'Rank-and-fill'"
                            ),
                        ),
                        tooltip=[
                            alt.Tooltip("strategy:N", title="Strategy"),
                            alt.Tooltip("budget:Q", title="Budget"),
                            alt.Tooltip("expected_cases_averted:Q", title="Averted", format=".1f"),
                        ],
                    )
                    .properties(height=340)
                )
                st.altair_chart(front_chart, use_container_width=True)
                st.caption(
                    "The frontier flattens as the budget grows — the same diminishing returns "
                    "seen in Stage 2, now aggregated nationally. Where it flattens is where "
                    "extra teams stop being worth funding."
                )

            with st.expander("Constraints this plan satisfies"):
                st.markdown(
                    f"""
- **Budget** — at most **{budget}** team-weeks in total.
- **One intensity level per district** — modelled as a binary per (district, level),
  which represents the concave effect curve exactly while keeping the program linear.
- **High-risk floor** — districts flagged high-risk by Stage 1 receive a minimum
  allocation regardless of their marginal return.
- **Per-district cap** — no district may absorb the whole budget.
- **Continuity** *(rolling mode)* — a district's allocation may not swing more than a
  set number of teams week to week. Teams are people; reassigning all of them every
  week is not operationally real.
"""
                )

            st.markdown("**Full plan**")
            st.dataframe(
                scenario[["district", "team_weeks"]]
                .sort_values("team_weeks", ascending=False)
                .rename(columns={"district": "District", "team_weeks": "Team-weeks"}),
                hide_index=True,
                use_container_width=True,
            )

# ==========================================================================
# Model performance
# ==========================================================================
with tab_perf:
    if scores is None or scores.empty:
        st.info("No scores found. Run `make baseline` to build the backtest.", icon="ℹ️")
    else:
        st.markdown("**Rolling-origin backtest**")
        st.caption(
            "Strict expanding-window rolling origin — never a random split. At origin *t* "
            "the model sees weeks ≤ *t* and nothing else."
        )

        folds = sorted(scores["fold"].dropna().unique()) if "fold" in scores.columns else []
        if folds:
            fold = st.radio("Fold", folds, horizontal=True, index=len(folds) - 1)
            frame = scores[scores["fold"] == fold]
        else:
            frame = scores

        headline = frame[
            frame["metric"].isin(
                [
                    "pinball_mean",
                    "mae",
                    "mape",
                    "coverage_80",
                    "interval_width",
                    "mean_lead_time_weeks",
                ]
            )
        ]
        pivot = headline.pivot_table(
            index=["model", "horizon"], columns="metric", values="value", observed=True
        ).reset_index()
        st.dataframe(pivot, hide_index=True, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Pinball loss** — headline metric, lower is better")
            pin = frame[frame["metric"] == "pinball_mean"]
            pin_chart = (
                alt.Chart(pin)
                .mark_bar(cornerRadiusEnd=4)
                .encode(
                    x=alt.X("horizon:O", title="Horizon (weeks)"),
                    y=alt.Y("value:Q", title="Mean pinball loss"),
                    color=alt.Color(
                        "model:N", title=None, scale=alt.Scale(range=list(CATEGORICAL))
                    ),
                    xOffset="model:N",
                    tooltip=["model:N", "horizon:O", alt.Tooltip("value:Q", format=".3f")],
                )
                .properties(height=300)
            )
            st.altair_chart(pin_chart, use_container_width=True)

        with col_b:
            st.markdown("**80% interval coverage** — target 0.80")
            cov = frame[frame["metric"] == "coverage_80"]
            cov_bars = (
                alt.Chart(cov)
                .mark_bar(cornerRadiusEnd=4)
                .encode(
                    x=alt.X("horizon:O", title="Horizon (weeks)"),
                    y=alt.Y("value:Q", title="Empirical coverage", scale=alt.Scale(domain=[0, 1])),
                    color=alt.Color(
                        "model:N", title=None, scale=alt.Scale(range=list(CATEGORICAL))
                    ),
                    xOffset="model:N",
                    tooltip=["model:N", "horizon:O", alt.Tooltip("value:Q", format=".3f")],
                )
                .properties(height=300)
            )
            target_rule = (
                alt.Chart(pd.DataFrame({"y": [config.PI_NOMINAL_COVERAGE]}))
                .mark_rule(color=STATUS["critical"], strokeDash=[4, 4], strokeWidth=2)
                .encode(y="y:Q")
            )
            st.altair_chart(cov_bars + target_rule, use_container_width=True)
            st.caption(
                "Bars below the dashed line are **overconfident** — the interval is too "
                "narrow for its nominal coverage."
            )
