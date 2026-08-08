"""Search spaces and genome decoders for the two tunable Stage 1 genomes.

LightGBM hyperparameters
-------------------------
Mirrors :data:`dengue.models.lgbm_quantile.DEFAULT_PARAMS`'s keys exactly, so
decoding a genome is a direct dict merge with no translation layer to keep in
sync.

``n_estimators`` is capped at **50-200**, not the current default's 400.
LightGBM fit cost is empirically linear in this parameter (~1.65s + 0.084s x
n_estimators per rolling-origin origin, measured on this project's synthetic
panel), and that cap is what keeps a real evolutionary search tractable in
minutes rather than hours -- see :mod:`dengue.tuning.runner` for the full
budget accounting.

Ensemble weights
-----------------
A second, much cheaper genome: blend the three already-implemented models'
quantile predictions with evolved weights, normalised to a simplex at decode
time. Because a weighted average of already-sorted quantiles stays sorted, no
monotonicity repair is needed on the blended result.
"""

from __future__ import annotations

from typing import Any

from dengue.tuning.genetic import GeneSpec, Genome, ParameterSpace

LGBM_SEARCH_SPACE = ParameterSpace(
    (
        GeneSpec("n_estimators", "int", 50, 200, mutation="step"),
        GeneSpec("learning_rate", "float_log", 0.01, 0.2),
        GeneSpec("num_leaves", "int", 15, 63, mutation="step"),
        GeneSpec("max_depth", "int", 3, 10, mutation="step"),
        GeneSpec("min_child_samples", "int", 10, 100, mutation="step"),
        GeneSpec("subsample", "float", 0.5, 1.0),
        GeneSpec("colsample_bytree", "float", 0.5, 1.0),
        GeneSpec("reg_alpha", "float", 0.0, 2.0),
        GeneSpec("reg_lambda", "float", 0.0, 5.0),
    )
)


def decode_lgbm_genome(genome: Genome) -> dict[str, Any]:
    """Genome -> a ``params`` dict for ``LGBMQuantile(params=...)``.

    ``subsample_freq=1`` is fixed rather than tuned: it only has an effect
    paired with ``subsample < 1.0`` (which is in the search space) and adding
    it as a tenth gene would not meaningfully expand what the search can
    express.
    """
    return {**genome, "subsample_freq": 1}


ENSEMBLE_SEARCH_SPACE = ParameterSpace(
    (
        GeneSpec("w_naive", "float", 0.0, 1.0),
        GeneSpec("w_sarima", "float", 0.0, 1.0),
        GeneSpec("w_lgbm", "float", 0.0, 1.0),
    )
)

#: Model keys the ensemble genome blends, in the order its genes are decoded.
ENSEMBLE_MODEL_KEYS = ("w_naive", "w_sarima", "w_lgbm")


def decode_ensemble_genome(genome: Genome) -> dict[str, float]:
    """Genome -> normalised blend weights summing to 1.

    A genome that samples to all-zero (astronomically unlikely but not
    impossible, and cheap to guard) decodes to equal weights rather than
    dividing by zero.
    """
    total = sum(genome.values())
    if total <= 1e-9:
        return dict.fromkeys(genome, 1.0 / len(genome))
    return {k: v / total for k, v in genome.items()}
