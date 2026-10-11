"""
Tests for RC1 Hardening: Abuse & Cost Protection, Security Headers, Text Sanitization,
Rate Limiting, Health, and Ping Endpoints.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.config import settings
from app.security import (
    ai_cap_tracker,
    rate_limiter,
    sanitize_text,
)


# ---------------------------------------------------------------------------
# 1. Ping & Health Endpoints
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ping_endpoint(client: AsyncClient):
    resp = await client.get("/api/ping")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"ping": "pong"}
    assert "X-Content-Type-Options" in resp.headers
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert "frame-ancestors 'none'" in resp.headers.get("Content-Security-Policy", "")


@pytest.mark.asyncio
async def test_health_endpoint_metadata(client: AsyncClient):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "app_version" in data
    assert data["app_version"] == settings.app_version
    assert "git_sha" in data


# ---------------------------------------------------------------------------
# 2. Text Sanitization Unit Tests
# ---------------------------------------------------------------------------

def test_sanitize_text_control_chars_and_length():
    # Nickname max 24
    raw_nick = "Alice\x00\x08\x1f\tLabScientistVeryLongNameOver24Chars"
    cleaned_nick = sanitize_text(raw_nick, max_length=24)
    assert len(cleaned_nick) <= 24
    assert "\x00" not in cleaned_nick
    assert "\x08" not in cleaned_nick
    assert "\x1f" not in cleaned_nick

    # Label text max 60
    raw_label = "Vial #1\x07: " + ("A" * 100)
    cleaned_label = sanitize_text(raw_label, max_length=60)
    assert len(cleaned_label) <= 60
    assert "\x07" not in cleaned_label

    # Mentor question max 200
    raw_q = "Question\x1b" + ("?" * 250)
    cleaned_q = sanitize_text(raw_q, max_length=200)
    assert len(cleaned_q) <= 200
    assert "\x1b" not in cleaned_q

    # None handling
    assert sanitize_text(None, max_length=50) == ""


# ---------------------------------------------------------------------------
# 3. Payload Size Protection (413 Payload Too Large)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_payload_size_limit_exceeded(client: AsyncClient):
    # Payload over 20 KB (20,480 bytes)
    big_body = {"data": "X" * 25000}
    resp = await client.post("/api/simulate", json=big_body)
    assert resp.status_code == 413
    data = resp.json()
    assert "payload too large" in data["detail"].lower()


# ---------------------------------------------------------------------------
# 4. Rate Limiting Tests (429 Rate limit exceeded)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ai_rate_limiter_triggers_429(client: AsyncClient):
    # Rate limiter allows 10 calls for AI category per minute from client IP
    test_ip = "192.168.1.99"
    # Exhaust tokens for test_ip on category "ai"
    for _ in range(10):
        allowed = rate_limiter.check(test_ip, category="ai")
        assert allowed is True

    # 11th call should fail
    allowed = rate_limiter.check(test_ip, category="ai")
    assert allowed is False

    # Calling tutor endpoint with header X-Forwarded-For: test_ip should get 429
    headers = {"X-Forwarded-For": test_ip}
    resp = await client.post(
        "/api/tutor",
        json={"mode": "hint", "context": {}},
        headers=headers,
    )
    assert resp.status_code == 429
    assert "Rate limit exceeded" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 5. Daily Cap Tracker & AI_ENABLED Flag
# ---------------------------------------------------------------------------

def test_daily_cap_tracker():
    ai_cap_tracker.reset_for_test(0)
    orig_cap = settings.mentor_daily_cap
    settings.mentor_daily_cap = 2
    try:
        allowed, reason = ai_cap_tracker.can_call_ai()
        assert allowed is True
        assert reason == ""

        ai_cap_tracker.record_call()
        ai_cap_tracker.record_call()

        allowed, reason = ai_cap_tracker.can_call_ai()
        assert allowed is False
        assert reason == "daily_cap_exceeded"
    finally:
        settings.mentor_daily_cap = orig_cap
        ai_cap_tracker.reset_for_test(0)


def test_ai_enabled_flag():
    orig_flag = settings.ai_enabled
    try:
        settings.ai_enabled = False
        allowed, reason = ai_cap_tracker.can_call_ai()
        assert allowed is False
        assert reason == "ai_disabled"
    finally:
        settings.ai_enabled = orig_flag


# ---------------------------------------------------------------------------
# 6. Fallback Behavior under Cap in Lab Mentor
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mentor_fallback_when_cap_reached(client: AsyncClient):
    # Create a session
    sess_res = await client.post("/api/lab/sessions", json={"experiment_id": "pk_ward"})
    assert sess_res.status_code == 201
    session_id = sess_res.json()["session_id"]

    orig_cap = settings.mentor_daily_cap
    settings.mentor_daily_cap = 0  # Force cap reached immediately
    try:
        # Call mentor
        mentor_res = await client.post(
            f"/api/lab/sessions/{session_id}/mentor",
            json={"mode": "hint"},
        )
        assert mentor_res.status_code == 200
        data = mentor_res.json()
        assert data["source"] == "fallback"
        assert "AI mentor resting" in (data["fallback_reason"] or "")
    finally:
        settings.mentor_daily_cap = orig_cap
