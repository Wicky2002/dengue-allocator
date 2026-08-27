"""Predicted-vs-actual Stage 1 forecasts for a fixed historical window.

Companion to the app's real/observed "View a past week" map
(``app/portals.py:national_overview``). That feature is free: ``panel_recent``
already holds the real cases for any past week. This module is the harder
half -- "what did the model predict for that week, back when it only had data
up to some earlier origin" -- which the live pipeline cannot answer, because
:func:`dengue.pipeline.run_stage1` only ever keeps the *latest* forecast
origin (see ``pipeline.py``'s own module docstring on ``district_risk``).

Why the window is fixed, not rolling
-------------------------------------
This platform was built and iterated on in June-August 2026. Bounding the
window to :data:`HISTORY_START`-:data:`HISTORY_END` keeps this scoped to "how
did our own model do while we were building it" rather than silently growing
into an unbounded, ever-more-expensive backtest every week it isn't touched.

Every origin in the window is a genuine expanding-window refit via
:func:`dengue.eval.backtest.rolling_origin` -- the same leakage-safe machinery
the main baseline comparison uses -- with the exact model
:func:`dengue.pipeline.run_stage1` deploys live, so the historical view and
today's live forecast are directly comparable. Rows are kept only where the
target week already has an observed actual, so the app never has to render a
"predicted" map for a week that hasn't happened yet.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable

import pandas as pd

from dengue import config
from dengue.eval.backtest import Fold, ModelLike, rolling_origin
from dengue.models import ForecastModel
from dengue.utils.io import read_panel, write_artifact
from dengue.utils.logging import get_logger

log = get_logger(__name__)

#: When this platform was actually built -- see the module docstring.
HISTORY_START: pd.Period = pd.Period("2026-06-01", freq=config.WEEK_FREQ)
HISTORY_END: pd.Period = pd.Period("2026-08-31", freq=config.WEEK_FREQ)


def _production_model_factory() -> Callable[[], ForecastModel]:
    """The exact Stage 1 model :func:`dengue.pipeline.run_stage1` deploys live.

    Loading the GA-tuned hyperparameters here (rather than hardcoding
    defaults) is what keeps the historical view honest against "what does the
    live app actually show today" -- the two would silently diverge the next
    time ``make tune`` finds new weights otherwise.
    """
    from dengue.models.baseline import SeasonalNaive
    from dengue.models.lgbm_quantile import LGBMQuantile
    from dengue.tuning.runner import load_tuned_params

    tuned = load_tuned_params("lgbm_quantile")
    params = tuned["params"] if tuned else None

    def factory() -> ForecastModel:
        try:
            return LGBMQuantile(horizons=config.HORIZONS, params=params)
        except Exception:  # - one bad origin must not abort the whole window
            return SeasonalNaive()

    return factory


def build_history_predictions(
    panel: pd.DataFrame, *, model: ModelLike | None = None
) -> pd.DataFrame:
    """Predicted-vs-actual rows for every weekly origin in the build window.

    Returns
    -------
    pandas.DataFrame
        Columns: ``district_id``, ``iso_week`` (the forecast origin),
        ``target_week``, ``horizon``, ``q0.1``/``q0.5``/``q0.9``,
        ``actual_cases``, ``population``, ``predicted_incidence_per_100k``,
        ``actual_incidence_per_100k``. Empty if the panel does not yet reach
        :data:`HISTORY_START`.
    """
    weeks = pd.PeriodIndex(sorted(panel["iso_week"].unique()), freq=config.WEEK_FREQ)
    if weeks.empty or weeks.max() < HISTORY_START:
        log.warning(
            "history: panel's latest week (%s) is before the build window "
            "starts (%s); nothing to build",
            weeks.max() if not weeks.empty else None,
            HISTORY_START,
        )
        return pd.DataFrame()

    end = min(HISTORY_END, weeks.max())
    fold = Fold(name="history", train_end=HISTORY_START - 1, eval_start=HISTORY_START, eval_end=end)

    predictions = rolling_origin(
        model or _production_model_factory(),
        panel,
        horizons=config.HORIZONS,
        folds=[fold],
        stride=1,
    )
    if predictions.empty:
        return predictions

    # The join against real outcomes is what turns a bare forecast into a
    # "predicted vs. actual" comparison -- and an inner join is deliberate:
    # a target week that hasn't happened yet (origins near the end of the
    # window, at horizon 3-4) simply has no row here, rather than a row with
    # a blank actual the UI would have to special-case.
    actuals = panel[["district_id", "iso_week", "cases", "population"]].rename(
        columns={"iso_week": "target_week", "cases": "actual_cases"}
    )
    joined = predictions.merge(actuals, on=["district_id", "target_week"], how="inner")
    joined["predicted_incidence_per_100k"] = (
        joined["q0.5"].astype("float64") / joined["population"].astype("float64") * 100_000.0
    )
    joined["actual_incidence_per_100k"] = (
        joined["actual_cases"].astype("float64") / joined["population"].astype("float64") * 100_000.0
    )

    log.info(
        "history: %d predicted-vs-actual rows, origins=[%s .. %s], model=%s",
        len(joined),
        joined["iso_week"].min(),
        joined["iso_week"].max(),
        joined["model"].iloc[0] if "model" in joined else "?",
    )
    return joined


def main(argv: list[str] | None = None) -> pd.DataFrame:
    """Build and cache the predicted-vs-actual historical artifact."""
    parser = argparse.ArgumentParser(
        description="Build the app's predicted-vs-actual historical view "
        f"({HISTORY_START} to {HISTORY_END})."
    )
    parser.add_argument(
        "--synthetic", action="store_true", help="Use the synthetic panel (fully offline)."
    )
    args = parser.parse_args(argv)

    config.ensure_dirs()

    if args.synthetic or not config.PANEL_PATH.exists():
        from dengue.utils.synthetic import make_synthetic_panel

        panel = make_synthetic_panel(n_weeks=260)
    else:
        panel = read_panel()

    result = build_history_predictions(panel)
    write_artifact(result, "predictions_history")
    return result


if __name__ == "__main__":
    main()
