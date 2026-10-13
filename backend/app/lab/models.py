"""
Data models and schemas for Orbis Lab interactive lab sessions.

Defines the action vocabulary, visual directives contract, session state,
violations, and protocol progression.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal
import uuid

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Supported interactive action vocabulary in Orbis Lab."""

    wear_ppe = "wear_ppe"
    remove_ppe = "remove_ppe"
    tare_balance = "tare_balance"
    weigh = "weigh"
    dissolve = "dissolve"
    pour = "pour"
    label = "label"
    administer_oral = "administer_oral"
    advance_time = "advance_time"
    draw_blood = "draw_blood"
    run_assay = "run_assay"
    rinse_burette = "rinse_burette"
    fill_burette = "fill_burette"
    pipette_analyte = "pipette_analyte"
    add_indicator = "add_indicator"
    titrate = "titrate"
    swirl = "swirl"
    read_ph_meter = "read_ph_meter"
    record_endpoint = "record_endpoint"
    dispose_waste = "dispose_waste"
    wash_hands = "wash_hands"
    submit_report = "submit_report"


# ---------------------------------------------------------------------------
# Visual Directives Contract (Rendered by 3D Client)
# ---------------------------------------------------------------------------

class VisualDirective(BaseModel):
    """
    Structured visual directive returned by the engine for 3D/client visualization.
    Directives instruct Three.js / frontend to update glassware liquids, particles,
    readouts, alarms, or labels.
    """

    type: Literal["liquid", "effect", "readout", "vitals", "label", "highlight"]
    target: str | None = None
    hex: str | None = None
    volume_ml: float | None = None
    opacity: float | None = None
    name: Literal[
        "splash", "bubbles", "smoke", "spark", "alarm", "glow",
        "fume_puff", "spill_puddle", "runaway_reaction", "foam_eruption",
        "contamination", "sparkles", "confetti", "camera_shake", "alarm_flash"
    ] | None = None
    duration_ms: int | None = None
    label: str | None = None
    value: float | str | None = None
    unit: str | None = None
    patient: str | None = None
    hr: int | None = None
    spo2: int | None = None
    status: str | None = None
    text: str | None = None


class CharacterAnimation(BaseModel):
    """Avatar animation directive informing 3D client which gesture to trigger."""

    name: Literal[
        "idle",
        "pick_up",
        "pour",
        "weigh",
        "write_label",
        "wear_ppe",
        "draw_blood",
        "administer",
        "swirl",
        "turn_stopcock",
        "read",
        "dispose",
        "wash_hands",
    ]
    target: str
    duration_ms: int = 1500


# ---------------------------------------------------------------------------
# Violations & Safety
# ---------------------------------------------------------------------------

class Violation(BaseModel):
    """Laboratory safety rule violation with educational explanation."""

    rule_id: str
    title: str
    severity: Literal["info", "warning", "major", "critical"]
    penalty_points: int
    explanation: str


# ---------------------------------------------------------------------------
# Session Models
# ---------------------------------------------------------------------------

class ActionRequest(BaseModel):
    """Player action submission payload."""

    action: ActionType
    target: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class AvailableAction(BaseModel):
    """Context-aware action menu item for UI/3D controls."""

    action: ActionType
    label: str
    targets: list[str] = Field(default_factory=list)
    enabled: bool
    disabled_reason: str | None = None


class ActionResult(BaseModel):
    """Complete response returned after attempting an action."""

    accepted: bool
    message: str
    events: list[dict[str, Any]] = Field(default_factory=list)
    violations: list[Violation] = Field(default_factory=list)
    visuals: list[dict[str, Any]] = Field(default_factory=list)
    character_animation: dict[str, Any] | None = None
    score_delta: int = 0
    hints: list[str] = Field(default_factory=list)
    status: Literal["active", "completed", "failed"] = "active"


class MentorRequest(BaseModel):
    """Student query payload for Dr. Orbis lab mentor."""

    mode: Literal["hint", "explain", "ask", "debrief"]
    question: str | None = Field(default=None, max_length=200, description="Optional question up to 200 chars")


class MentorResponse(BaseModel):
    """Dr. Orbis AI or rule-based mentor response."""

    message: str
    source: Literal["ai", "fallback"]
    provider: str | None = None
    provider_tag: str = "Rule-based"
    fallback_reason: str | None = None
    calls_left: int


class LabSession(BaseModel):
    """Complete state container for an interactive lab session."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str
    nickname: str
    created_at: str
    clock_h: float = 0.0
    ppe: set[str] = Field(default_factory=set)
    apparatus_state: dict[str, Any] = Field(default_factory=dict)
    inventory: dict[str, Any] = Field(default_factory=dict)
    samples: list[dict[str, Any]] = Field(default_factory=list)
    protocol_progress: list[str] = Field(default_factory=list)
    score_parts: dict[str, int] = Field(
        default_factory=lambda: {
            "safety": 40,
            "accuracy": 30,
            "technique": 20,
            "protocol": 10,
        }
    )
    violations: list[Violation] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)
    hints_used: int = 0
    mentor_calls: int = 0
    agent_calls: int = 0
    mentor_history: list[dict[str, str]] = Field(default_factory=list)
    status: Literal["active", "completed", "failed"] = "active"

    model_config = {
        "arbitrary_types_allowed": True,
    }

