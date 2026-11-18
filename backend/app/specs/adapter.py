"""
Specification Adapter for Simly Orbis.
Converts declarative ExperimentSpec instances into ExperimentDefinition objects
consumed by the laboratory engine and API routes.
"""

from __future__ import annotations

from typing import Any
from app.lab.experiments.base import ExperimentDefinition
from app.specs.schema import ExperimentSpec


def spec_to_experiment_definition(
    spec: ExperimentSpec,
    base_apparatus: dict[str, dict[str, Any]] | None = None,
    base_inventory: dict[str, dict[str, Any]] | None = None,
    required_ppe: list[str] | None = None,
) -> ExperimentDefinition:
    """
    Bridge an ExperimentSpec to an ExperimentDefinition.
    Preserves exact engine apparatus and inventory while sourcing title, goals,
    protocol, rules, scoring weights, and allowed actions from the declarative spec.
    """
    protocol_list: list[dict[str, str]] = []
    for step in spec.steps:
        hint_text = ""
        if step.id in spec.mentor.hints_per_step and spec.mentor.hints_per_step[step.id]:
            hint_text = spec.mentor.hints_per_step[step.id][0]
        protocol_list.append(
            {
                "id": step.id,
                "title": step.title,
                "hint_text": hint_text,
                "hint": hint_text,
            }
        )

    rules_list: list[dict[str, str]] = []
    for rule in spec.rules:
        rules_list.append(
            {
                "rule_id": rule.id,
                "title": rule.text,
                "explanation": rule.text,
                "severity": rule.severity,
            }
        )

    # Allowed actions from ask_orbis or steps
    allowed = list(spec.ask_orbis.allowed_actions)
    if not allowed:
        for s in spec.steps:
            for a in s.allowed_actions:
                if a not in allowed:
                    allowed.append(a)

    return ExperimentDefinition(
        id=spec.id,
        title=spec.title,
        district=spec.district,
        description=f"{spec.title} (Spec v{spec.version})",
        learning_goals=list(spec.learning_goals),
        required_ppe=required_ppe or ["goggles", "gloves", "coat"],
        apparatus=dict(base_apparatus or {}),
        inventory=dict(base_inventory or {}),
        allowed_actions=allowed,
        protocol=protocol_list,
        rules=rules_list,
        scoring_weights=dict(spec.scoring.weights),
    )
