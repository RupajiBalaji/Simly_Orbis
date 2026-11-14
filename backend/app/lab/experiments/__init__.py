"""
Laboratory experiment registry.
"""

from __future__ import annotations

from app.lab.experiments.base import ExperimentDefinition
from app.lab.experiments.dose_lab import DOSE_LAB_EXPERIMENT
from app.lab.experiments.launch_bench import LAUNCH_BENCH_EXPERIMENT
from app.lab.experiments.pk_ward import PK_WARD_EXPERIMENT
from app.lab.experiments.titration import TITRATION_BENCH_EXPERIMENT

_EXPERIMENTS: dict[str, ExperimentDefinition] = {
    PK_WARD_EXPERIMENT.id: PK_WARD_EXPERIMENT,
    TITRATION_BENCH_EXPERIMENT.id: TITRATION_BENCH_EXPERIMENT,
    LAUNCH_BENCH_EXPERIMENT.id: LAUNCH_BENCH_EXPERIMENT,
    DOSE_LAB_EXPERIMENT.id: DOSE_LAB_EXPERIMENT,
}


def list_experiments(include_all: bool = False, district: str | None = None) -> list[ExperimentDefinition]:
    """Return registered laboratory experiment definitions."""
    if district:
        return [e for e in _EXPERIMENTS.values() if e.district == district]
    if include_all:
        return list(_EXPERIMENTS.values())
    # Keep legacy default matching pk_ward and titration_bench
    return [e for e in _EXPERIMENTS.values() if e.id in ("pk_ward", "titration_bench")]


def get_experiment(experiment_id: str) -> ExperimentDefinition:
    """Retrieve an experiment definition by id. Raises KeyError if unknown."""
    if experiment_id not in _EXPERIMENTS:
        raise KeyError(f"Unknown experiment: {experiment_id!r}. Available: {list(_EXPERIMENTS)}")
    return _EXPERIMENTS[experiment_id]


__all__ = [
    "DOSE_LAB_EXPERIMENT",
    "ExperimentDefinition",
    "LAUNCH_BENCH_EXPERIMENT",
    "PK_WARD_EXPERIMENT",
    "TITRATION_BENCH_EXPERIMENT",
    "get_experiment",
    "list_experiments",
]
