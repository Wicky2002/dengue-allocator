"""CLI entry point for `make tune`: python -m dengue.tuning.runner

Runs the LightGBM hyperparameter genetic search and the ensemble-weight
genetic search, confirms the LightGBM winner on the untouched ``test`` fold
(the only time this module touches ``test``), and writes the results to
:data:`dengue.config.TUNED_PARAMS_PATH`.

Both ``make baseline`` and ``dengue.pipeline`` read that file through
:func:`load_tuned_params`, which never raises -- a missing or malformed file
degrades to "use the hardcoded defaults", the exact behaviour before this
module existed, so running the tuner is optional at every point in the
pipeline.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

from dengue import config
from dengue.eval.backtest import default_folds, rolling_origin, score_predictions
from dengue.tuning.fitness import (
    FitnessConfig,
    aggregate_scores,
    base_model_predictions,
    build_search_fold,
    make_ensemble_fitness,
    make_lgbm_fitness,
    merge_base_predictions,
)
from dengue.tuning.genetic import GAConfig, GeneticAlgorithm
from dengue.tuning.search_spaces import (
    ENSEMBLE_SEARCH_SPACE,
    LGBM_SEARCH_SPACE,
    decode_ensemble_genome,
    decode_lgbm_genome,
)
from dengue.utils.logging import get_logger

log = get_logger(__name__)


def load_tuned_params(model_name: str, path: Path | None = None) -> dict[str, Any] | None:
    """Load one model's tuned entry. Never raises.

    Returns
    -------
    dict or None
        ``None`` if the file is missing, malformed, or does not contain
        ``model_name`` -- logged, not raised, so a caller can always fall
        back to hardcoded defaults.
    """
    path = path or config.TUNED_PARAMS_PATH
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("tuning: could not read %s (%s); using defaults", path, exc)
        return None
    entry = payload.get(model_name)
    if entry is None:
        log.debug("tuning: no tuned entry for %r in %s", model_name, path)
    return entry


def _write_entry(model_name: str, entry: dict[str, Any], path: Path | None = None) -> None:
    """Read-merge-write so tuning one model never clobbers another's entry."""
    path = path or config.TUNED_PARAMS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {}
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            log.warning("tuning: existing %s was unreadable; overwriting", path)
    payload[model_name] = entry
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log.info("tuning: wrote %s -> %s", model_name, path)


def run_lgbm_search(
    panel: pd.DataFrame,
    search_fold,
    *,
    ga_cfg: GAConfig,
    fitness_cfg: FitnessConfig,
    horizons: tuple[int, ...],
    stride: int,
) -> tuple[dict[str, Any], dict[str, float]]:
    """Run the GA and return ``(decoded_params, search_fitness_summary)``."""
    fitness_fn = make_lgbm_fitness(
        panel, search_fold, horizons=horizons, stride=stride, fitness_cfg=fitness_cfg
    )
    ga = GeneticAlgorithm(LGBM_SEARCH_SPACE, fitness_fn, ga_cfg)
    result = ga.run()
    params = decode_lgbm_genome(result.best.genome)
    summary = {"fitness": result.best.fitness, "stopped_reason": result.stopped_reason}
    log.info("tuning: LGBM search winner  fitness=%.4f  params=%s", result.best.fitness, params)
    return params, summary


def confirm_lgbm(
    panel: pd.DataFrame, params: dict[str, Any], folds, *, horizons: tuple[int, ...], stride: int
) -> dict[str, dict[str, float]]:
    """One confirmation backtest of the winning params on val AND test.

    The only place this module touches ``test``.
    """
    from dengue.models.lgbm_quantile import LGBMQuantile

    model = LGBMQuantile(horizons=horizons, params=params)
    predictions = rolling_origin(model, panel, horizons=horizons, folds=folds, stride=stride)
    scores = score_predictions(predictions, panel)

    confirmation: dict[str, dict[str, float]] = {}
    for fold in folds:
        pinball_mean, coverage_80 = aggregate_scores(scores, fold=fold.name)
        confirmation[fold.name] = {"pinball_mean": pinball_mean, "coverage_80": coverage_80}
    log.info("tuning: LGBM confirmation  %s", confirmation)
    return confirmation


def run_ensemble_search(
    panel: pd.DataFrame,
    val_fold,
    *,
    ga_cfg: GAConfig,
    fitness_cfg: FitnessConfig,
    horizons: tuple[int, ...],
    stride: int,
) -> tuple[dict[str, float], dict[str, float]]:
    """Run the ensemble-weight GA over the full ``val`` fold.

    Cheap enough (no refitting per genome) to search the whole fold rather
    than the reduced search_fold used for the LightGBM hyperparameter search.
    """
    predictions = base_model_predictions(panel, val_fold, horizons=horizons, stride=stride)
    merged = merge_base_predictions(predictions)
    if merged.empty:
        raise RuntimeError(
            "No overlapping predictions across the three base models on the val fold; "
            "cannot search ensemble weights."
        )

    fitness_fn = make_ensemble_fitness(panel, merged, fitness_cfg=fitness_cfg)
    ga = GeneticAlgorithm(ENSEMBLE_SEARCH_SPACE, fitness_fn, ga_cfg)
    result = ga.run()
    weights = decode_ensemble_genome(result.best.genome)
    summary = {"fitness": result.best.fitness, "stopped_reason": result.stopped_reason}
    log.info(
        "tuning: ensemble search winner  fitness=%.4f  weights=%s", result.best.fitness, weights
    )
    return weights, summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Genetic-algorithm hyperparameter and ensemble-weight search for Stage 1."
    )
    parser.add_argument(
        "--synthetic", action="store_true", help="Use the synthetic panel (offline)."
    )
    parser.add_argument("--n-weeks", type=int, default=520, help="Synthetic panel length.")
    parser.add_argument(
        "--horizons", type=int, nargs="+", default=list(config.HORIZONS), help="Forecast horizons."
    )
    parser.add_argument(
        "--population", type=int, default=8, help="GA population size (LGBM search)."
    )
    parser.add_argument("--generations", type=int, default=5, help="GA generations (LGBM search).")
    parser.add_argument("--elitism", type=int, default=2)
    parser.add_argument("--tournament-size", type=int, default=3)
    parser.add_argument(
        "--search-origins", type=int, default=2, help="Origins in the LGBM search fold."
    )
    parser.add_argument("--search-stride", type=int, default=4)
    parser.add_argument("--coverage-penalty-weight", type=float, default=2.0)
    parser.add_argument("--coverage-tolerance", type=float, default=0.03)
    parser.add_argument(
        "--max-minutes",
        type=float,
        default=20.0,
        help="Hard wall-clock cap on the LGBM search loop.",
    )
    parser.add_argument("--seed", type=int, default=config.RANDOM_SEED)
    parser.add_argument(
        "--skip-ensemble",
        action="store_true",
        help="Skip the ensemble-weight genome (LGBM search only).",
    )
    parser.add_argument(
        "--ensemble-population",
        type=int,
        default=40,
        help="Ensemble GA population (cheap, can be large).",
    )
    parser.add_argument("--ensemble-generations", type=int, default=25)
    parser.add_argument("--out", type=str, default=None, help="Override output path.")
    args = parser.parse_args(argv)

    config.ensure_dirs()
    started = time.perf_counter()

    from dengue.utils.io import read_panel
    from dengue.utils.synthetic import make_synthetic_panel

    if args.synthetic or not config.PANEL_PATH.exists():
        panel = make_synthetic_panel(n_weeks=args.n_weeks)
        log.info("tuning: using SYNTHETIC panel")
    else:
        panel = read_panel()

    horizons = tuple(args.horizons)
    folds = default_folds(panel)
    val = next(f for f in folds if f.name == "val")
    weeks = pd.PeriodIndex(sorted(panel["iso_week"].unique()), freq=config.WEEK_FREQ)
    search_fold = build_search_fold(
        val, weeks, n_origins=args.search_origins, stride=args.search_stride
    )
    log.info("tuning: search fold = %s", search_fold)

    fitness_cfg = FitnessConfig(
        coverage_penalty_weight=args.coverage_penalty_weight,
        coverage_tolerance=args.coverage_tolerance,
    )

    # ---- LightGBM hyperparameter search ---------------------------------
    lgbm_ga_cfg = GAConfig(
        population_size=args.population,
        generations=args.generations,
        elitism=args.elitism,
        tournament_size=args.tournament_size,
        seed=args.seed,
        max_wall_seconds=args.max_minutes * 60.0,
    )
    lgbm_params, lgbm_search_summary = run_lgbm_search(
        panel,
        search_fold,
        ga_cfg=lgbm_ga_cfg,
        fitness_cfg=fitness_cfg,
        horizons=horizons,
        stride=args.search_stride,
    )
    lgbm_confirmation = confirm_lgbm(
        panel, lgbm_params, folds, horizons=horizons, stride=args.search_stride
    )

    out_path = Path(args.out) if args.out else config.TUNED_PARAMS_PATH
    _write_entry(
        "lgbm_quantile",
        {
            "generated_at": pd.Timestamp.utcnow().isoformat(),
            "ga_config": lgbm_ga_cfg.__dict__,
            "search_fitness": lgbm_search_summary,
            "params": lgbm_params,
            "confirmation": lgbm_confirmation,
        },
        path=out_path,
    )

    # ---- Ensemble-weight search (cheap, approved add-on) -----------------
    if not args.skip_ensemble:
        ensemble_ga_cfg = GAConfig(
            population_size=args.ensemble_population,
            generations=args.ensemble_generations,
            elitism=max(2, args.ensemble_population // 10),
            tournament_size=3,
            seed=args.seed,
            max_wall_seconds=300.0,
        )
        weights, ensemble_summary = run_ensemble_search(
            panel,
            val,
            ga_cfg=ensemble_ga_cfg,
            fitness_cfg=fitness_cfg,
            horizons=horizons,
            stride=args.search_stride,
        )
        _write_entry(
            "ensemble",
            {
                "generated_at": pd.Timestamp.utcnow().isoformat(),
                "ga_config": ensemble_ga_cfg.__dict__,
                "search_fitness": ensemble_summary,
                "weights": weights,
            },
            path=out_path,
        )

    elapsed = time.perf_counter() - started
    print()
    print("=" * 78)
    print(f"  Tuning complete in {elapsed / 60:.1f} min")
    print("=" * 78)
    print(f"  LGBM params: {lgbm_params}")
    print(f"  LGBM confirmation (val/test, untouched by search): {lgbm_confirmation}")
    if not args.skip_ensemble:
        print(f"  Ensemble weights: {weights}")
    print(f"  Written to: {out_path}")
    print("=" * 78)


if __name__ == "__main__":  # pragma: no cover
    main()
