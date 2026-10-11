"""
Shared AI helper for Dr. Orbis Mentor and Tutor.

Provider Precedence:
1. Google Gemini (if GEMINI_API_KEY is configured)
2. Anthropic Claude (if ANTHROPIC_API_KEY is configured)
3. Rule-based template / heuristic fallback

Guardrails enforced:
- Maximum 8-second timeout on network calls.
- Central daily cap tracking via ai_cap_tracker.
- Strict prompt-injection defense with user text contained in structured blocks.
- Output token constraints (max 250 tokens, ~70 words target).
- Explicit provider attribution ("AI - Gemini", "AI - Claude", "Rule-based").
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Literal

import httpx

from app.config import settings
from app.security import ai_cap_tracker

log = logging.getLogger(__name__)


@dataclass
class AIResult:
    """Standardized response from AI assistant or rule-based fallback."""

    text: str | None
    provider: Literal["gemini", "claude"] | None
    provider_tag: str  # "AI - Gemini" | "AI - Claude" | "Rule-based"
    fallback_reason: str | None = None


async def call_ai_assistant(
    system_prompt: str,
    user_content: str,
    max_tokens: int = 250,
    timeout: float = 8.0,
) -> AIResult:
    """
    Call the preferred configured AI provider (Gemini first, then Anthropic),
    falling back gracefully to rule-based indications when unavailable.
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
    anthropic_key = settings.anthropic_api_key.strip()

    if not gemini_key and not anthropic_key:
        return AIResult(
            text=None,
            provider=None,
            provider_tag="Rule-based",
            fallback_reason="No AI key configured",
        )

    # 2. Try Google Gemini (First priority)
    if gemini_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=gemini_key)
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
                temperature=0.3,
            )
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=settings.gemini_model,
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
            log.warning("Gemini AI call failed (%s: %s) – checking Anthropic fallback.", type(exc).__name__, exc)

    # 3. Try Anthropic Claude (Second priority)
    if anthropic_key:
        try:
            # Check if anthropic SDK is available
            try:
                import anthropic  # noqa: PLC0415

                client = anthropic.AsyncAnthropic(api_key=anthropic_key)
                response = await asyncio.wait_for(
                    client.messages.create(
                        model=settings.anthropic_model or "claude-haiku-4-5-20251001",
                        max_tokens=max_tokens,
                        system=system_prompt,
                        messages=[{"role": "user", "content": user_content}],
                    ),
                    timeout=timeout,
                )
                if response.content and len(response.content) > 0:
                    text = response.content[0].text.strip()
                    if text:
                        ai_cap_tracker.record_call()
                        return AIResult(
                            text=text,
                            provider="claude",
                            provider_tag="AI - Claude",
                            fallback_reason=None,
                        )
            except (ImportError, AttributeError):
                # Direct REST fallback via httpx if anthropic SDK is absent
                url = "https://api.anthropic.com/v1/messages"
                headers = {
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                }
                payload = {
                    "model": settings.anthropic_model or "claude-haiku-4-5-20251001",
                    "max_tokens": max_tokens,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_content}],
                }
                async with httpx.AsyncClient(timeout=timeout) as h_client:
                    h_resp = await h_client.post(url, headers=headers, json=payload)
                    h_resp.raise_for_status()
                    data = h_resp.json()
                    content_blocks = data.get("content", [])
                    for block in content_blocks:
                        if block.get("type") == "text":
                            text = block.get("text", "").strip()
                            if text:
                                ai_cap_tracker.record_call()
                                return AIResult(
                                    text=text,
                                    provider="claude",
                                    provider_tag="AI - Claude",
                                    fallback_reason=None,
                                )
        except Exception as exc:  # noqa: BLE001
            log.warning("Anthropic Claude call failed (%s: %s).", type(exc).__name__, exc)

    # 4. Fallback when keys were configured but network / timeout / API errors occurred
    return AIResult(
        text=None,
        provider=None,
        provider_tag="Rule-based",
        fallback_reason="AI service timeout or unavailable.",
    )
