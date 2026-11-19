"""
Shared AI helper for Dr. Orbis Mentor and Tutor.

Provider:
- Google Gemini (when GEMINI_API_KEY is configured)
- Rule-based template / heuristic fallback

Guardrails enforced:
- Maximum 15-second timeout on network calls.
- Central daily cap tracking via ai_cap_tracker.
- Strict prompt-injection defense with user text contained in structured blocks.
- Output token constraints (max 250 tokens, ~70 words target).
- Explicit provider attribution ("AI - Gemini", "Rule-based").
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Literal

from app.config import settings
from app.security import ai_cap_tracker

log = logging.getLogger(__name__)


@dataclass
class AIResult:
    """Standardized response from AI assistant or rule-based fallback."""

    text: str | None
    provider: Literal["gemini"] | None
    provider_tag: str  # "AI - Gemini" | "Rule-based"
    fallback_reason: str | None = None


async def call_ai_assistant(
    system_prompt: str,
    user_content: str,
    max_tokens: int = 250,
    timeout: float = 15.0,
) -> AIResult:
    """
    Call Google Gemini AI assistant, falling back gracefully across available
    Gemini models (e.g. flash-lite tiers) before resorting to rule-based fallback.
    """
    # 1. Check daily cap and AI_ENABLED flag
    can_call, block_reason = ai_cap_tracker.can_call_ai()
    if not can_call:
        log.info("AI assistant call blocked (%s) – using rule-based fallback.", block_reason)
        reason = (
            "AI mentor resting, using rule-based hints"
            if block_reason == "daily_cap_exceeded"
            else "AI disabled by administrator."
        )
        return AIResult(text=None, provider=None, provider_tag="Rule-based", fallback_reason=reason)

    gemini_key = settings.gemini_api_key.strip()
    if not gemini_key:
        return AIResult(
            text=None,
            provider=None,
            provider_tag="Rule-based",
            fallback_reason="No AI key configured",
        )

    # 2. Call Google Gemini with model cascading
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=gemini_key)
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
            temperature=0.4,
        )

        # Prioritize configured model, followed by primary standard fallback
        models_to_try: list[str] = []
        preferred_model = settings.gemini_model.strip()
        if preferred_model:
            models_to_try.append(preferred_model)
        for fallback_model in ("gemini-2.0-flash", "gemini-flash-lite-latest"):
            if fallback_model not in models_to_try:
                models_to_try.append(fallback_model)
                break  # At most one fallback model to prevent compounding latency

        last_error: Exception | None = None
        for model_name in models_to_try:
            try:
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=model_name,
                        contents=user_content,
                        config=config,
                    ),
                    timeout=timeout,
                )
                text = (response.text or "").strip()
                if text:
                    ai_cap_tracker.record_call()
                    return AIResult(
                        text=text,
                        provider="gemini",
                        provider_tag="AI - Gemini",
                        fallback_reason=None,
                    )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                err_str = str(exc).lower()
                is_terminal = (
                    isinstance(exc, (asyncio.TimeoutError, TimeoutError))
                    or "quota" in err_str
                    or "resource_exhausted" in err_str
                    or "429" in err_str
                    or "503" in err_str
                )
                log.warning(
                    "Gemini model '%s' failed (%s: %s).",
                    model_name,
                    type(exc).__name__,
                    exc,
                )
                if is_terminal:
                    log.info("Terminal AI error or timeout encountered. Falling back to rule-based assistant immediately.")
                    break
                continue

        if last_error:
            log.warning("All Gemini candidate models failed. Last error: %s: %s", type(last_error).__name__, last_error)
    except Exception as exc:  # noqa: BLE001
        log.warning("Gemini AI client initialization failed (%s: %s) – using rule-based fallback.", type(exc).__name__, exc)

    # 3. Fallback when key was configured but network / timeout / quota errors occurred
    return AIResult(
        text=None,
        provider=None,
        provider_tag="Rule-based",
        fallback_reason="AI service timeout or unavailable.",
    )
