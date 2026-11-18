"""
Specification package for Simly Orbis.
Implements the declarative experiment format per Section 10.
"""

from app.specs.loader import (
    SpecLoadError,
    load_all_specs,
    load_and_validate_spec,
    load_raw_spec,
)
from app.specs.schema import (
    ExperimentSpec,
    RuleSpec,
    StepSpec,
)
from app.specs.validator import (
    SpecValidationError,
    ValidationReport,
    validate_spec_data,
)

__all__ = [
    "ExperimentSpec",
    "RuleSpec",
    "SpecLoadError",
    "SpecValidationError",
    "StepSpec",
    "ValidationReport",
    "load_all_specs",
    "load_and_validate_spec",
    "load_raw_spec",
    "validate_spec_data",
]
