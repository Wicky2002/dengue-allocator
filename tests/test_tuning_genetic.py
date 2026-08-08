"""GA engine tests: convergence, determinism, and operator correctness.

Runs against a toy analytic fitness landscape with a known optimum -- no
model fitting, no panel data -- so this stays numpy-only and sub-second,
independent of :mod:`tests.test_tuning_fitness`, which exercises the real
``genome -> LGBMQuantile -> rolling_origin`` wiring.
"""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from dengue.tuning.genetic import GAConfig, GeneSpec, GeneticAlgorithm, Individual, ParameterSpace

#: x=3 (float), y=-2 (int), z=1 (float_log) -- one gene of each kind, chosen
#: so the optimum sits inside every gene's bounds rather than at an edge.
TOY_SPACE = ParameterSpace(
    (
        GeneSpec("x", "float", -5.0, 5.0),
        GeneSpec("y", "int", -5, 5),
        GeneSpec("z", "float_log", 0.001, 10.0),
    )
)


def _toy_fitness(genome: dict) -> float:
    return (genome["x"] - 3.0) ** 2 + (genome["y"] + 2) ** 2 + np.log10(genome["z"]) ** 2


# --------------------------------------------------------------------------
# GeneSpec / ParameterSpace
# --------------------------------------------------------------------------


def test_gene_spec_rejects_low_greater_than_high():
    with pytest.raises(ValueError, match="must be <"):
        GeneSpec("bad", "float", 5.0, 1.0)


def test_float_log_gene_rejects_non_positive_low():
    with pytest.raises(ValueError, match="float_log"):
        GeneSpec("bad", "float_log", 0.0, 1.0)


def test_int_gene_sample_and_clip_stay_integer():
    rng = np.random.default_rng(0)
    gene = GeneSpec("n", "int", 1, 10)
    for _ in range(50):
        value = gene.sample(rng)
        assert isinstance(value, int)
        assert 1 <= value <= 10
    assert gene.clip(100) == 10
    assert gene.clip(-100) == 1
    assert isinstance(gene.clip(5.6), int)


def test_float_log_gene_sample_stays_within_bounds_and_positive():
    rng = np.random.default_rng(0)
    gene = GeneSpec("lr", "float_log", 0.01, 0.2)
    samples = [gene.sample(rng) for _ in range(200)]
    assert all(0.01 <= s <= 0.2 for s in samples)
    assert all(s > 0 for s in samples)


def test_default_mutation_matches_gene_kind():
    assert GeneSpec("a", "int", 0, 1).default_mutation == "step"
    assert GeneSpec("a", "float", 0, 1).default_mutation == "gaussian"
    assert GeneSpec("a", "float_log", 0.1, 1).default_mutation == "gaussian_log"
    assert GeneSpec("a", "int", 0, 1, mutation="reset").default_mutation == "reset"


def test_parameter_space_rejects_duplicate_gene_names():
    with pytest.raises(ValueError, match="Duplicate"):
        ParameterSpace((GeneSpec("x", "float", 0, 1), GeneSpec("x", "float", 0, 1)))


def test_parameter_space_clip_respects_each_genes_dtype():
    space = ParameterSpace((GeneSpec("n", "int", 0, 10), GeneSpec("f", "float", 0.0, 1.0)))
    clipped = space.clip({"n": 3.7, "f": 5.0})
    assert clipped["n"] == 4
    assert isinstance(clipped["n"], int)
    assert clipped["f"] == 1.0


# --------------------------------------------------------------------------
# GAConfig
# --------------------------------------------------------------------------


def test_ga_config_rejects_elitism_at_or_above_population_size():
    with pytest.raises(ValueError, match="elitism"):
        GAConfig(population_size=4, elitism=4)


def test_ga_config_rejects_tournament_size_out_of_range():
    with pytest.raises(ValueError, match="tournament_size"):
        GAConfig(population_size=4, tournament_size=5)


def test_mutation_prob_anneals_linearly_from_start_to_end():
    cfg = GAConfig(generations=5, mutation_prob_start=0.3, mutation_prob_end=0.1)
    assert cfg.mutation_prob(0) == pytest.approx(0.3)
    assert cfg.mutation_prob(4) == pytest.approx(0.1)
    assert cfg.mutation_prob(2) == pytest.approx(0.2)


def test_mutation_prob_is_constant_for_a_single_generation_run():
    cfg = GAConfig(generations=1, mutation_prob_start=0.3, mutation_prob_end=0.1)
    assert cfg.mutation_prob(0) == pytest.approx(0.3)


# --------------------------------------------------------------------------
# GeneticAlgorithm: convergence, determinism, bounds
# --------------------------------------------------------------------------


def test_ga_converges_toward_the_known_optimum():
    cfg = GAConfig(population_size=24, generations=25, elitism=2, tournament_size=3, seed=7)
    ga = GeneticAlgorithm(TOY_SPACE, _toy_fitness, cfg)
    result = ga.run()

    assert result.best.fitness < 0.05
    assert result.best.genome["x"] == pytest.approx(3.0, abs=0.5)
    assert result.best.genome["y"] == -2
    assert result.best.genome["z"] == pytest.approx(1.0, rel=0.5)


def test_ga_best_fitness_never_gets_worse_across_generations():
    cfg = GAConfig(population_size=16, generations=15, seed=3)
    ga = GeneticAlgorithm(TOY_SPACE, _toy_fitness, cfg)
    result = ga.run()

    bests = [row["best"] for row in result.history]
    assert all(later <= earlier + 1e-9 for earlier, later in itertools.pairwise(bests))


def test_ga_is_deterministic_given_a_fixed_seed():
    cfg = GAConfig(population_size=10, generations=6, seed=42)
    a = GeneticAlgorithm(TOY_SPACE, _toy_fitness, cfg).run()
    b = GeneticAlgorithm(TOY_SPACE, _toy_fitness, cfg).run()

    assert a.best.genome == b.best.genome
    assert a.best.fitness == b.best.fitness
    # Compare everything except `elapsed_s`, which is real wall-clock time
    # and will never match bit-for-bit between two runs.
    a_history = [{k: v for k, v in row.items() if k != "elapsed_s"} for row in a.history]
    b_history = [{k: v for k, v in row.items() if k != "elapsed_s"} for row in b.history]
    assert a_history == b_history


def test_ga_different_seeds_can_diverge():
    cfg_a = GAConfig(population_size=6, generations=4, seed=1)
    cfg_b = GAConfig(population_size=6, generations=4, seed=2)
    a = GeneticAlgorithm(TOY_SPACE, _toy_fitness, cfg_a).run()
    b = GeneticAlgorithm(TOY_SPACE, _toy_fitness, cfg_b).run()

    # Not a strict guarantee for any RNG, but true for these two seeds on this
    # landscape -- regressing to always-identical output would mean the seed
    # is silently not threaded through every stochastic step.
    assert a.best.genome != b.best.genome or a.history != b.history


def test_ga_every_evaluated_genome_respects_bounds_and_dtype():
    seen: list[dict] = []

    def _spy_fitness(genome: dict) -> float:
        seen.append(genome)
        return _toy_fitness(genome)

    cfg = GAConfig(population_size=12, generations=8, seed=5)
    GeneticAlgorithm(TOY_SPACE, _spy_fitness, cfg).run()

    assert seen
    for genome in seen:
        assert -5.0 <= genome["x"] <= 5.0
        assert -5 <= genome["y"] <= 5
        assert isinstance(genome["y"], int)
        assert 0.001 <= genome["z"] <= 10.0


def test_ga_stops_early_on_a_flat_fitness_landscape():
    cfg = GAConfig(population_size=8, generations=50, patience=2, min_delta=0.005, seed=9)
    ga = GeneticAlgorithm(TOY_SPACE, lambda genome: 1.0, cfg)
    result = ga.run()

    assert result.stopped_reason == "early_stopping"
    assert len(result.history) < 50


def test_ga_respects_a_tight_wall_clock_cap():
    def _slow_fitness(genome: dict) -> float:
        return _toy_fitness(genome)

    cfg = GAConfig(population_size=8, generations=1000, max_wall_seconds=0.0, seed=1)
    ga = GeneticAlgorithm(TOY_SPACE, _slow_fitness, cfg)
    result = ga.run()

    assert result.stopped_reason == "wall_clock"
    assert len(result.history) == 1


def test_ga_carries_elites_forward_without_re_evaluating_them():
    calls = 0

    def _counting_fitness(genome: dict) -> float:
        nonlocal calls
        calls += 1
        return _toy_fitness(genome)

    cfg = GAConfig(population_size=10, generations=3, elitism=3, seed=1)
    GeneticAlgorithm(TOY_SPACE, _counting_fitness, cfg).run()

    # Each generation evaluates only the (population_size - elitism) children;
    # the elites are reused, not re-scored.
    max_calls = cfg.population_size + cfg.generations * (cfg.population_size - cfg.elitism)
    assert calls <= max_calls


def test_tournament_select_prefers_lower_fitness_on_average():
    cfg = GAConfig(population_size=5, tournament_size=5, seed=0)
    ga = GeneticAlgorithm(TOY_SPACE, _toy_fitness, cfg)
    population = [Individual({"x": 0, "y": 0, "z": 1}, fitness=float(i)) for i in range(5)]
    winners = [ga._tournament_select(population).fitness for _ in range(20)]
    # tournament_size == population_size means every tournament sees the
    # whole population, so the winner must always be the global best.
    assert set(winners) == {0.0}
