"""
POST /api/tutor – Dr. Orbis AI tutor.

Calls the Anthropic Claude API with a concise pharmacology-tutor system prompt.
Falls back to a template-based explanation if the key is missing or the API
call fails, so the endpoint always returns 200.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import settings

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tutor", tags=["tutor"])

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
    fallback_reason: str | None = None  # e.g. "no_api_key" | "api_error"



# ---------------------------------------------------------------------------
# Template fallback
# ---------------------------------------------------------------------------

def _template_response(s: SimSummary) -> str:
    """Generate a rule-based explanation when Claude is unavailable."""
    zone = "therapeutic" if s.pct_green > 50 else ("toxic" if s.pct_red > 20 else "sub-therapeutic")
    peak_note = (
        f"Your peak of {s.peak_concentration:.1f} mg/L was reached at "
        f"{s.time_of_peak:.1f} h after dosing."
    )

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
    Call Google Gemini (or Anthropic Claude) with a simulation summary and return educational feedback.
    Falls back to a template if API keys are absent or API calls fail.
    """
    gemini_key = settings.gemini_api_key.strip()
    anthropic_key = settings.anthropic_api_key.strip()

    if not gemini_key and not anthropic_key:
        log.info("No AI API key set – using template fallback.")
        return TutorResponse(
            message=_template_response(body),
            source="fallback",
            fallback_reason="no_api_key",
        )

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

    # 1. Try Google Gemini
    if gemini_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=gemini_key)
            config = types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                max_output_tokens=256,
                temperature=0.3,
            )
            response = await client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=user_content,
                config=config,
            )
            text = (response.text or "").strip()
            if text:
                return TutorResponse(message=text, source="ai")
        except Exception as exc:  # noqa: BLE001
            log.warning("Gemini API call failed (%s) – checking fallback.", exc)

    # 2. Try Anthropic Claude if configured
    if anthropic_key:
        try:
            import anthropic  # noqa: PLC0415

            client = anthropic.AsyncAnthropic(api_key=anthropic_key)
            response = await client.messages.create(
                model=settings.anthropic_model,
                max_tokens=256,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
            )
            text = response.content[0].text.strip()
            return TutorResponse(message=text, source="ai")
        except Exception as exc:  # noqa: BLE001
            log.warning("Claude API call failed (%s) – using template fallback.", exc)

    # 3. Rule-based template fallback
    return TutorResponse(
        message=_template_response(body),
        source="fallback",
        fallback_reason="api_error",
    )

