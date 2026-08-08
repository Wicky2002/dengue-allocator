"""Hyperparameter search for Stage 1 models: a hand-rolled genetic algorithm.

Two genome types live here.

**Hyperparameter genomes** (:mod:`dengue.tuning.search_spaces`) tune
:class:`~dengue.models.lgbm_quantile.LGBMQuantile`'s LightGBM parameters
against the existing rolling-origin harness in :mod:`dengue.eval.backtest`.
Each fitness evaluation is a real (small) backtest, so this is the expensive
genome -- see :mod:`dengue.tuning.runner` for the wall-clock budget.

**Ensemble-weight genomes** blend the three already-implemented models'
predictions with evolved weights. Each base model is backtested once; every
subsequent genome evaluation is then pure vectorised arithmetic over the
cached predictions, so this genome is close to free and can run with a much
larger population and generation count.

Why a hand-rolled GA rather than a library (Optuna, DEAP, scikit-optimize):
this project has repeatedly chosen to implement a small amount of code over
adding a dependency where the alternative is heavy or only loosely needed --
see the custom RData reader in ``ingest/colmozzie.py`` instead of
``pyreadr``/``rpy2``, or ``geopandas`` kept fully optional. A real GA
(selection, crossover, mutation, elitism) is a few hundred lines of numpy and
keeps that pattern.
"""
