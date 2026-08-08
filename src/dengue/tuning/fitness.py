"""Fitness functions: genome -> scalar, via the existing leakage-safe harness.

Every fitness function here calls :func:`dengue.eval.backtest.rolling_origin`
and :func:`dengue.eval.backtest.score_predictions` **unmodified** -- the
whole point of this project's leakage-safety work is that models never see
data past their forecast origin, and a tuning system that bypassed the
harness to go faster would quietly undermine that guarantee for exactly the
model that ends up shipped.

Fitness always evaluates against a slice of the ``val`` fold, never
``test``. ``test`` is touched exactly once, by the confirmation run in
:mod:`dengue.tuning.runner`, after the search has already picked a winner --
mirroring how :mod:`dengue.eval.backtest` already documents ``val`` for
selection and ``test`` touched once at the end.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from dengue import config
from dengue.eval.backtest import Fold, rolling_origin, score_predictions
from dengue.models import PREDICTION_COLUMNS, QUANTILE_COLUMNS, enforce_quantile_monotonicity
from dengue.tuning.genetic import FitnessFn, Genome
from dengue.tuning.search_spaces import decode_ensemble_genome, decode_lgbm_genome
from dengue.utils.logging import get_logger

log = get_logger(__name__)


@dataclass(frozen=True)
class FitnessConfig:
    """Composite-fitness parameters. See :func:`composite_fitness`."""

    coverage_penalty_weight: float = 2.0
    coverage_tolerance: float = 0.03
    penalty_value: float = 1e6


def build_search_fold(
    val: Fold, weeks: pd.PeriodIndex, *, n_origins: int = 2, stride: int = 4
) -> Fold:
    """A cheap, still-genuinely-rolling proxy of ``val`` for use during search.

    Covers only the most recent ``n_origins`` origins (at ``stride``) of
    ``val`` rather than the whole fold, so each fitness evaluation stays
    cheap. Still >= 2 origins -- a real (if short) rolling-origin backtest,
    not a single snapshot.
    """
    candidates = [w for w in weeks if val.eval_start <= w <= val.eval_end]
    if len(candidates) < n_origins:
        raise ValueError(
            f"val fold only has {len(candidates)} origins at this stride; "
            f"need at least {n_origins} for a search fold"
        )
    tail = candidates[-(n_origins * stride) :][::stride][-n_origins:]
    return Fold(name="search", train_end=val.train_end, eval_start=tail[0], eval_end=tail[-1])


def aggregate_scores(scores: pd.DataFrame, *, fold: str | None = None) -> tuple[float, float]:
    """Mean ``pinball_mean`` and mean ``coverage_80`` across horizons.

    Parameters
    ----------
    scores:
        Tidy output of :func:`~dengue.eval.backtest.score_predictions`.
    fold:
        Restrict to one fold if the ``fold`` column is present and this is
        given; otherwise aggregate whatever is there.
    """
    frame = scores
    if fold is not None and "fold" in frame.columns:
        frame = frame[frame["fold"] == fold]

    pinball = frame[frame["metric"] == "pinball_mean"]["value"]
    coverage = frame[frame["metric"] == "coverage_80"]["value"]

    pinball_mean = float(pinball.mean()) if len(pinball) else float("nan")
    coverage_mean = float(coverage.mean()) if len(coverage) else float("nan")
    return pinball_mean, coverage_mean


def composite_fitness(pinball_mean: float, coverage_80: float, cfg: FitnessConfig) -> float:
    """``pinball_mean`` with a multiplicative penalty for miscalibration.

    ``pinball_mean * (1 + weight * max(0, |coverage_80 - 0.80| - tolerance))``

    A pure ``pinball_mean`` objective is only an indirect signal for interval
    width -- a genome can shave pinball loss by tightening intervals in ways
    that make coverage worse, which is precisely LightGBM's documented
    weakness in this project (empirical coverage ~0.65-0.68 against the 0.80
    nominal target). The penalty stays in the same units as ``pinball_mean``
    (no invented cases-per-coverage-point exchange rate), is zero inside a
    +/-``tolerance`` dead-band around nominal coverage so it doesn't fight a
    well-calibrated genome over noise, and scales with how badly miscalibrated
    the genome already is. ``coverage_penalty_weight=0`` recovers plain
    pinball loss.
    """
    if not np.isfinite(pinball_mean):
        return cfg.penalty_value
    gap = max(0.0, abs(coverage_80 - config.PI_NOMINAL_COVERAGE) - cfg.coverage_tolerance)
    return pinball_mean * (1.0 + cfg.coverage_penalty_weight * gap)


def make_lgbm_fitness(
    panel: pd.DataFrame,
    search_fold: Fold,
    *,
    horizons: tuple[int, ...] = config.HORIZONS,
    stride: int = 4,
    fitness_cfg: FitnessConfig | None = None,
) -> FitnessFn:
    """Build a fitness function for the LightGBM hyperparameter genome.

    Returns
    -------
    callable
        ``genome -> float``. Never raises: a genome that makes LightGBM error
        out (an invalid parameter combination, a degenerate fit) is caught
        and scored at ``fitness_cfg.penalty_value`` so tournament selection
        simply discards it rather than the search crashing.
    """
    from dengue.models.lgbm_quantile import LGBMQuantile

    fitness_cfg = fitness_cfg or FitnessConfig()

    def _fitness(genome: Genome) -> float:
        try:
            model = LGBMQuantile(horizons=horizons, params=decode_lgbm_genome(genome))
            predictions = rolling_origin(
                model, panel, horizons=horizons, folds=[search_fold], stride=stride
            )
            if predictions.empty:
                return fitness_cfg.penalty_value
            scores = score_predictions(predictions, panel)
            pinball_mean, coverage_80 = aggregate_scores(scores, fold="search")
            return composite_fitness(pinball_mean, coverage_80, fitness_cfg)
        except Exception as exc:  # - a bad genome must not kill the run
            log.warning("tuning: genome failed (%s): %s", genome, exc)
            return fitness_cfg.penalty_value

    return _fitness


# --------------------------------------------------------------------------
# Ensemble-weight genome
# --------------------------------------------------------------------------


def base_model_predictions(
    panel: pd.DataFrame, fold: Fold, *, horizons: tuple[int, ...] = config.HORIZONS, stride: int = 4
) -> dict[str, pd.DataFrame]:
    """Backtest the three existing models once each, for the ensemble genome.

    Every subsequent ensemble-genome evaluation reuses these frames -- pure
    vectorised arithmetic, no refitting -- which is what makes the
    ensemble-weight search close to free compared to the LightGBM
    hyperparameter search.
    """
    from dengue.models.baseline import SarimaBaseline, SeasonalNaive
    from dengue.models.lgbm_quantile import LGBMQuantile

    roster = {"w_naive": SeasonalNaive, "w_sarima": SarimaBaseline, "w_lgbm": LGBMQuantile}
    predictions: dict[str, pd.DataFrame] = {}
    for key, factory in roster.items():
        frame = rolling_origin(factory, panel, horizons=horizons, folds=[fold], stride=stride)
        if frame.empty:
            log.warning("tuning: base model %s produced no predictions on the search fold", key)
        predictions[key] = frame
    return predictions


_JOIN_KEYS = ("district_id", "iso_week", "target_week", "horizon")


def merge_base_predictions(base_predictions: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Inner-join the three base models' predictions on their common rows.

    A district-origin-horizon combination that any one model failed to
    produce (e.g. a district too short for SARIMA) is dropped from ensemble
    evaluation entirely, rather than guessing a fill value.
    """
    frames = [
        df[[*_JOIN_KEYS, *QUANTILE_COLUMNS]].rename(
            columns={q: f"{q}__{key}" for q in QUANTILE_COLUMNS}
        )
        for key, df in base_predictions.items()
        if not df.empty
    ]
    if len(frames) < 2:
        return pd.DataFrame(columns=list(PREDICTION_COLUMNS))

    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on=list(_JOIN_KEYS), how="inner")
    return merged


def blend_predictions(merged: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    """Weighted combination of the merged base-model quantiles.

    A weighted average of already-sorted quantiles is itself sorted in exact
    arithmetic; :func:`~dengue.models.enforce_quantile_monotonicity` is
    applied anyway as cheap insurance against floating-point noise.
    """
    if merged.empty:
        return merged.assign(**{q: pd.Series(dtype="float64") for q in QUANTILE_COLUMNS})[
            list(PREDICTION_COLUMNS)
        ]

    out = merged[list(_JOIN_KEYS)].copy()
    for q in QUANTILE_COLUMNS:
        out[q] = sum(weights[key] * merged[f"{q}__{key}"] for key in weights)
    return enforce_quantile_monotonicity(out)[list(PREDICTION_COLUMNS)]


def make_ensemble_fitness(
    panel: pd.DataFrame,
    merged_base_predictions: pd.DataFrame,
    *,
    fitness_cfg: FitnessConfig | None = None,
) -> FitnessFn:
    """Build a fitness function for the ensemble-weight genome.

    Parameters
    ----------
    merged_base_predictions:
        Output of :func:`merge_base_predictions`, computed once by the
        caller and shared across every genome evaluation.
    """
    from dengue.eval.metrics import evaluate_predictions

    fitness_cfg = fitness_cfg or FitnessConfig()

    def _fitness(genome: Genome) -> float:
        try:
            weights = decode_ensemble_genome(genome)
            blended = blend_predictions(merged_base_predictions, weights)
            if blended.empty:
                return fitness_cfg.penalty_value
            metrics = evaluate_predictions(blended, panel)
            pinball_mean = metrics.get("pinball_mean", float("nan"))
            coverage_80 = metrics.get("coverage_80", float("nan"))
            return composite_fitness(pinball_mean, coverage_80, fitness_cfg)
        except Exception as exc:
            log.warning("tuning: ensemble genome failed (%s): %s", genome, exc)
            return fitness_cfg.penalty_value

    return _fitness
