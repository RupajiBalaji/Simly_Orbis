"""
Laboratory experiment registry.
Supports both legacy static experiment definitions and declarative JSON/YAML specs
via the SPEC_RUNTIME configuration flag.
"""

from __future__ import annotations

from pathlib import Path
from app.config import settings
from app.lab.experiments.base import ExperimentDefinition
from app.lab.experiments.dose_lab import DOSE_LAB_EXPERIMENT
from app.lab.experiments.kinetics_bench import KINETICS_BENCH_EXPERIMENT
from app.lab.experiments.launch_bench import LAUNCH_BENCH_EXPERIMENT
from app.lab.experiments.pk_ward import PK_WARD_EXPERIMENT
from app.lab.experiments.titration import TITRATION_BENCH_EXPERIMENT

_EXPERIMENTS: dict[str, ExperimentDefinition] = {
    PK_WARD_EXPERIMENT.id: PK_WARD_EXPERIMENT,
    TITRATION_BENCH_EXPERIMENT.id: TITRATION_BENCH_EXPERIMENT,
    LAUNCH_BENCH_EXPERIMENT.id: LAUNCH_BENCH_EXPERIMENT,
    DOSE_LAB_EXPERIMENT.id: DOSE_LAB_EXPERIMENT,
    KINETICS_BENCH_EXPERIMENT.id: KINETICS_BENCH_EXPERIMENT,
}

_SPECS_CACHE: dict[str, ExperimentDefinition] = {}

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
SPECS_DIR = REPO_ROOT / "specs"


def _get_spec_experiment(experiment_id: str) -> ExperimentDefinition | None:
    """Attempt to load and adapt a declarative spec for an experiment."""
    if experiment_id in _SPECS_CACHE:
        return _SPECS_CACHE[experiment_id]

    spec_file = None
    for ext in (".json", ".yaml", ".yml"):
        candidate = SPECS_DIR / f"{experiment_id}{ext}"
        if candidate.is_file():
            spec_file = candidate
            break

    if spec_file is None:
        return None

    from app.specs.loader import load_and_validate_spec
    from app.specs.adapter import spec_to_experiment_definition

    spec, report = load_and_validate_spec(spec_file)
    if not report.valid or spec is None or not spec.approved:
        # Unapproved specs are never served to students/users (Section 10.3)
        return None

    legacy_base = _EXPERIMENTS.get(experiment_id)
    base_app = legacy_base.apparatus if legacy_base else {}
    base_inv = legacy_base.inventory if legacy_base else {}
    base_ppe = legacy_base.required_ppe if legacy_base else None

    adapted = spec_to_experiment_definition(
        spec,
        base_apparatus=base_app,
        base_inventory=base_inv,
        required_ppe=base_ppe,
    )
    _SPECS_CACHE[experiment_id] = adapted
    return adapted


def list_experiments(include_all: bool = False, district: str | None = None) -> list[ExperimentDefinition]:
    """Return registered laboratory experiment definitions."""
    exps: list[ExperimentDefinition] = []
    for exp_id, legacy_exp in _EXPERIMENTS.items():
        if getattr(settings, "spec_runtime", False):
            spec_exp = _get_spec_experiment(exp_id)
            exps.append(spec_exp if spec_exp is not None else legacy_exp)
        else:
            exps.append(legacy_exp)

    if district:
        return [e for e in exps if e.district == district]
    if include_all:
        return exps
    # Keep legacy default matching pk_ward and titration_bench
    return [e for e in exps if e.id in ("pk_ward", "titration_bench")]


def get_experiment(experiment_id: str) -> ExperimentDefinition:
    """Retrieve an experiment definition by id. Raises KeyError if unknown."""
    if getattr(settings, "spec_runtime", False):
        spec_exp = _get_spec_experiment(experiment_id)
        if spec_exp is not None:
            return spec_exp

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
