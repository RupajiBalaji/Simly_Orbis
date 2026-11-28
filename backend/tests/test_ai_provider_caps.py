"""Tests for P7-T1: AIProvider interface, AI_ENABLED kill switch, per-session and daily caps."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.ai import AIProviderResponse, call_ai_assistant, set_ai_provider
from app.config import settings
from app.main import app
from app.security import ai_cap_tracker, rate_limiter


class FakeAIProvider:
    name = "fake"
    provider_tag = "AI - Fake"

    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, system_prompt: str, user_content: str, max_tokens: int = 250, timeout: float = 15.0):
        self.calls += 1
        return AIProviderResponse(text="Fake AI hint: put on PPE first.", input_tokens=42, output_tokens=12)


@pytest.fixture(autouse=True)
def reset_ai_state():
    orig_enabled = settings.ai_enabled
    orig_daily = settings.mentor_daily_cap
    orig_sess = settings.ai_session_cap
    ai_cap_tracker.reset_for_test(0)
    yield
    set_ai_provider(None)
    settings.ai_enabled = orig_enabled
    settings.mentor_daily_cap = orig_daily
    settings.ai_session_cap = orig_sess
    ai_cap_tracker.reset_for_test(0)


def test_fake_provider_and_caps():
    fake = FakeAIProvider()
    set_ai_provider(fake)
    settings.ai_enabled = True
    settings.ai_session_cap = 2
    settings.mentor_daily_cap = 3

    # Session A gets 2 calls, 3rd hits session cap
    r1 = asyncio.run(call_ai_assistant("sys", "hi", session_id="sess-A"))
    r2 = asyncio.run(call_ai_assistant("sys", "hi", session_id="sess-A"))
    r3 = asyncio.run(call_ai_assistant("sys", "hi", session_id="sess-A"))
    assert r1.provider == "fake" and r1.text is not None
    assert r2.provider == "fake"
    assert r3.provider is None and r3.provider_tag == "Rule-based"
    assert "session" in (r3.fallback_reason or "").lower()

    # Session B gets 1 call (daily total becomes 3), next hits daily cap
    r4 = asyncio.run(call_ai_assistant("sys", "hi", session_id="sess-B"))
    r5 = asyncio.run(call_ai_assistant("sys", "hi", session_id="sess-B"))
    assert r4.provider == "fake"
    assert r5.provider is None and "resting" in (r5.fallback_reason or "").lower()
    assert fake.calls == 3


def test_kill_switch_off_falls_back_cleanly_across_lab_features():
    fake = FakeAIProvider()
    set_ai_provider(fake)
    settings.ai_enabled = False

    with TestClient(app) as client:
        rate_limiter._buckets.clear()
        s = client.post("/api/lab/sessions", json={"experiment_id": "pk_ward"})
        assert s.status_code == 201, s.text
        sid = s.json()["session_id"]

        # Dr. Orbis mentor still works via rule-based fallback
        ask = client.post(
            f"/api/lab/sessions/{sid}/mentor",
            json={"mode": "ask", "question": "What should I do next?"},
        )
        assert ask.status_code == 200, ask.text
        assert ask.json()["provider_tag"] == "Rule-based"
        assert len(ask.json()["message"]) > 10

        # Ask Orbis agent still works via deterministic parser
        cmd = client.post(
            f"/api/lab/sessions/{sid}/agent/plan",
            json={"text": "put on goggles"},
        )
        assert cmd.status_code == 200, cmd.text
        assert fake.calls == 0
