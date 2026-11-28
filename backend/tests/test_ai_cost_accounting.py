"""Tests for P7-T6: token cost accounting, admin view, and alert thresholds with a fake provider."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.ai import AIProviderResponse, call_ai_assistant, set_ai_provider
from app.config import settings
from app.main import app
from app.security import ai_cap_tracker, rate_limiter


class MeteredFakeProvider:
    name = "fake"
    provider_tag = "AI - Fake"

    async def generate(self, system_prompt: str, user_content: str, max_tokens: int = 250, timeout: float = 15.0):
        return AIProviderResponse(text="Metered hint.", input_tokens=1_000_000, output_tokens=500_000)


@pytest.fixture(autouse=True)
def reset_state():
    orig_enabled = settings.ai_enabled
    orig_admin = settings.admin_token
    orig_alert = settings.ai_cost_alert_usd
    orig_cap = settings.mentor_daily_cap
    ai_cap_tracker.reset_for_test(0)
    yield
    set_ai_provider(None)
    settings.ai_enabled = orig_enabled
    settings.admin_token = orig_admin
    settings.ai_cost_alert_usd = orig_alert
    settings.mentor_daily_cap = orig_cap
    ai_cap_tracker.reset_for_test(0)


def test_token_accounting_alerts_and_admin_view():
    set_ai_provider(MeteredFakeProvider())
    settings.ai_enabled = True
    settings.admin_token = "super-secret-admin-tok"
    settings.ai_cost_alert_usd = 0.20
    settings.mentor_daily_cap = 2

    # 1st call: 1M input ($0.075) + 0.5M output ($0.15) = $0.225 >= $0.20 alert threshold
    res = asyncio.run(call_ai_assistant("sys", "hi", session_id="s-cost"))
    assert res.input_tokens == 1_000_000
    assert res.output_tokens == 500_000

    # 2nd call hits 80% of daily cap=2 (2 >= 1)
    asyncio.run(call_ai_assistant("sys", "hi", session_id="s-cost"))

    with TestClient(app) as client:
        rate_limiter._buckets.clear()
        # Unauthorized admin request rejected
        assert client.get("/api/classroom/admin/ai-usage").status_code == 401
        assert client.get("/api/classroom/admin/ai-usage", headers={"X-Admin-Token": "wrong"}).status_code == 401

        # Authorized admin request returns token counts, cost, and both alerts
        ok = client.get("/api/classroom/admin/ai-usage", headers={"X-Admin-Token": "super-secret-admin-tok"})
        assert ok.status_code == 200
        body = ok.json()
        assert body["calls_today"] == 2
        assert body["input_tokens_today"] == 2_000_000
        assert body["output_tokens_today"] == 1_000_000
        assert body["total_tokens_today"] == 3_000_000
        assert body["estimated_cost_usd"] == pytest.approx(0.45, rel=1e-4)
        assert "daily_call_threshold_80pct" in body["alerts"]
        assert "daily_cost_threshold_exceeded" in body["alerts"]
