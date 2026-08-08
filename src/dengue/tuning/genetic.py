"""A generic, model-agnostic genetic algorithm engine.

Genome representation
----------------------
A genome is a flat ``dict[str, int | float]``, described by a
:class:`ParameterSpace` of :class:`GeneSpec` entries -- one spec per
hyperparameter, each carrying its own type (``int`` / ``float`` /
``float_log``) and bounds. This is generic across genome *meaning*: the same
engine drives both LightGBM hyperparameter search and ensemble-weight search
in :mod:`dengue.tuning.search_spaces` -- only the space and the fitness
function change.

Operators, and why each was chosen
-----------------------------------
**Tournament selection** (``k=3``), not roulette-wheel. A genome that makes a
model error out gets a large sentinel penalty fitness (see
:mod:`dengue.tuning.fitness`), and roulette selection would let one such
outlier distort selection probability for the whole population. Tournament
selection only needs a fitness *ordering*, so it is unaffected by how large
the penalty is.

**Uniform crossover**, for every gene type uniformly. Blending two integer
genes (``num_leaves``) produces an intermediate value that needs rounding
anyway, and blending a log-scale gene (``learning_rate``) in linear space
biases toward the larger operand. Uniform crossover -- each gene inherited
independently from one parent or the other -- sidesteps both problems with
one rule that is correct for every gene kind.

**Mutation strategy tied to gene kind**: Gaussian perturbation for continuous
genes, Gaussian-in-log-space for log-scale genes (so mutation isn't dominated
by the top of the range), a local "step" perturbation for integer genes with
wide ranges, and a full random "reset" for genes whose range is small enough
that a step would degenerate into a reset anyway.

**Linearly-annealed mutation rate** (default 0.3 -> 0.1 across generations).
With a necessarily small generation budget (an expensive genome's fitness
evaluation is a real backtest), there is no time for a self-adapting
schedule to be worth its own complexity; more exploration early, more local
refinement late is the right amount of sophistication.

**Elitism + early stopping + a hard wall-clock cap.** Elites are carried
forward with their fitness cached, not re-evaluated. Early stopping is a
plateau detector (``patience`` generations without ``min_delta`` relative
improvement). The wall-clock cap is the actual safety net: measured
per-generation cost varies with ordinary machine load, so an evaluation-count
budget alone is not trustworthy under time pressure -- the cap stops the run
after the current (completed) generation regardless of the other criteria.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import numpy as np

from dengue import config
from dengue.utils.logging import get_logger

log = get_logger(__name__)

Genome = dict[str, "int | float"]

#: A fitness function: genome -> scalar, lower is better. MUST NOT raise --
#: see fitness.py for why a failing genome should return a sentinel instead.
FitnessFn = Callable[[Genome], float]


@dataclass(frozen=True)
class GeneSpec:
    """One tunable parameter.

    Attributes
    ----------
    name:
        Key in the genome dict; also the key the decoded parameter takes.
    kind:
        ``"int"`` -- integer, uniform initial sampling, step or reset mutation.
        ``"float"`` -- continuous, uniform initial sampling, Gaussian mutation.
        ``"float_log"`` -- continuous, log-uniform initial sampling, mutated
        in log space. Use for parameters like ``learning_rate`` that are
        naturally reasoned about multiplicatively.
    low, high:
        Inclusive bounds.
    mutation:
        Override the default mutation strategy for ``kind``. ``"reset"`` --
        a full random redraw -- is normally only worth choosing explicitly
        for an ``int`` gene whose range is small enough that a local step
        would degenerate into a reset anyway.
    """

    name: str
    kind: Literal["int", "float", "float_log"]
    low: float
    high: float
    mutation: Literal["step", "gaussian", "gaussian_log", "reset"] | None = None

    def __post_init__(self) -> None:
        if self.low >= self.high:
            raise ValueError(
                f"GeneSpec {self.name!r}: low ({self.low}) must be < high ({self.high})"
            )
        if self.kind == "float_log" and self.low <= 0:
            raise ValueError(f"GeneSpec {self.name!r}: float_log genes must have low > 0")

    @property
    def default_mutation(self) -> str:
        if self.mutation is not None:
            return self.mutation
        return {"int": "step", "float": "gaussian", "float_log": "gaussian_log"}[self.kind]

    def sample(self, rng: np.random.Generator) -> int | float:
        """Uniform (or log-uniform) initial sample within bounds."""
        if self.kind == "int":
            return int(rng.integers(int(self.low), int(self.high) + 1))
        if self.kind == "float_log":
            lo, hi = np.log10(self.low), np.log10(self.high)
            return float(10.0 ** rng.uniform(lo, hi))
        return float(rng.uniform(self.low, self.high))

    def clip(self, value: int | float) -> int | float:
        """Enforce bounds and dtype."""
        clipped = min(max(value, self.low), self.high)
        return int(round(clipped)) if self.kind == "int" else float(clipped)

    def mutate(self, value: int | float, rng: np.random.Generator) -> int | float:
        """One mutation draw, strategy chosen by :attr:`default_mutation`."""
        strategy = self.default_mutation
        span = self.high - self.low

        if strategy == "reset":
            return self.sample(rng)
        if strategy == "step":
            step = round(float(rng.uniform(-0.15, 0.15)) * span)
            return self.clip(value + step)
        if strategy == "gaussian":
            return self.clip(value + rng.normal(0.0, 0.1 * span))
        if strategy == "gaussian_log":
            log_value = np.log10(max(value, self.low))
            log_span = np.log10(self.high) - np.log10(self.low)
            mutated_log = log_value + rng.normal(0.0, 0.1 * log_span)
            return self.clip(float(10.0**mutated_log))
        raise ValueError(f"Unknown mutation strategy {strategy!r}")  # pragma: no cover


@dataclass(frozen=True)
class ParameterSpace:
    """A named collection of genes defining one genome's search space."""

    genes: tuple[GeneSpec, ...]

    def __post_init__(self) -> None:
        names = [g.name for g in self.genes]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate gene names in ParameterSpace: {names}")

    def sample(self, rng: np.random.Generator) -> Genome:
        return {g.name: g.sample(rng) for g in self.genes}

    def clip(self, genome: Genome) -> Genome:
        return {g.name: g.clip(genome[g.name]) for g in self.genes}

    def by_name(self) -> dict[str, GeneSpec]:
        return {g.name: g for g in self.genes}


@dataclass(frozen=True)
class GAConfig:
    """Genetic algorithm hyperparameters. See module docstring for rationale."""

    population_size: int = 8
    generations: int = 5
    elitism: int = 2
    tournament_size: int = 3
    crossover_prob: float = 0.7
    mutation_prob_start: float = 0.3
    mutation_prob_end: float = 0.1
    seed: int = config.RANDOM_SEED
    max_wall_seconds: float | None = 1200.0
    patience: int = 2
    min_delta: float = 0.005

    def __post_init__(self) -> None:
        if self.population_size < 2:
            raise ValueError("population_size must be >= 2")
        if self.elitism >= self.population_size:
            raise ValueError("elitism must be smaller than population_size")
        if self.tournament_size < 1 or self.tournament_size > self.population_size:
            raise ValueError("tournament_size must be in [1, population_size]")

    def mutation_prob(self, generation: int) -> float:
        """Linear anneal from ``mutation_prob_start`` to ``mutation_prob_end``."""
        if self.generations <= 1:
            return self.mutation_prob_start
        t = generation / (self.generations - 1)
        return self.mutation_prob_start + (self.mutation_prob_end - self.mutation_prob_start) * t


@dataclass(frozen=True)
class Individual:
    genome: Genome
    fitness: float


@dataclass(frozen=True)
class GAResult:
    """Outcome of a full GA run.

    Attributes
    ----------
    best:
        The fittest individual found.
    history:
        One row per generation: ``{"generation", "best", "mean", "worst",
        "elapsed_s"}``.
    stopped_reason:
        Why the run ended.
    """

    best: Individual
    history: tuple[dict[str, float], ...]
    stopped_reason: Literal["generations_exhausted", "early_stopping", "wall_clock"]


class GeneticAlgorithm:
    """Evolve a population of genomes against a fitness function.

    Parameters
    ----------
    space:
        The genome's :class:`ParameterSpace`.
    fitness_fn:
        Scores a genome; lower is better. Must not raise -- a genome that
        cannot be evaluated should return a large sentinel value instead (see
        :mod:`dengue.tuning.fitness`).
    cfg:
        Algorithm hyperparameters.
    """

    def __init__(
        self, space: ParameterSpace, fitness_fn: FitnessFn, cfg: GAConfig | None = None
    ) -> None:
        self.space = space
        self.fitness_fn = fitness_fn
        self.cfg = cfg or GAConfig()
        self._rng = np.random.default_rng(self.cfg.seed)

    def _evaluate(self, genomes: list[Genome]) -> list[Individual]:
        return [Individual(g, self.fitness_fn(g)) for g in genomes]

    def _tournament_select(self, population: list[Individual]) -> Individual:
        contenders_idx = self._rng.choice(
            len(population), size=self.cfg.tournament_size, replace=False
        )
        contenders = [population[i] for i in contenders_idx]
        return min(contenders, key=lambda ind: ind.fitness)

    def _crossover(self, parent_a: Genome, parent_b: Genome) -> Genome:
        if self._rng.uniform() > self.cfg.crossover_prob:
            return dict(parent_a if self._rng.uniform() < 0.5 else parent_b)
        child: Genome = {}
        for name in parent_a:
            child[name] = parent_a[name] if self._rng.uniform() < 0.5 else parent_b[name]
        return child

    def _mutate(self, genome: Genome, mutation_prob: float) -> Genome:
        specs = self.space.by_name()
        mutated = dict(genome)
        for name, spec in specs.items():
            if self._rng.uniform() < mutation_prob:
                mutated[name] = spec.mutate(mutated[name], self._rng)
        return mutated

    def run(self) -> GAResult:
        """Run the full evolutionary loop and return the best genome found."""
        cfg = self.cfg
        started = time.perf_counter()

        initial_genomes = [self.space.sample(self._rng) for _ in range(cfg.population_size)]
        population = self._evaluate(initial_genomes)
        history: list[dict[str, float]] = []
        best_ever = min(population, key=lambda ind: ind.fitness)
        generations_without_improvement = 0
        stopped_reason: str = "generations_exhausted"

        for generation in range(cfg.generations):
            gen_started = time.perf_counter()

            fitnesses = [ind.fitness for ind in population]
            history.append(
                {
                    "generation": float(generation),
                    "best": float(min(fitnesses)),
                    "mean": float(np.mean(fitnesses)),
                    "worst": float(max(fitnesses)),
                    "elapsed_s": time.perf_counter() - started,
                }
            )
            log.info(
                "tuning: gen %d/%d  best=%.4f  mean=%.4f  elapsed=%.0fs",
                generation + 1,
                cfg.generations,
                history[-1]["best"],
                history[-1]["mean"],
                history[-1]["elapsed_s"],
            )

            wall_elapsed = time.perf_counter() - started
            if cfg.max_wall_seconds is not None and wall_elapsed >= cfg.max_wall_seconds:
                stopped_reason = "wall_clock"
                log.warning(
                    "tuning: wall-clock cap (%.0fs) reached after generation %d; stopping",
                    cfg.max_wall_seconds,
                    generation + 1,
                )
                break

            gen_best = min(population, key=lambda ind: ind.fitness)
            improvement = (best_ever.fitness - gen_best.fitness) / max(abs(best_ever.fitness), 1e-9)
            if gen_best.fitness < best_ever.fitness:
                best_ever = gen_best
            if improvement >= cfg.min_delta:
                generations_without_improvement = 0
            else:
                generations_without_improvement += 1
            if generations_without_improvement >= cfg.patience and generation > 0:
                stopped_reason = "early_stopping"
                log.info(
                    "tuning: no improvement >= %.1f%% for %d generations; stopping early",
                    cfg.min_delta * 100,
                    cfg.patience,
                )
                break

            # Elitism: carry the top performers forward untouched.
            elites = sorted(population, key=lambda ind: ind.fitness)[: cfg.elitism]

            children_genomes: list[Genome] = []
            while len(children_genomes) < cfg.population_size - cfg.elitism:
                parent_a = self._tournament_select(population)
                parent_b = self._tournament_select(population)
                child = self._crossover(parent_a.genome, parent_b.genome)
                child = self._mutate(child, cfg.mutation_prob(generation))
                child = self.space.clip(child)
                children_genomes.append(child)

            children = self._evaluate(children_genomes)
            population = elites + children

            gen_elapsed = time.perf_counter() - gen_started
            log.debug("tuning: generation %d took %.1fs", generation + 1, gen_elapsed)

        final_best = min([*population, best_ever], key=lambda ind: ind.fitness)
        log.info(
            "tuning: done  best_fitness=%.4f  stopped=%s  total=%.0fs",
            final_best.fitness,
            stopped_reason,
            time.perf_counter() - started,
        )
        return GAResult(best=final_best, history=tuple(history), stopped_reason=stopped_reason)
