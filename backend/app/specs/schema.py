"""
Experiment Specification Schema for Simly Orbis.
Strict Pydantic models implementing Section 10 of the MVP Build Specification.
"""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

# Supported domains & engines
DISTRICTS = {"chemistry", "pharma", "space"}
SUPPORTED_ENGINES = {
    "chem.titration",
    "pharma.pk",
    "pharma.trial",
    "pharma.pkpd",
    "space.orbit",
}

# Supported visual directive types and effect names (from VisualDirective model)
VALID_DIRECTIVE_TYPES = {
    "liquid", "effect", "readout", "vitals", "label", "highlight",
    "rocket", "flame", "orbit_path", "stage_sep", "failure",
}
VALID_EFFECT_NAMES = {
    "splash", "bubbles", "smoke", "spark", "alarm", "glow",
    "fume_puff", "spill_puddle", "runaway_reaction", "foam_eruption",
    "contamination", "sparkles", "confetti", "camera_shake", "alarm_flash",
}

# Adult-only ranges for pharma per Rule R6 and Section 10
ADULT_RANGES = {
    "age": (18, 90),
    "weight_kg": (40.0, 150.0),
    "crcl_ml_min": (15.0, 150.0),
}

# Engine parameter limits
ENGINE_LIMITS: dict[str, dict[str, tuple[float, float]]] = {
    "chem.titration": {
        "analyte_vol_ml": (1.0, 1000.0),
        "titrant_vol_ml": (0.0, 200.0),
        "analyte_molarity": (0.001, 5.0),
        "titrant_molarity": (0.001, 5.0),
        "temperature_c": (0.0, 100.0),
    },
    "pharma.pk": {
        "dose_mg": (1.0, 5000.0),
        "cl_l_per_h": (0.1, 100.0),
        "v_d_l": (1.0, 500.0),
        "ka_per_h": (0.01, 20.0),
    },
    "pharma.trial": {
        "age": (18.0, 90.0),
        "weight_kg": (40.0, 150.0),
        "crcl_ml_min": (15.0, 150.0),
        "dose_mg": (1.0, 5000.0),
        "e0": (0.0, 100.0),
        "emax": (0.0, 100.0),
        "ec50": (0.01, 100.0),
    },
    "pharma.pkpd": {
        "age": (18.0, 90.0),
        "weight_kg": (40.0, 150.0),
        "crcl_ml_min": (15.0, 150.0),
        "dose_mg": (1.0, 5000.0),
        "e0": (0.0, 100.0),
        "emax": (0.0, 100.0),
        "ec50": (0.01, 100.0),
    },
    "space.orbit": {
        "target_alt_km": (100.0, 40000.0),
        "payload_mass_kg": (1.0, 50000.0),
        "stage_mass_kg": (10.0, 1000000.0),
        "isp_s": (50.0, 1000.0),
        "stages": (1.0, 5.0),
    },
}


class StrictModel(BaseModel):
    """Base model that forbids unknown fields."""
    model_config = ConfigDict(extra="forbid")


class ParameterBound(StrictModel):
    """Min/Max parameter limits."""
    min: float
    max: float
    unit: str | None = None
    default: float | None = None


class EngineSpec(StrictModel):
    """Engine declaration with version and parameter bounds."""
    id: str
    minimum_version: str
    parameter_bounds: dict[str, ParameterBound] = Field(default_factory=dict)


class StepSpec(StrictModel):
    """Step definition within an experiment."""
    id: str
    title: str
    allowed_actions: list[str]
    preconditions: list[str] = Field(default_factory=list)
    effects: list[str] = Field(default_factory=list)


class RuleSpec(StrictModel):
    """Safety and protocol rule definition."""
    id: str
    text: str
    severity: Literal["info", "penalty", "block", "fail"]
    condition: str | None = None
    built_in_rule: str | None = None


class ScoringSpec(StrictModel):
    """Scoring weights and letter grade cutoffs."""
    weights: dict[str, int]
    grade_thresholds: dict[str, int]


class DirectiveSpec(StrictModel):
    """Visual directive specification."""
    type: str
    target: str | None = None
    name: str | None = None
    hex: str | None = None
    duration_ms: int | None = None
    label: str | None = None
    value: str | float | None = None
    unit: str | None = None


class MentorMistakeSpec(StrictModel):
    """Common mistake pattern and remedy."""
    id: str
    trigger: str
    remedy: str


class MentorSpec(StrictModel):
    """Dr. Orbis contextual hints and mistake remediations."""
    hints_per_step: dict[str, list[str]] = Field(default_factory=dict)
    common_mistakes: list[MentorMistakeSpec] = Field(default_factory=list)


class AskOrbisSpec(StrictModel):
    """Ask Orbis natural language action planning spec."""
    allowed_actions: list[str] = Field(default_factory=list)
    synonyms: dict[str, list[str]] = Field(default_factory=dict)


class ConstantProvenance(StrictModel):
    """Provenance metadata for an experimental physical constant."""
    value: float | int | str
    unit: str | None = None
    source: str
    citation: str | None = None
    verified_by: str = "unverified"
    retrieved_on: str = ""
    notes: str | None = None


class ProvenanceBlock(StrictModel):
    """Experiment author and constants provenance block."""
    author: str
    model_card: str
    constants: dict[str, ConstantProvenance] = Field(default_factory=dict)
    notes: str | None = None


class ExperimentSpec(StrictModel):
    """Complete specification of an interactive laboratory experiment."""
    id: str
    version: str
    district: Literal["chemistry", "pharma", "space"]
    title: str
    learning_goals: list[str] = Field(default_factory=list)
    difficulty: Literal["beginner", "intermediate", "advanced", "challenge"]
    est_minutes: int
    engine: EngineSpec
    equipment: list[str] = Field(default_factory=list)
    steps: list[StepSpec]
    rules: list[RuleSpec]
    scoring: ScoringSpec
    visual_directive_mapping: dict[str, DirectiveSpec] = Field(default_factory=dict)
    mentor: MentorSpec
    ask_orbis: AskOrbisSpec
    model_card: str
    provenance: ProvenanceBlock
    i18n_keys: dict[str, str] = Field(default_factory=dict)
