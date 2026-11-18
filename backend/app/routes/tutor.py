"""
POST /api/tutor – Dr. Orbis AI tutor.

Calls the Google Gemini API with a concise pharmacology-tutor system prompt.
Falls back to a template-based explanation if the key is missing or the API
call fails, so the endpoint always returns 200.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import settings
from app.specs.loader import get_spec_by_id

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tutor", tags=["tutor"])


def get_spec_mentor_hint(
    experiment_id: str,
    step_id: str | None = None,
    rule_id: str | None = None,
) -> str | None:
    """
    Source Dr. Orbis mentor hints dynamically from the loaded ExperimentSpec.
    Returns the step hint, rule hint/explanation, or common mistake remedy.
    """
    spec = get_spec_by_id(experiment_id)
    if not spec:
        return None

    # 1. Rule hint check
    if rule_id:
        for r in spec.rules:
            if r.id == rule_id:
                return r.hint or r.text

    # 2. Step hint check
    if step_id and step_id in spec.mentor.hints_per_step:
        hints = spec.mentor.hints_per_step[step_id]
        if hints:
            return hints[0]

    # 3. Step matching by step.id
    if step_id:
        for step in spec.steps:
            if step.id == step_id and step.id in spec.mentor.hints_per_step:
                hints = spec.mentor.hints_per_step[step.id]
                if hints:
                    return hints[0]

    return None


def get_spec_allowed_actions(experiment_id: str) -> list[str]:
    """Retrieve allowed actions list directly from an experiment spec."""
    spec = get_spec_by_id(experiment_id)
    if spec:
        return list(spec.ask_orbis.allowed_actions)
    return []


def get_spec_synonyms(experiment_id: str) -> dict[str, list[str]]:
    """Retrieve action synonyms dictionary directly from an experiment spec."""
    spec = get_spec_by_id(experiment_id)
    if spec:
        return dict(spec.ask_orbis.synonyms)
    return {}

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """\
You are Dr. Orbis, a friendly pharmacokinetics tutor for pharmacy and medical students.
You receive a brief summary of a student's simulation run: the drug, patient, dose settings,
and outcome (peak concentration, time in therapeutic zone, time in toxic zone, score).
In no more than 80 words:
1. Explain in plain language what happened physiologically (absorption, peak, elimination).
2. Give ONE concrete tip the student can use to improve their score next time.
Never give real medical advice. Never prescribe. Always remind the student this is a
simplified educational simulation.
Be warm, encouraging, and precise. Use units (mg/L, hours) when helpful.
"""


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class SimSummary(BaseModel):
    drug_name: str
    dose_mg: float
    n_doses: int
    interval_h: float
    weight_kg: float
    clearance_multiplier: float
    peak_concentration: float
    time_of_peak: float
    pct_green: float
    pct_red: float
    score: int


class TutorResponse(BaseModel):
    message: str
    source: str  # "ai" | "fallback"
    provider: str | None = None
    provider_tag: str = "Rule-based"
    fallback_reason: str | None = None  # e.g. "no_api_key" | "api_error"


# ---------------------------------------------------------------------------
# Template fallback
# ---------------------------------------------------------------------------

def _template_response(s: SimSummary) -> str:
    """Generate a rule-based explanation when Gemini is unavailable, sourced from spec.mentor."""
    spec = get_spec_by_id("dose_lab") or get_spec_by_id("pk_ward")

    zone = "therapeutic" if s.pct_green > 50 else ("toxic" if s.pct_red > 20 else "sub-therapeutic")
    peak_note = (
        f"Your peak of {s.peak_concentration:.1f} mg/L was reached at "
        f"{s.time_of_peak:.1f} h after dosing."
    )

    tip: str | None = None
    if spec and spec.mentor.common_mistakes:
        if s.pct_red > 20:
            for m in spec.mentor.common_mistakes:
                if "toxic" in m.id or "overdose" in m.id:
                    tip = f"Try: {m.remedy}"
                    break
        elif s.pct_green < 30:
            for m in spec.mentor.common_mistakes:
                if "subtherapeutic" in m.id or "underdose" in m.id:
                    tip = f"Try: {m.remedy}"
                    break

    if not tip:
        if s.pct_red > 20:
            tip = (
                "Try reducing the dose or extending the dosing interval to keep "
                "levels below the toxic threshold."
            )
        elif s.pct_green < 30:
            tip = (
                "Try increasing the dose or adding more doses to maintain levels "
                "in the therapeutic window longer."
            )
        else:
            tip = (
                "Good work! Fine-tune the interval between doses to keep the "
                "trough concentrations above the lower therapeutic boundary."
            )

    clearance_note = ""
    if s.clearance_multiplier < 0.8:
        clearance_note = (
            " Remember: reduced clearance means the drug lingers longer — "
            "lower doses are needed to avoid accumulation."
        )

    return (
        f"With {s.drug_name} at {s.dose_mg:.0f} mg × {s.n_doses} dose(s), "
        f"the patient spent {s.pct_green:.0f}% of 24 h in the {zone} zone. "
        f"{peak_note}{clearance_note} {tip} "
        f"(Educational simulation — not medical advice.)"
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("", response_model=TutorResponse, summary="Get AI tutor feedback")
async def get_tutor_feedback(body: SimSummary) -> TutorResponse:
    """
    Call Google Gemini with a simulation summary and return educational feedback.
    Falls back to a template if API keys are absent, cap is reached, or API calls fail.
    """
    user_content = (
        f"Drug: {body.drug_name}\n"
        f"Dose: {body.dose_mg:.0f} mg × {body.n_doses} dose(s)"
        + (f", every {body.interval_h:.1f} h" if body.n_doses > 1 else "") + "\n"
        f"Patient: {body.weight_kg:.0f} kg, clearance ×{body.clearance_multiplier:.2f}\n"
        f"Peak concentration: {body.peak_concentration:.2f} mg/L at t={body.time_of_peak:.1f} h\n"
        f"Time in therapeutic zone: {body.pct_green:.1f}%\n"
        f"Time in toxic zone: {body.pct_red:.1f}%\n"
        f"Score: {body.score}/100\n"
    )

    from app.ai import call_ai_assistant
    ai_res = await call_ai_assistant(
        system_prompt=_SYSTEM_PROMPT,
        user_content=user_content,
        max_tokens=256,
        timeout=8.0,
    )

    if ai_res.text:
        return TutorResponse(
            message=ai_res.text,
            source="ai",
            provider=ai_res.provider,
            provider_tag=ai_res.provider_tag,
        )

    return TutorResponse(
        message=_template_response(body),
        source="fallback",
        provider=None,
        provider_tag="Rule-based",
        fallback_reason=ai_res.fallback_reason,
    )

