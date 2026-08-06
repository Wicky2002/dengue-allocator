"""Strict rolling-origin backtesting.

Why this file matters more than the models
------------------------------------------
The single most common way a published dengue-forecasting result turns out to be
wrong is evaluation leakage, and it usually enters one of three ways:

1. **Random train/test splits.** A random split puts week *t+1* in train and week
   *t* in test. With autocorrelation as strong as dengue's, that alone can halve
   the apparent error. This module never shuffles: splits are strictly temporal.
2. **Feature statistics fitted over the whole series.** Scalers, target encodings
   and imputation means computed before splitting leak test-period information
   into training. Here, models receive a *raw panel truncated at the forecast
   origin* and build their own features inside :meth:`fit`, so there is no
   pre-computed matrix to leak through.
3. **Refitting on data after the origin.** At origin *t*, the model may see weeks
   ``<= t`` and nothing else. :func:`rolling_origin` enforces this by
   construction: it slices the panel to ``iso_week <= origin`` and hands over
   only that.

The window is **expanding**, not sliding: at each origin the model trains on all
history up to that point, which is what an operational system deployed at that
date would have had.

Default folds
-------------
==========  ===========================  ==========================
fold        training data                evaluated origins
==========  ===========================  ==========================
``val``     everything through 2023      2024
``test``    everything through 2024      2025 and 2026 year-to-date
==========  ===========================  ==========================

Model selection uses ``val``. ``test`` is touched once, at the end. Panels that
do not span these dates (the synthetic default, or colmozzie's 2009-2014 window)
fall back to proportional 60/20/20 splits by week -- still strictly chronological
-- with a warning, so the harness stays usable on any panel.
"""

from __future__ import annotations

import copy
import itertools
import time
from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from dengue import config
from dengue.eval.metrics import LOWER_IS_BETTER, evaluate_predictions
from dengue.models import ForecastModel
from dengue.utils.logging import get_logger

log = get_logger(__name__)

ModelLike = ForecastModel | Callable[[], ForecastModel]


@dataclass(frozen=True)
class Fold:
    """One rolling-origin evaluation fold.

    Attributes
    ----------
    name:
        Fold label, e.g. ``"val"`` or ``"test"``.
    train_end:
        Last week available for training at the fold's *first* origin. The window
        expands from here as origins advance.
    eval_start, eval_end:
        First and last forecast origin in this fold, inclusive.

    Notes
    -----
    ``train_end < eval_start <= eval_end`` is an invariant, checked in
    :meth:`validate`. It is what guarantees no training week is ever also an
    evaluated origin.
    """

    name: str
    train_end: pd.Period
    eval_start: pd.Period
    eval_end: pd.Period

    def validate(self) -> None:
        """Raise if the fold's temporal ordering is invalid."""
        if self.train_end >= self.eval_start:
            raise ValueError(
                f"Fold {self.name!r}: train_end ({self.train_end}) must precede "
                f"eval_start ({self.eval_start}); otherwise training data overlaps "
                "the evaluation period."
            )
        if self.eval_start > self.eval_end:
            raise ValueError(
                f"Fold {self.name!r}: eval_start ({self.eval_start}) is after "
                f"eval_end ({self.eval_end})"
            )

    def origins(self, weeks: pd.PeriodIndex, stride: int = 1) -> list[pd.Period]:
        """Forecast origins in this fold, taken from the panel's own weeks."""
        selected = [w for w in weeks if self.eval_start <= w <= self.eval_end]
        return selected[::stride]


def default_folds(panel: pd.DataFrame) -> list[Fold]:
    """Build the default val/test folds, adapting if the panel is too short.

    Returns folds in chronological order.
    """
    weeks = pd.PeriodIndex(sorted(panel["iso_week"].unique()), freq=config.WEEK_FREQ)
    if len(weeks) < 20:
        raise ValueError(f"Panel has only {len(weeks)} weeks; too short to backtest")

    train_end = pd.Period(config.TRAIN_END_DEFAULT, freq=config.WEEK_FREQ)
    val_end = pd.Period(config.VAL_END_DEFAULT, freq=config.WEEK_FREQ)

    covers_defaults = weeks[0] < train_end and weeks[-1] > val_end
    if covers_defaults:
        folds = [
            Fold("val", train_end=train_end, eval_start=train_end + 1, eval_end=val_end),
            Fold("test", train_end=val_end, eval_start=val_end + 1, eval_end=weeks[-1]),
        ]
    else:
        # Proportional 60/20/20 by week, still strictly chronological.
        n = len(weeks)
        i_train, i_val = int(n * 0.6), int(n * 0.8)
        log.warning(
            "backtest: panel spans %s..%s and does not cover the default "
            "2023/2024/2025 boundaries; falling back to chronological 60/20/20 splits",
            weeks[0],
            weeks[-1],
        )
        folds = [
            Fold("val", weeks[i_train - 1], weeks[i_train], weeks[i_val - 1]),
            Fold("test", weeks[i_val - 1], weeks[i_val], weeks[-1]),
        ]

    for fold in folds:
        fold.validate()
    validate_fold_ordering(folds)
    return folds


def validate_fold_ordering(folds: list[Fold]) -> None:
    """Assert folds are chronological, non-overlapping, and leakage-free.

    Raises
    ------
    ValueError
        If any fold is internally inconsistent, if evaluation windows overlap, or
        if a later fold's training data would not have been available.
    """
    if not folds:
        raise ValueError("No folds supplied")

    for fold in folds:
        fold.validate()

    for earlier, later in itertools.pairwise(folds):
        if later.eval_start <= earlier.eval_end:
            raise ValueError(
                f"Folds {earlier.name!r} and {later.name!r} have overlapping "
                f"evaluation windows: {earlier.eval_end} >= {later.eval_start}"
            )
        if later.train_end < earlier.train_end:
            raise ValueError(
                f"Fold {later.name!r} trains on less data than the earlier fold "
                f"{earlier.name!r}; the window must expand, not shrink."
            )


def _instantiate(model: ModelLike) -> ForecastModel:
    """Return a fresh, unfitted model from an instance or a factory."""
    if callable(model) and not isinstance(model, ForecastModel):
        return model()
    return copy.deepcopy(model)


def rolling_origin(
    model: ModelLike,
    panel: pd.DataFrame,
    horizons: tuple[int, ...] = config.HORIZONS,
    folds: list[Fold] | None = None,
    *,
    stride: int = 4,
    min_train_weeks: int = 52,
) -> pd.DataFrame:
    """Run a strict expanding-window rolling-origin backtest.

    At every origin the model is refitted from scratch on ``iso_week <= origin``
    and asked for each horizon. Refitting (rather than fitting once and rolling
    forward) is the honest simulation of redeployment, and it is why ``stride``
    exists: refitting SARIMA at all 25 districts for every one of ~100 origins is
    the dominant cost.

    Parameters
    ----------
    model:
        A :class:`~dengue.models.ForecastModel` instance (deep-copied before each
        fit) or a zero-argument factory returning one.
    panel:
        District-week panel conforming to :data:`dengue.config.PANEL_DTYPES`.
    horizons:
        Forecast horizons in weeks.
    folds:
        Evaluation folds. Defaults to :func:`default_folds`.
    stride:
        Weeks between successive origins. 1 evaluates every week (most rigorous,
        slowest); the default 4 evaluates monthly, which for a 2-4 week horizon
        keeps successive forecasts nearly independent while cutting runtime
        roughly fourfold.
    min_train_weeks:
        Minimum weeks of history required before an origin is evaluated. One year
        is the floor for anything that estimates annual seasonality.

    Returns
    -------
    pandas.DataFrame
        Long frame of predictions: ``model``, ``fold``, ``district_id``,
        ``iso_week`` (origin), ``target_week``, ``horizon``, and the quantile
        columns. Empty if no origin had enough history.
    """
    folds = folds or default_folds(panel)
    validate_fold_ordering(folds)

    panel = panel.sort_values(["district_id", "iso_week"]).reset_index(drop=True)
    weeks = pd.PeriodIndex(sorted(panel["iso_week"].unique()), freq=config.WEEK_FREQ)

    probe = _instantiate(model)
    model_name = probe.name

    collected: list[pd.DataFrame] = []
    n_fits = 0
    started = time.perf_counter()

    for fold in folds:
        origins = fold.origins(weeks, stride=stride)
        log.info(
            "backtest[%s] fold=%s  origins=%d  stride=%d  window=[%s .. %s]",
            model_name,
            fold.name,
            len(origins),
            stride,
            fold.eval_start,
            fold.eval_end,
        )

        for origin in origins:
            # THE leakage boundary: everything at or before the origin, nothing after.
            train = panel[panel["iso_week"] <= origin]
            n_train_weeks = train["iso_week"].nunique()
            if n_train_weeks < min_train_weeks:
                log.debug(
                    "backtest: skipping origin %s (%d train weeks < %d)",
                    origin,
                    n_train_weeks,
                    min_train_weeks,
                )
                continue

            fitted = _instantiate(model)
            try:
                fitted.fit(train)
            except Exception as exc:  # - one bad origin must not abort the run
                log.error("backtest: fit failed at origin %s: %s", origin, exc)
                continue
            n_fits += 1

            for horizon in horizons:
                try:
                    predictions = fitted.predict(train, horizon)
                except NotImplementedError:
                    raise
                except Exception as exc:
                    log.error(
                        "backtest: predict failed at origin %s, horizon %d: %s",
                        origin,
                        horizon,
                        exc,
                    )
                    continue

                if predictions.empty:
                    continue
                predictions = predictions.copy()
                predictions["model"] = model_name
                predictions["fold"] = fold.name
                collected.append(predictions)

    elapsed = time.perf_counter() - started
    if not collected:
        log.warning("backtest[%s]: produced no predictions", model_name)
        return pd.DataFrame()

    result = pd.concat(collected, ignore_index=True)
    log.info(
        "backtest[%s]: %d predictions from %d fits in %.1fs",
        model_name,
        len(result),
        n_fits,
        elapsed,
    )
    return result


def score_predictions(
    predictions: pd.DataFrame,
    panel: pd.DataFrame,
    *,
    by_fold: bool = True,
    top_k: int = 6,
) -> pd.DataFrame:
    """Turn backtest predictions into a tidy model x horizon x metric frame.

    Returns
    -------
    pandas.DataFrame
        Columns ``model``, ``fold`` (if ``by_fold``), ``horizon``, ``metric``,
        ``value``.
    """
    if predictions.empty:
        return pd.DataFrame(columns=["model", "fold", "horizon", "metric", "value"])

    group_columns = ["model", "horizon"]
    if by_fold and "fold" in predictions.columns:
        group_columns.insert(1, "fold")

    rows: list[dict[str, object]] = []
    for keys, group in predictions.groupby(group_columns, observed=True):
        keys = keys if isinstance(keys, tuple) else (keys,)
        metrics = evaluate_predictions(group, panel, top_k=top_k)
        for metric, value in metrics.items():
            row = dict(zip(group_columns, keys, strict=True))
            row["metric"] = metric
            row["value"] = value
            rows.append(row)

    return pd.DataFrame(rows)


def compare_models(
    models: dict[str, ModelLike],
    panel: pd.DataFrame,
    horizons: tuple[int, ...] = config.HORIZONS,
    folds: list[Fold] | None = None,
    *,
    stride: int = 4,
    top_k: int = 6,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Backtest several models and return ``(scores, predictions)``.

    Models that raise :class:`NotImplementedError` (the STGNN stub) are skipped
    with a note rather than aborting the comparison.
    """
    folds = folds or default_folds(panel)

    all_predictions: list[pd.DataFrame] = []
    for label, model in models.items():
        log.info("=" * 72)
        log.info("backtest: %s", label)
        try:
            predictions = rolling_origin(
                model, panel, horizons=horizons, folds=folds, stride=stride
            )
        except NotImplementedError as exc:
            log.warning("backtest: skipping %s -- not implemented (%s)", label, exc)
            continue

        if predictions.empty:
            log.warning("backtest: %s produced no predictions", label)
            continue
        predictions["model"] = label
        all_predictions.append(predictions)

    if not all_predictions:
        return pd.DataFrame(), pd.DataFrame()

    predictions = pd.concat(all_predictions, ignore_index=True)
    scores = score_predictions(predictions, panel, top_k=top_k)
    return scores, predictions


# --------------------------------------------------------------------------
# Presentation
# --------------------------------------------------------------------------

#: Metrics shown in the headline comparison table, in order.
HEADLINE_METRICS = (
    "pinball_mean",
    "mae",
    "mape",
    "coverage_80",
    "interval_width",
    "high_risk_recall",
    "mean_lead_time_weeks",
)


def comparison_table(
    scores: pd.DataFrame,
    *,
    fold: str | None = "test",
    metrics: tuple[str, ...] = HEADLINE_METRICS,
) -> pd.DataFrame:
    """Pivot tidy scores into a ``model x horizon`` table for display."""
    if scores.empty:
        return pd.DataFrame()

    frame = scores
    if fold is not None and "fold" in frame.columns:
        available = set(frame["fold"].unique())
        if fold in available:
            frame = frame[frame["fold"] == fold]
        else:
            log.warning("comparison_table: fold %r not found; showing all folds", fold)

    frame = frame[frame["metric"].isin(metrics)]
    if frame.empty:
        return pd.DataFrame()

    table = frame.pivot_table(
        index=["model", "horizon"], columns="metric", values="value", observed=True
    )
    ordered = [m for m in metrics if m in table.columns]
    return table[ordered].reset_index()


def print_comparison(
    scores: pd.DataFrame,
    *,
    fold: str | None = "test",
    title: str = "Stage 1 forecast comparison",
) -> pd.DataFrame:
    """Pretty-print the comparison table to stdout and return it.

    Marks the best model per (horizon, metric) with ``*``, using
    :data:`dengue.eval.metrics.LOWER_IS_BETTER` to know which direction wins.
    Coverage is judged by absolute distance from nominal (0.80), since
    over-covering is a failure too.
    """
    table = comparison_table(scores, fold=fold, metrics=HEADLINE_METRICS)
    if table.empty:
        print("\n(no scores to display)\n")
        return table

    display = table.copy()
    metric_columns = [c for c in display.columns if c not in ("model", "horizon")]

    # Identify the winner per (horizon, metric) before formatting to strings.
    winners: dict[tuple[int, str], int] = {}
    for horizon, group in display.groupby("horizon", observed=True):
        for metric in metric_columns:
            series = group[metric].dropna()
            if series.empty:
                continue
            if metric == "coverage_80":
                best_index = (series - config.PI_NOMINAL_COVERAGE).abs().idxmin()
            elif LOWER_IS_BETTER.get(metric, True):
                best_index = series.idxmin()
            else:
                best_index = series.idxmax()
            winners[(horizon, metric)] = best_index

    for column in metric_columns:
        formatted = []
        for index, value in display[column].items():
            if pd.isna(value):
                formatted.append("--")
                continue
            text = f"{value:,.3f}" if abs(value) < 1000 else f"{value:,.0f}"
            if winners.get((display.at[index, "horizon"], column)) == index:
                text += "*"
            formatted.append(text)
        display[column] = formatted

    fold_label = fold or "all folds"
    header = f"  {title}  (fold: {fold_label})  "
    line = "=" * max(len(header), 100)

    print()
    print(line)
    print(header)
    print(line)
    try:
        print(display.to_markdown(index=False))
    except ImportError:  # pragma: no cover - tabulate is a pinned dependency
        print(display.to_string(index=False))
    print(line)
    print("  * = best for that horizon.  pinball_mean is the headline metric (lower is better).")
    print(f"  coverage_80 target = {config.PI_NOMINAL_COVERAGE:.2f}; further from target is worse.")
    print("  mean_lead_time_weeks: mean warning before a district's high-risk onset.")
    print(line)
    print()

    return table


def summarise_best(scores: pd.DataFrame, *, fold: str = "test") -> pd.DataFrame:
    """Return the best model per horizon by mean pinball loss."""
    if scores.empty:
        return pd.DataFrame()

    frame = scores[scores["metric"] == "pinball_mean"]
    if "fold" in frame.columns and fold in set(frame["fold"].unique()):
        frame = frame[frame["fold"] == fold]
    if frame.empty:
        return pd.DataFrame()

    best = frame.loc[frame.groupby("horizon", observed=True)["value"].idxmin()]
    return (
        best[["horizon", "model", "value"]]
        .rename(columns={"value": "pinball_mean"})
        .sort_values("horizon")
        .reset_index(drop=True)
    )


# --------------------------------------------------------------------------
# CLI: `make baseline`
# --------------------------------------------------------------------------


def build_default_models() -> dict[str, ModelLike]:
    """The Stage 1 model roster evaluated by ``make baseline``.

    Factories rather than instances, so every backtest origin gets a genuinely
    fresh model with no state carried across folds.
    """
    from dengue.models.baseline import SarimaBaseline, SeasonalNaive
    from dengue.models.lgbm_quantile import LGBMQuantile

    return {
        "seasonal_naive": SeasonalNaive,
        "sarima": SarimaBaseline,
        "lgbm_quantile": LGBMQuantile,
    }


def write_app_artifacts(
    predictions: pd.DataFrame, scores: pd.DataFrame, panel: pd.DataFrame
) -> None:
    """Write the cached artifacts the Streamlit app reads.

    The app must never call a model at request time, so everything it renders is
    materialised here: the latest forecast per district, the score table, and the
    recent observed panel.
    """
    from dengue.utils.io import write_artifact

    write_artifact(scores, "scores")
    write_artifact(predictions, "predictions")

    if not predictions.empty:
        # Latest available forecast per (district, horizon), for the risk table.
        latest_origin = predictions["iso_week"].max()
        latest = predictions[predictions["iso_week"] == latest_origin].copy()

        populations = panel.drop_duplicates("district_id").set_index("district_id")["population"]
        latest["population"] = latest["district_id"].map(populations)
        latest["incidence_per_100k"] = (
            latest["q0.5"].astype("float64") / latest["population"].astype("float64") * 100_000.0
        )
        latest = latest.sort_values(["horizon", "incidence_per_100k"], ascending=[True, False])
        write_artifact(latest, "district_risk")

    recent_weeks = sorted(panel["iso_week"].unique())[-104:]
    write_artifact(panel[panel["iso_week"].isin(recent_weeks)], "panel_recent")


def main(argv: list[str] | None = None) -> pd.DataFrame:
    """Train the Stage 1 baselines, print the comparison table, cache artifacts."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Rolling-origin backtest of the Stage 1 forecasting models."
    )
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Use the synthetic panel (fully offline). Implied when no panel exists.",
    )
    parser.add_argument(
        "--stride", type=int, default=4, help="Weeks between forecast origins (default: 4)."
    )
    parser.add_argument(
        "--horizons",
        type=int,
        nargs="+",
        default=list(config.HORIZONS),
        help="Forecast horizons in weeks (default: 2 3 4).",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        help="Subset of models to run (default: all).",
    )
    parser.add_argument(
        "--n-weeks",
        type=int,
        default=520,
        help="Weeks to generate when using the synthetic panel (default: 520).",
    )
    parser.add_argument(
        "--fold", default="test", help="Fold to display in the headline table (default: test)."
    )
    args = parser.parse_args(argv)

    config.ensure_dirs()

    # ---- panel --------------------------------------------------------
    from dengue.utils.io import read_panel
    from dengue.utils.synthetic import make_synthetic_panel

    if args.synthetic or not config.PANEL_PATH.exists():
        if not args.synthetic:
            log.warning(
                "backtest: no panel at %s; using the SYNTHETIC panel. "
                "Run `make panel` to build from real sources.",
                config.PANEL_PATH,
            )
        panel = make_synthetic_panel(n_weeks=args.n_weeks)
        panel_source = "SYNTHETIC (simulated data -- not observations)"
    else:
        panel = read_panel()
        panel_source = str(config.PANEL_PATH)

    log.info(
        "backtest: panel source=%s  rows=%d  districts=%d  weeks=[%s .. %s]",
        panel_source,
        len(panel),
        panel["district_id"].nunique(),
        panel["iso_week"].min(),
        panel["iso_week"].max(),
    )

    # ---- models -------------------------------------------------------
    models = build_default_models()
    if args.models:
        unknown = set(args.models) - set(models)
        if unknown:
            raise SystemExit(f"Unknown model(s): {sorted(unknown)}. Available: {sorted(models)}")
        models = {k: v for k, v in models.items() if k in args.models}

    folds = default_folds(panel)
    log.info("backtest: folds -> %s", [(f.name, str(f.eval_start), str(f.eval_end)) for f in folds])

    scores, predictions = compare_models(
        models,
        panel,
        horizons=tuple(args.horizons),
        folds=folds,
        stride=args.stride,
    )

    if scores.empty:
        log.error("backtest: no scores produced")
        return scores

    # ---- report -------------------------------------------------------
    for fold in folds:
        print_comparison(
            scores,
            fold=fold.name,
            title=f"Stage 1 forecast comparison [{panel_source}]",
        )

    best = summarise_best(scores, fold=args.fold)
    if not best.empty:
        print(f"Best model per horizon on '{args.fold}' (mean pinball loss):")
        print(best.to_string(index=False))
        print()

    write_app_artifacts(predictions, scores, panel)
    return scores


if __name__ == "__main__":  # pragma: no cover
    main()
