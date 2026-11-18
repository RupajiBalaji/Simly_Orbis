"""
Experiment Spec Loader for Simly Orbis.
Loads and caches experiment specifications from YAML and JSON files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import yaml

from app.specs.schema import ExperimentSpec
from app.specs.validator import ValidationReport, validate_spec_data


class SpecLoadError(Exception):
    """Raised when a spec file cannot be read or parsed."""
    pass


def load_raw_spec(file_path: Path | str) -> dict[str, Any]:
    """Parse a JSON or YAML spec file into a raw dictionary."""
    path = Path(file_path)
    if not path.is_file():
        raise SpecLoadError(f"Spec file not found: {path}")

    try:
        content = path.read_text(encoding="utf-8")
        if path.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(content)
        elif path.suffix == ".json":
            data = json.loads(content)
        else:
            # Attempt JSON first, then YAML
            try:
                data = json.loads(content)
            except Exception:
                data = yaml.safe_load(content)
    except Exception as exc:
        raise SpecLoadError(f"Error parsing spec file {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise SpecLoadError(f"Spec file {path} did not parse into a top-level dictionary")

    return data


def load_and_validate_spec(file_path: Path | str) -> tuple[ExperimentSpec | None, ValidationReport]:
    """Load and validate an experiment spec file."""
    raw_data = load_raw_spec(file_path)
    report = validate_spec_data(raw_data)
    return report.spec, report


def load_all_specs(specs_dir: Path | str) -> dict[str, ExperimentSpec]:
    """Load and validate all .json and .yaml/.yml specs in a directory."""
    dir_path = Path(specs_dir)
    if not dir_path.is_dir():
        return {}

    specs: dict[str, ExperimentSpec] = {}
    candidate_files = sorted(list(dir_path.glob("*.json")) + list(dir_path.glob("*.yaml")) + list(dir_path.glob("*.yml")))

    for fpath in candidate_files:
        spec, report = load_and_validate_spec(fpath)
        if not report.valid or spec is None:
            err_summary = "; ".join(str(e) for e in report.errors)
            raise SpecLoadError(f"Invalid spec file {fpath.name}: {err_summary}")
        specs[spec.id] = spec

    return specs
