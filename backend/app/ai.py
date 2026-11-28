"""
Shared AI helper & provider interface for Dr. Orbis Mentor and Tutor (P7-T1).

Provider:
- Pluggable AIProvider interface (default: GeminiProvider when GEMINI_API_KEY is set)
- Rule-based template / heuristic fallback

Guardrails enforced:
- Maximum 15-second timeout on network calls.
- Central daily cap & per-session cap tracking via ai_cap_tracker.
- AI_ENABLED kill switch.
- Strict prompt-injection defense with user text contained in structured blocks.
- Output token constraints (max 250 tokens, ~70 words target).
- Explicit provider attribution ("AI - Gemini", "Rule-based").
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Literal, Protocol

from app.config import settings
from app.security import ai_cap_tracker

log = logging.getLogger(__name__)


@dataclass
class AIProviderResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0


class AIProvider(Protocol):
    """Provider interface for LLM backends and test doubles."""

    name: str
    provider_tag: str

    async def generate(
        self,
        system_prompt: str,
        user_content: str,
        max_tokens: int = 250,
        timeout: float = 15.0,
    ) -> AIProviderResponse: ...


class GeminiProvider:
    """Google Gemini provider using the single configured GEMINI_MODEL path."""

    name = "gemini"
    provider_tag = "AI - Gemini"

    def __init__(self, api_key: str, model_name: str) -> None:
        self._api_key = api_key
        self._model_name = model_name

    async def generate(
        self,
        system_prompt: str,
        user_content: str,
        max_tokens: int = 250,
        timeout: float = 15.0,
    ) -> AIProviderResponse:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self._api_key)
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_tokens,
            temperature=0.4,
        )
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=self._model_name,
                contents=user_content,
                config=config,
            ),
            timeout=timeout,
        )
        text = (response.text or "").strip()
        usage = getattr(response, "usage_metadata", None)
        in_tok = int(getattr(usage, "prompt_token_count", 0) or 0) if usage else 0
        out_tok = int(getattr(usage, "candidates_token_count", 0) or 0) if usage else 0
        return AIProviderResponse(text=text, input_tokens=in_tok, output_tokens=out_tok)


_custom_provider: AIProvider | None = None


def set_ai_provider(provider: AIProvider | None) -> None:
    """Override the active AI provider (used by tests and evaluation harness)."""
    global _custom_provider
    _custom_provider = provider


def get_ai_provider() -> AIProvider | None:
    if _custom_provider is not None:
        return _custom_provider
    gemini_key = settings.gemini_api_key.strip()
    if not gemini_key:
        return None
    preferred_model = settings.gemini_model.strip() or "gemini-flash-lite-latest"
    return GeminiProvider(api_key=gemini_key, model_name=preferred_model)


@dataclass
class AIResult:
    """Standardized response from AI assistant or rule-based fallback."""

    text: str | None
    provider: Literal["gemini"] | str | None
    provider_tag: str  # "AI - Gemini" | "Rule-based"
    fallback_reason: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0


async def call_ai_assistant(
    system_prompt: str,
    user_content: str,
    max_tokens: int = 250,
    timeout: float = 15.0,
    session_id: str | None = None,
) -> AIResult:
    """
    Call the configured AIProvider, enforcing kill switch, daily cap, and
    per-session cap before falling back gracefully to rule-based hints.
    """
    can_call, block_reason = ai_cap_tracker.can_call_ai(session_id=session_id)
    if not can_call:
        log.info("AI assistant call blocked (%s) – using rule-based fallback.", block_reason)
        if block_reason == "daily_cap_exceeded":
            reason = "AI mentor resting, using rule-based hints"
        elif block_reason == "session_cap_exceeded":
            reason = "Session AI cap reached, using rule-based hints"
        else:
            reason = "AI disabled by administrator."
        return AIResult(text=None, provider=None, provider_tag="Rule-based", fallback_reason=reason)

    provider = get_ai_provider()
    if provider is None:
        return AIResult(
            text=None,
            provider=None,
            provider_tag="Rule-based",
            fallback_reason="No AI key configured",
        )

    try:
        resp = await provider.generate(
            system_prompt=system_prompt,
            user_content=user_content,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        text = (resp.text or "").strip()
        if text:
            ai_cap_tracker.record_call(
                session_id=session_id,
                input_tokens=resp.input_tokens,
                output_tokens=resp.output_tokens,
            )
            return AIResult(
                text=text,
                provider=provider.name,
                provider_tag=provider.provider_tag,
                fallback_reason=None,
                input_tokens=resp.input_tokens,
                output_tokens=resp.output_tokens,
            )
    except Exception as exc:  # noqa: BLE001
        log.warning("AI provider '%s' failed (%s: %s) – using rule-based fallback.", provider.name, type(exc).__name__, exc)

    return AIResult(
        text=None,
        provider=None,
        provider_tag="Rule-based",
        fallback_reason="AI service timeout or unavailable.",
    )
