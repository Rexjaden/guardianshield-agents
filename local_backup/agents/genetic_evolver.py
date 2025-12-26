"""Non-mutating compatibility shim for the historic genetic evolver backup."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Individual:
    """Simple data container used by the legacy backup implementation."""

    detection_threshold: float
    response_aggressiveness: float
    learning_rate: float
    fitness: float = 0.0


class GeneticEvolver:
    """Lightweight proxy around the primary ``agents.genetic_evolver`` module."""

    def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - simple wrapper
        from agents.genetic_evolver import GeneticEvolver as PrimaryEvolver

        self._impl = PrimaryEvolver(*args, **kwargs)

    def __getattr__(self, name):  # pragma: no cover - forwarding helper
        return getattr(self._impl, name)


__all__ = ["Individual", "GeneticEvolver"]
