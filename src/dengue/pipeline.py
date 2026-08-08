"""End-to-end 3-stage pipeline: forecast -> causal effect -> allocation.

Run with ``make pipeline`` (or ``python -m dengue.pipeline``). Produces every
artifact the Streamlit dashboard reads, so the app never has to fit a model,
solve a program, or fetch data at request time.

Why the budget sweep is precomputed
-----------------------------------
An allocation dashboard needs a budget slider to be useful -- the first question
anyone asks is "what if we had twenty more teams?". Solving the ILP on slider
drag would violate the app's no-compute-at-request-time rule. Instead this
module solves the program across a **grid** of budgets and risk postures once,
and caches the result. The slider then indexes a lookup table: fully interactive,
zero runtime solving.

Artifacts written to ``artifacts/``
-----------------------------------
========================  =================================================
file                       contents
========================  =================================================
``panel_recent``           last ~2 years of the observed panel
``forecasts``              Stage 1 quantile forecasts, latest origin
``district_risk``          per-district forecast + incidence, for the table
``scores``                 backtest metrics (written by ``make baseline``)
``effect_table``           Stage 2 district x intensity response curves
``sei_sir_params``         fitted mechanistic parameters per district
``allocation_sweep``       Stage 3 solutions across the budget grid
``allocation_summary``     one row per (budget, quantile, strategy)
``pipeline_meta``          provenance: synthetic vs real, timestamps, versions
========================  =================================================
"""

from __future__ import annotations

import argparse
import time
from dataclasses import asdict

import numpy as np
import pandas as pd

from dengue import config
from dengue.utils.io import write_artifact
from dengue.utils.logging import get_logger

log = get_logger(__name__)

#: Budget grid for the precomputed sweep, in team-weeks.
DEFAULT_BUDGETS = tuple(range(10, 161, 10))

#: How many districts the NDCU designates high-risk in the app's default view.
DEFAULT_TOP_K_HIGH_RISK = 6


def run_stage1(panel: pd.DataFrame, *, horizons: tuple[int, ...] = config.HORIZONS) -> pd.DataFrame:
    """Fit the best Stage 1 model on all history and forecast from the last week.

    Uses :class:`~dengue.models.lgbm_quantile.LGBMQuantile`, falling back to
    :class:`~dengue.models.baseline.SeasonalNaive` if it fails -- a missing
    forecast would take down Stages 2 and 3 with it.
    """
    from dengue.models.baseline import SeasonalNaive
    from dengue.models.lgbm_quantile import LGBMQuantile
    from dengue.tuning.runner import load_tuned_params

    tuned = load_tuned_params("lgbm_quantile")
    params = tuned["params"] if tuned else None
    if tuned:
        log.info("pipeline: using GA-tuned LGBM hyperparameters (run `make tune` to refresh)")

    try:
        model = LGBMQuantile(horizons=horizons, params=params).fit(panel)
    except Exception as exc:  # - fall back rather than lose the stage
        log.error("pipeline: LGBMQuantile failed (%s); falling back to SeasonalNaive", exc)
        model = SeasonalNaive().fit(panel)

    frames = [model.predict(panel, horizon=h) for h in horizons]
    forecasts = pd.concat(frames, ignore_index=True)
    forecasts["model"] = model.name

    log.info(
        "pipeline/stage1: model=%s  rows=%d  origin=%s  horizons=%s",
        model.name,
        len(forecasts),
        forecasts["iso_week"].max(),
        list(horizons),
    )
    return forecasts


def run_stage2(
    panel: pd.DataFrame,
    forecasts: pd.DataFrame,
    *,
    max_team_weeks: int = 12,
    horizon_weeks: int = 4,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit SEI-SIR per district and build the effect table.

    Returns
    -------
    tuple
        ``(effect_table, parameters_frame)``.
    """
    from dengue.causal.sei_sir import build_effect_table, fit_all_districts

    started = time.perf_counter()
    parameters = fit_all_districts(panel)

    params_frame = pd.DataFrame([asdict(p) for p in parameters.values()])

    effect_table = build_effect_table(
        panel,
        parameters,
        max_team_weeks=max_team_weeks,
        horizon_weeks=horizon_weeks,
        forecasts=forecasts,
    )
    log.info(
        "pipeline/stage2: fitted %d districts in %.1fs; effect table rows=%d",
        len(parameters),
        time.perf_counter() - started,
        len(effect_table),
    )
    return effect_table, params_frame


def run_stage3(
    effect_table: pd.DataFrame,
    iso_week: pd.Period,
    *,
    budgets: tuple[int, ...] = DEFAULT_BUDGETS,
    high_risk_districts: tuple[str, ...] = (),
    max_teams_per_district: int = 12,
    min_teams_high_risk: int = 2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Solve the allocation across the budget grid.

    Returns
    -------
    tuple
        ``(sweep, summary)`` where ``summary`` has one row per scenario.
    """
    from dengue.optim.allocate import allocate_budget_sweep

    started = time.perf_counter()
    sweep = allocate_budget_sweep(
        effect_table,
        iso_week,
        list(budgets),
        max_teams_per_district=max_teams_per_district,
        min_teams_high_risk=min_teams_high_risk,
        high_risk_districts=high_risk_districts,
    )

    if sweep.empty:
        log.error("pipeline/stage3: sweep produced no solutions")
        return sweep, pd.DataFrame()

    summary = (
        sweep.groupby(["budget", "risk_quantile", "strategy"], observed=True)
        .agg(
            expected_cases_averted=("expected_cases_averted", "first"),
            shadow_price_budget=("shadow_price_budget", "first"),
            budget_used=("team_weeks", "sum"),
            districts_served=("team_weeks", lambda s: int((s > 0).sum())),
        )
        .reset_index()
    )

    # Uplift of the ILP over the greedy rank-and-fill baseline, per scenario.
    pivot = summary.pivot_table(
        index=["budget", "risk_quantile"],
        columns="strategy",
        values="expected_cases_averted",
        observed=True,
    )
    if {"ilp", "greedy"}.issubset(pivot.columns):
        pivot["uplift_pct"] = (
            100.0 * (pivot["ilp"] - pivot["greedy"]) / pivot["greedy"].replace(0, np.nan)
        )
        median_uplift = float(pivot["uplift_pct"].median())
        log.info(
            "pipeline/stage3: ILP beats greedy by a median of %.1f%% across the sweep",
            median_uplift,
        )
        summary = summary.merge(
            pivot[["uplift_pct"]].reset_index(), on=["budget", "risk_quantile"], how="left"
        )

    log.info("pipeline/stage3: %d scenarios in %.1fs", len(summary), time.perf_counter() - started)
    return sweep, summary


def build_district_risk(
    forecasts: pd.DataFrame, panel: pd.DataFrame, *, top_k: int = DEFAULT_TOP_K_HIGH_RISK
) -> pd.DataFrame:
    """Per-district risk view: latest forecast, incidence, and high-risk rank."""
    latest_origin = forecasts["iso_week"].max()
    latest = forecasts[forecasts["iso_week"] == latest_origin].copy()

    populations = panel.drop_duplicates("district_id").set_index("district_id")["population"]
    latest["population"] = latest["district_id"].map(populations).astype("float64")
    latest["incidence_per_100k"] = (
        latest["q0.5"].astype("float64") / latest["population"] * 100_000.0
    )
    latest["interval_width"] = latest["q0.9"].astype("float64") - latest["q0.1"].astype("float64")

    latest["risk_rank"] = latest.groupby("horizon", observed=True)["incidence_per_100k"].rank(
        ascending=False, method="first"
    )
    latest["high_risk"] = latest["risk_rank"] <= top_k

    # Recent observed level, so the UI can show direction of travel.
    recent = (
        panel.sort_values("iso_week")
        .groupby("district_id", observed=True)["cases"]
        .apply(lambda s: float(s.tail(4).mean()))
        .rename("recent_4w_mean_cases")
    )
    latest = latest.merge(recent, on="district_id", how="left")
    latest["change_vs_recent_pct"] = (
        100.0
        * (latest["q0.5"].astype("float64") - latest["recent_4w_mean_cases"])
        / latest["recent_4w_mean_cases"].replace(0, np.nan)
    )

    return latest.sort_values(["horizon", "incidence_per_100k"], ascending=[True, False])


def run_platform_layer(
    panel: pd.DataFrame,
    district_risk: pd.DataFrame,
    effect_table: pd.DataFrame,
    parameters: dict | None = None,
) -> dict[str, pd.DataFrame]:
    """Build the role-facing artifacts: capacity, readiness, scenarios, budget.

    Runs after Stages 1-3 because every one of these is derived from their
    outputs. Failures here are logged and skipped rather than aborting the run:
    the epidemiological stages are the load-bearing part, and a missing
    readiness table should not cost you the forecast.
    """
    from dengue.optim.budget import budget_sweep
    from dengue.platform.hospital import build_readiness_table

    out: dict[str, pd.DataFrame] = {}

    # --- health facilities and estimated bed capacity ---
    try:
        from dengue.ingest.health_facilities import build_district_capacity, load

        facilities, capacity = load()
        out["health_facilities"] = facilities
        out["district_capacity"] = capacity
        log.info("pipeline/platform: capacity for %d districts", len(capacity))
    except Exception as exc:
        log.error("pipeline/platform: facility ingest failed (%s)", exc)
        from dengue.ingest.health_facilities import build_district_capacity

        # Bed density is the load-bearing input; locations are a nice-to-have.
        capacity = build_district_capacity(None, beds_per_1000=3.93)
        out["district_capacity"] = capacity

    # --- hospital readiness, per horizon ---
    try:
        frames = [
            build_readiness_table(district_risk, capacity, horizon_weeks=h)
            for h in sorted(district_risk["horizon"].dropna().unique())
        ]
        out["hospital_readiness"] = pd.concat(frames, ignore_index=True)
        log.info("pipeline/platform: readiness rows=%d", len(out["hospital_readiness"]))
    except Exception as exc:
        log.error("pipeline/platform: readiness failed (%s)", exc)

    # --- scenarios (mechanistic, so only where Stage 2 fitted) ---
    if parameters:
        try:
            from dengue.platform.scenario import build_scenario_table

            # Scenarios are ODE integrations; restrict to the districts a planner
            # would actually be looking at rather than burning minutes on all 25.
            top = (
                district_risk[district_risk["horizon"] == district_risk["horizon"].min()]
                .nlargest(8, "incidence_per_100k")["district_id"]
                .astype(str)
                .tolist()
            )
            out["scenarios"] = build_scenario_table(parameters, panel, district_ids=top)
        except Exception as exc:
            log.error("pipeline/platform: scenarios failed (%s)", exc)

    # --- budget optimiser sweep ---
    try:
        max_effect = float(
            effect_table[effect_table["team_weeks"] == effect_table["team_weeks"].max()][
                "cases_averted_mean"
            ].sum()
        )
        budgets = [float(b) * 1e6 for b in range(5, 105, 5)]
        out["budget_sweep"] = budget_sweep(budgets, vector_max_effect=max_effect)
        log.info("pipeline/platform: budget sweep rows=%d", len(out["budget_sweep"]))
    except Exception as exc:
        log.error("pipeline/platform: budget sweep failed (%s)", exc)

    return out


def main(argv: list[str] | None = None) -> dict[str, pd.DataFrame]:
    """Run all three stages and write every dashboard artifact."""
    parser = argparse.ArgumentParser(description="Run the full 3-stage dengue pipeline.")
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Use the synthetic panel (fully offline). Implied when no panel exists.",
    )
    parser.add_argument("--n-weeks", type=int, default=520, help="Synthetic panel length.")
    parser.add_argument(
        "--max-team-weeks", type=int, default=12, help="Highest per-district intensity level."
    )
    parser.add_argument(
        "--effect-horizon", type=int, default=4, help="Weeks over which averted cases accumulate."
    )
    parser.add_argument(
        "--skip-stage2",
        action="store_true",
        help="Reuse a cached effect table instead of refitting SEI-SIR (slow step).",
    )
    args = parser.parse_args(argv)

    config.ensure_dirs()
    started = time.perf_counter()

    # ---- panel --------------------------------------------------------
    from dengue.utils.io import read_panel
    from dengue.utils.synthetic import make_synthetic_panel

    if args.synthetic or not config.PANEL_PATH.exists():
        if not args.synthetic:
            log.warning("pipeline: no panel at %s; using SYNTHETIC", config.PANEL_PATH)
        panel = make_synthetic_panel(n_weeks=args.n_weeks)
        panel_source = "synthetic"
    else:
        panel = read_panel()
        panel_source = "real"

    log.info(
        "pipeline: panel source=%s  rows=%d  districts=%d  weeks=[%s .. %s]",
        panel_source,
        len(panel),
        panel["district_id"].nunique(),
        panel["iso_week"].min(),
        panel["iso_week"].max(),
    )

    # ---- Stage 1 ------------------------------------------------------
    forecasts = run_stage1(panel)
    district_risk = build_district_risk(forecasts, panel)

    high_risk_districts = tuple(
        district_risk[(district_risk["high_risk"]) & (district_risk["horizon"] == 2)][
            "district_id"
        ].astype(str)
    )
    log.info("pipeline: high-risk districts (h=2): %s", list(high_risk_districts))

    # ---- Stage 2 ------------------------------------------------------
    effect_path = config.ARTIFACTS_DIR / "effect_table.parquet"
    parameters: dict | None = None
    if args.skip_stage2 and effect_path.exists():
        effect_table = pd.read_parquet(effect_path)
        params_frame = pd.DataFrame()
        # Fitted parameter objects are not recoverable from the cached table, so
        # scenario simulation (which needs them) is skipped in this mode.
        log.info(
            "pipeline/stage2: reusing cached effect table (%d rows); " "scenarios will be skipped",
            len(effect_table),
        )
    else:
        from dengue.causal.sei_sir import build_effect_table, fit_all_districts

        parameters = fit_all_districts(panel)
        params_frame = pd.DataFrame([asdict(p) for p in parameters.values()])
        effect_table = build_effect_table(
            panel,
            parameters,
            max_team_weeks=args.max_team_weeks,
            horizon_weeks=args.effect_horizon,
            forecasts=forecasts,
        )

    # ---- Stage 3 ------------------------------------------------------
    iso_week = forecasts["iso_week"].max()
    sweep, summary = run_stage3(
        effect_table,
        iso_week,
        high_risk_districts=high_risk_districts,
        max_teams_per_district=args.max_team_weeks,
    )

    # ---- Stage 4: platform layer --------------------------------------
    platform_artifacts = run_platform_layer(panel, district_risk, effect_table, parameters)

    # ---- artifacts ----------------------------------------------------
    recent_weeks = sorted(panel["iso_week"].unique())[-104:]
    artifacts: dict[str, pd.DataFrame] = {
        "panel_recent": panel[panel["iso_week"].isin(recent_weeks)],
        "forecasts": forecasts,
        "district_risk": district_risk,
        "effect_table": effect_table,
        "allocation_sweep": sweep,
        "allocation_summary": summary,
        **platform_artifacts,
    }
    if not params_frame.empty:
        artifacts["sei_sir_params"] = params_frame

    meta = pd.DataFrame(
        [
            {
                "generated_at": pd.Timestamp.utcnow().isoformat(),
                "panel_source": panel_source,
                "is_synthetic": panel_source == "synthetic",
                "panel_rows": len(panel),
                "n_districts": int(panel["district_id"].nunique()),
                "panel_start": str(panel["iso_week"].min()),
                "panel_end": str(panel["iso_week"].max()),
                "forecast_origin": str(iso_week),
                "forecast_model": str(forecasts["model"].iloc[0]),
                "max_team_weeks": args.max_team_weeks,
                "effect_horizon_weeks": args.effect_horizon,
                "runtime_seconds": round(time.perf_counter() - started, 1),
            }
        ]
    )
    artifacts["pipeline_meta"] = meta

    for name, frame in artifacts.items():
        write_artifact(frame, name)

    log.info(
        "pipeline: COMPLETE in %.1fs  artifacts=%d  source=%s",
        time.perf_counter() - started,
        len(artifacts),
        panel_source,
    )
    return artifacts


if __name__ == "__main__":  # pragma: no cover
    main()
