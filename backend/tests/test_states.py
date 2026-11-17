"""Tests for loading, empty, error, offline, and WebGL fallback states (P1-T10)."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_loading_and_offline_states_present():
    """Verify global loading spinner and offline banner exist in HTML with appropriate roles."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        html = res.text

        # Global loading spinner
        assert 'id="global-loading-spinner"' in html
        assert 'loading-spinner' in html
        assert 'id="loading-spinner-label"' in html

        # Offline banner
        assert 'id="offline-state-banner"' in html
        assert 'role="status"' in html
        assert "Offline" in html


@pytest.mark.asyncio
async def test_empty_state_on_leaderboard():
    """Verify empty state is present in leaderboard view."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        html = res.text

        assert 'id="leaderboard-empty-state"' in html
        assert "No runs yet" in html


@pytest.mark.asyncio
async def test_error_state_and_webgl_fallback():
    """Verify friendly error card with What Happened/What You Can Do and WebGL fallback card."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        html = res.text

        # Friendly error card
        assert 'id="session-error-overlay"' in html
        assert 'id="session-error-title"' in html
        assert 'id="error-what-happened"' in html
        assert 'id="error-what-to-do"' in html
        assert 'id="btn-error-back-to-brief"' in html
        assert 'id="btn-error-to-lobby"' in html

        # WebGL fallback
        assert 'id="webgl-fallback"' in html
        assert "WebGL Unavailable" in html
        assert "classic.html" in html
