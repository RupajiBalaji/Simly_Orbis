"""
Experiment definitions and schemas for Orbis Lab.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ExperimentDefinition(BaseModel):
    """Specification of an interactive laboratory experiment."""

    id: str
    title: str
    district: str
    description: str
    learning_goals: list[str] = Field(default_factory=list)
    required_ppe: list[str] = Field(default_factory=lambda: ["goggles", "gloves", "coat"])
    apparatus: dict[str, dict[str, Any]] = Field(default_factory=dict)
    inventory: dict[str, dict[str, Any]] = Field(default_factory=dict)
    allowed_actions: list[str] = Field(default_factory=list)
    protocol: list[dict[str, str]] = Field(default_factory=list)
    scoring_weights: dict[str, int] = Field(
        default_factory=lambda: {
            "safety": 40,
            "accuracy": 30,
            "technique": 20,
            "protocol": 10,
        }
    )
