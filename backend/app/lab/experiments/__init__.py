"""
Laboratory experiment registry.
"""

from __future__ import annotations

from app.lab.experiments.base import ExperimentDefinition
from app.lab.experiments.pk_ward import PK_WARD_EXPERIMENT
from app.lab.experiments.titration import TITRATION_BENCH_EXPERIMENT

_EXPERIMENTS: dict[str, ExperimentDefinition] = {
    PK_WARD_EXPERIMENT.id: PK_WARD_EXPERIMENT,
    TITRATION_BENCH_EXPERIMENT.id: TITRATION_BENCH_EXPERIMENT,
}


def list_experiments() -> list[ExperimentDefinition]:
    """Return all registered laboratory experiment definitions."""
    return list(_EXPERIMENTS.values())


def get_experiment(experiment_id: str) -> ExperimentDefinition:
    """Retrieve an experiment definition by id. Raises KeyError if unknown."""
    if experiment_id not in _EXPERIMENTS:
        raise KeyError(f"Unknown experiment: {experiment_id!r}. Available: {list(_EXPERIMENTS)}")
    return _EXPERIMENTS[experiment_id]


__all__ = [
    "ExperimentDefinition",
    "PK_WARD_EXPERIMENT",
    "TITRATION_BENCH_EXPERIMENT",
    "get_experiment",
    "list_experiments",
]
