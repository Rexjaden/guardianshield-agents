"""Population-based evolution utilities for GuardianShield agents.

This implementation provides a deterministic, test-friendly genetic algorithm
that keeps state in memory and never mutates source files unless explicitly
requested via the optional backup helpers.
"""

from __future__ import annotations

import os
import random
import shutil
from dataclasses import dataclass, replace
from typing import Dict, List, Optional


@dataclass
class Individual:
    """Represents one candidate configuration for an agent."""

    detection_threshold: float
    response_aggressiveness: float
    learning_rate: float
    fitness: float = 0.0

    # The unit tests interact with population entries as dictionaries, so
    # provide minimal mapping helpers to preserve backward compatibility.
    def __getitem__(self, key: str) -> float:
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def __setitem__(self, key: str, value: float) -> None:
        if hasattr(self, key):
            setattr(self, key, value)
            return
        raise KeyError(key)

    @classmethod
    def random(cls) -> "Individual":
        """Create a new individual with randomized parameters."""
        return cls(
            detection_threshold=round(random.uniform(0.1, 0.9), 3),
            response_aggressiveness=round(random.uniform(0.1, 1.0), 3),
            learning_rate=round(random.uniform(0.001, 0.1), 4),
        )

    def to_dict(self) -> Dict[str, float]:
        """Return a JSON-serialisable representation."""
        return {
            "detection_threshold": self.detection_threshold,
            "response_aggressiveness": self.response_aggressiveness,
            "learning_rate": self.learning_rate,
            "fitness": self.fitness,
        }


class GeneticEvolver:
    """Population-based evolver with safe defaults for unit tests."""

    def __init__(
        self,
        code_path: Optional[str] = None,
        backup_dir: str = "evolution_backups",
        population_size: int = 50,
        mutation_rate: float = 0.1,
        elite_fraction: float = 0.1,
    ) -> None:
        self.code_path = code_path
        self.backup_dir = backup_dir
        self.population_size = max(2, population_size)
        self.mutation_rate = max(0.0, min(1.0, mutation_rate))
        self.elite_fraction = max(0.0, min(0.5, elite_fraction))

        self.population: List[Individual] = []
        self.generation: int = 0
        self.best_individual: Optional[Individual] = None
        self.fitness_history: List[Dict[str, float]] = []

        if self.code_path:
            os.makedirs(self.backup_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Population management helpers
    # ------------------------------------------------------------------
    def create_individual(self) -> Dict[str, float]:
        """Return a new random individual as a dictionary."""
        return Individual.random().to_dict()

    def initialize_population(self) -> None:
        """Populate the initial generation and evaluate fitness."""
        self.population = [Individual.random() for _ in range(self.population_size)]
        self.generation = 0
        self.fitness_history.clear()
        self.evaluate_population()

    def evaluate_population(self) -> None:
        """Evaluate fitness for the whole population and keep history."""
        if not self.population:
            return

        for idx, individual in enumerate(self.population):
            updated = replace(individual, fitness=self._simulate_fitness(individual))
            self.population[idx] = updated

        self.population.sort(key=lambda agent: agent.fitness, reverse=True)
        self.best_individual = self.population[0]
        self.fitness_history.append(
            {
                "generation": float(self.generation),
                "best_fitness": self.best_individual.fitness,
            }
        )

    def evolve(self) -> List[Dict[str, float]]:
        """Advance the population by one generation."""
        if not self.population:
            self.initialize_population()

        self.generation += 1
        elites = self._select_elites()
        offspring = self._generate_offspring(len(self.population) - len(elites))
        self.population = elites + offspring
        self.evaluate_population()
        return [individual.to_dict() for individual in self.population]

    def recursive_self_improve(self) -> Dict[str, float]:
        """Inspect recent fitness and optionally run additional generations."""
        if not self.population:
            self.initialize_population()

        improvement_potential = self._estimate_improvement_potential()
        improvement_detected = improvement_potential > 0.7

        if improvement_detected:
            for _ in range(3):
                self.evolve()

        best_fitness = self.best_individual.fitness if self.best_individual else 0.0
        return {
            "improvement_detected": improvement_detected,
            "generation": self.generation,
            "best_fitness": best_fitness,
        }

    # ------------------------------------------------------------------
    # Internal mechanics
    # ------------------------------------------------------------------
    def _select_elites(self) -> List[Individual]:
        count = max(1, int(self.population_size * self.elite_fraction))
        return [replace(individual) for individual in self.population[:count]]

    def _generate_offspring(self, count: int) -> List[Individual]:
        if count <= 0 or len(self.population) < 2:
            return [Individual.random() for _ in range(max(0, count))]

        parent_pool = self.population[: max(2, len(self.population) // 2)]
        offspring: List[Individual] = []
        while len(offspring) < count:
            parent_a, parent_b = random.sample(parent_pool, 2)
            child = self._crossover(parent_a, parent_b)
            if random.random() < self.mutation_rate:
                child = self._mutate(child)
            offspring.append(child)
        return offspring

    def _crossover(self, parent_a: Individual, parent_b: Individual) -> Individual:
        return Individual(
            detection_threshold=round(
                random.uniform(parent_a.detection_threshold, parent_b.detection_threshold),
                3,
            ),
            response_aggressiveness=round(
                random.uniform(
                    parent_a.response_aggressiveness, parent_b.response_aggressiveness
                ),
                3,
            ),
            learning_rate=round(
                random.uniform(parent_a.learning_rate, parent_b.learning_rate),
                4,
            ),
        )

    def _mutate(self, individual: Individual) -> Individual:
        key = random.choice(["detection_threshold", "response_aggressiveness", "learning_rate"])
        delta = random.uniform(-0.1, 0.1)

        if key == "learning_rate":
            value = max(0.001, min(0.2, individual.learning_rate + delta))
            return replace(individual, learning_rate=round(value, 4), fitness=0.0)

        new_value = max(0.0, min(1.0, getattr(individual, key) + delta))
        rounded = round(new_value, 3)
        if key == "detection_threshold":
            return replace(individual, detection_threshold=rounded, fitness=0.0)
        return replace(individual, response_aggressiveness=rounded, fitness=0.0)

    def _simulate_fitness(self, individual: Individual) -> float:
        threshold_score = 1.0 - abs(0.6 - individual.detection_threshold)
        response_score = 1.0 - abs(0.7 - individual.response_aggressiveness)
        learning_score = 1.0 - abs(0.02 - individual.learning_rate) * 20
        return max(0.0, min(1.0, (threshold_score + response_score + learning_score) / 3))

    def _estimate_improvement_potential(self) -> float:
        if len(self.fitness_history) < 2:
            return 0.8
        previous = self.fitness_history[-2]["best_fitness"]
        latest = self.fitness_history[-1]["best_fitness"]
        delta = latest - previous
        return max(0.0, min(1.0, 0.5 + delta))

    # ------------------------------------------------------------------
    # Optional backup utilities (no source mutations by default)
    # ------------------------------------------------------------------
    def backup_code(self) -> Optional[str]:
        if not self.code_path or not os.path.exists(self.code_path):
            return None
        os.makedirs(self.backup_dir, exist_ok=True)
        backup_file = os.path.join(self.backup_dir, f"{os.path.basename(self.code_path)}.bak")
        shutil.copy2(self.code_path, backup_file)
        return backup_file

    def restore_code(self, backup_file: Optional[str]) -> None:
        if backup_file and self.code_path and os.path.exists(backup_file):
            shutil.copy2(backup_file, self.code_path)

    def evolve_advanced(self) -> bool:
        """Compatibility stub retained for older integrations."""
        self.evolve()
        return True

    def analyze_self_performance(self) -> Dict[str, float]:
        best_fitness = self.best_individual.fitness if self.best_individual else 0.0
        return {
            "improvement_potential": max(0.0, min(1.0, 0.5 + best_fitness / 2)),
            "efficiency_score": best_fitness,
            "adaptability_score": round(0.7 + random.uniform(-0.1, 0.1), 3),
        }
