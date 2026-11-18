"""
Experiment Spec Validator for Simly Orbis.
Validates spec files and dictionaries against Section 10 rejection rules:
1. Unknown fields
2. Duplicate rule IDs
3. Actions with no handler
4. Directives not in schema
5. Parameter bounds outside engine limits
6. Constants without provenance
7. Hard-coded strings / missing i18n
8. Pharma specs outside adult ranges
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from pydantic import ValidationError

from app.lab.models import ActionType
from app.specs.schema import (
    ADULT_RANGES,
    ENGINE_LIMITS,
    ExperimentSpec,
    SUPPORTED_ENGINES,
    VALID_DIRECTIVE_TYPES,
    VALID_EFFECT_NAMES,
)


@dataclass
class SpecValidationError:
    """A single validation error naming the exact field path."""
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


@dataclass
class ValidationReport:
    """Overall validation outcome for an experiment spec."""
    spec_id: str | None
    valid: bool
    errors: list[SpecValidationError]
    spec: ExperimentSpec | None = None


def _format_pydantic_loc(loc: tuple[Any, ...]) -> str:
    """Format a Pydantic loc tuple into a standard path string like steps[0].allowed_actions[1]."""
    parts: list[str] = []
    for item in loc:
        if isinstance(item, int):
            if parts:
                parts[-1] = f"{parts[-1]}[{item}]"
            else:
                parts.append(f"[{item}]")
        else:
            parts.append(str(item))
    return ".".join(parts)


def validate_spec_data(raw_data: dict[str, Any]) -> ValidationReport:
    """Validate a parsed spec dictionary against all Section 10 rules."""
    spec_id = raw_data.get("id") if isinstance(raw_data, dict) else None
    errors: list[SpecValidationError] = []

    # 1. Pydantic schema validation (catches unknown fields, missing required fields, type mismatches)
    try:
        spec = ExperimentSpec.model_validate(raw_data)
    except ValidationError as exc:
        for err in exc.errors():
            path = _format_pydantic_loc(err["loc"])
            errors.append(SpecValidationError(path=path, message=err["msg"]))
        return ValidationReport(spec_id=spec_id, valid=False, errors=errors, spec=None)

    # 2. Duplicate rule IDs
    seen_rules: dict[str, int] = {}
    for idx, rule in enumerate(spec.rules):
        if rule.id in seen_rules:
            errors.append(
                SpecValidationError(
                    path=f"rules[{idx}].id",
                    message=f"Duplicate rule id '{rule.id}' (previously defined at rules[{seen_rules[rule.id]}].id)",
                )
            )
        else:
            seen_rules[rule.id] = idx

    # 3. Actions with no handler
    valid_actions = {a.value for a in ActionType}
    for s_idx, step in enumerate(spec.steps):
        for a_idx, action_name in enumerate(step.allowed_actions):
            if action_name not in valid_actions:
                errors.append(
                    SpecValidationError(
                        path=f"steps[{s_idx}].allowed_actions[{a_idx}]",
                        message=f"Action '{action_name}' has no registered engine handler",
                    )
                )

    for a_idx, action_name in enumerate(spec.ask_orbis.allowed_actions):
        if action_name not in valid_actions:
            errors.append(
                SpecValidationError(
                    path=f"ask_orbis.allowed_actions[{a_idx}]",
                    message=f"Action '{action_name}' has no registered engine handler",
                )
            )

    # 4. Directives not in schema
    for key, directive in spec.visual_directive_mapping.items():
        if directive.type not in VALID_DIRECTIVE_TYPES:
            errors.append(
                SpecValidationError(
                    path=f"visual_directive_mapping.{key}.type",
                    message=f"Directive type '{directive.type}' not in schema. Allowed: {sorted(VALID_DIRECTIVE_TYPES)}",
                )
            )
        if directive.type == "effect" and directive.name and directive.name not in VALID_EFFECT_NAMES:
            errors.append(
                SpecValidationError(
                    path=f"visual_directive_mapping.{key}.name",
                    message=f"Effect name '{directive.name}' not in schema. Allowed: {sorted(VALID_EFFECT_NAMES)}",
                )
            )

    # 5. Parameter bounds outside engine limits
    engine_id = spec.engine.id
    if engine_id not in SUPPORTED_ENGINES:
        errors.append(
            SpecValidationError(
                path="engine.id",
                message=f"Unsupported engine id '{engine_id}'. Supported: {sorted(SUPPORTED_ENGINES)}",
            )
        )
    else:
        limits = ENGINE_LIMITS.get(engine_id, {})
        for param, bound in spec.engine.parameter_bounds.items():
            if bound.min > bound.max:
                errors.append(
                    SpecValidationError(
                        path=f"engine.parameter_bounds.{param}.min",
                        message=f"Parameter min ({bound.min}) cannot exceed max ({bound.max})",
                    )
                )
            if param in limits:
                lim_min, lim_max = limits[param]
                if bound.min < lim_min:
                    errors.append(
                        SpecValidationError(
                            path=f"engine.parameter_bounds.{param}.min",
                            message=f"Parameter bound min ({bound.min}) is below engine limit ({lim_min})",
                        )
                    )
                if bound.max > lim_max:
                    errors.append(
                        SpecValidationError(
                            path=f"engine.parameter_bounds.{param}.max",
                            message=f"Parameter bound max ({bound.max}) exceeds engine limit ({lim_max})",
                        )
                    )

    # 6. Constants without provenance
    for const_key, const_meta in spec.provenance.constants.items():
        src = (const_meta.source or "").strip()
        cit = (const_meta.citation or "").strip()
        if not src and not cit:
            errors.append(
                SpecValidationError(
                    path=f"provenance.constants.{const_key}.source",
                    message=f"Constant '{const_key}' has no provenance source or citation",
                )
            )

    # 7. Hard-coded strings / i18n
    if not spec.i18n_keys:
        errors.append(
            SpecValidationError(
                path="i18n_keys",
                message="Spec must provide i18n_keys mapping user-facing strings",
            )
        )
    else:
        if not spec.title.startswith("i18n:") and "title" not in spec.i18n_keys:
            errors.append(
                SpecValidationError(
                    path="i18n_keys.title",
                    message="Hard-coded string: missing i18n key for 'title'",
                )
            )
        for s_idx, step in enumerate(spec.steps):
            step_key = f"steps.{step.id}.title"
            if not step.title.startswith("i18n:") and step_key not in spec.i18n_keys and "steps" not in spec.i18n_keys:
                errors.append(
                    SpecValidationError(
                        path=f"i18n_keys.steps[{s_idx}].title",
                        message=f"Hard-coded string: missing i18n key for step '{step.id}'",
                    )
                )

    # 8. Pharma specs outside adult ranges
    is_pharma = spec.district == "pharma" or spec.engine.id.startswith("pharma")
    if is_pharma:
        for p_name, (a_min, a_max) in ADULT_RANGES.items():
            if p_name in spec.engine.parameter_bounds:
                bound = spec.engine.parameter_bounds[p_name]
                if bound.min < a_min or bound.max > a_max:
                    errors.append(
                        SpecValidationError(
                            path=f"engine.parameter_bounds.{p_name}",
                            message=(
                                f"Pharma spec outside adult range [{a_min}, {a_max}]: "
                                f"[{bound.min}, {bound.max}] (paediatric not supported per R6)"
                            ),
                        )
                    )

    return ValidationReport(
        spec_id=spec.id,
        valid=len(errors) == 0,
        errors=errors,
        spec=spec if len(errors) == 0 else None,
    )
