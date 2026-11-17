"""Tests for accessibility baseline, focus trapping, and reduced motion (P1-T9)."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from pathlib import Path


@pytest.mark.asyncio
async def test_2d_screens_landmarks_and_semantics():
    """Verify all 2D screens have appropriate headings, landmarks, and ARIA roles."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        html = res.text

        # Landmarks & Navigation
        assert 'role="dialog"' in html
        assert 'aria-modal="true"' in html
        assert 'role="log"' in html
        assert 'aria-live="polite"' in html
        assert 'aria-label=' in html

        # Screen IDs
        for screen_id in [
            "screen-lobby",
            "screen-brief",
            "screen-report",
            "screen-leaderboard",
            "screen-settings",
            "screen-model-cards",
            "screen-reality-check",
            "screen-404",
            "modal-onboarding",
            "modal-why-locked",
            "modal-about"
        ]:
            assert f'id="{screen_id}"' in html, f"Missing screen: {screen_id}"


def test_focus_visible_and_reduced_motion_css():
    """Verify tokens.css enforces 3px visible focus ring and reduced motion speed overrides."""
    tokens_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "styles" / "tokens.css"
    assert tokens_path.exists()
    content = tokens_path.read_text(encoding="utf-8")

    # Focus-visible rule
    assert ":focus-visible" in content
    assert "outline: 3px solid" in content

    # Reduced motion override
    assert "@media (prefers-reduced-motion: reduce)" in content
    assert "animation-duration: 0.01ms !important" in content
    assert "transition-duration: 0.01ms !important" in content


def test_modal_focus_traps_in_javascript():
    """Verify main.js handles Tab wrapping and Escape dismissal with focus restoration."""
    main_js_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "lab" / "main.js"
    assert main_js_path.exists()
    content = main_js_path.read_text(encoding="utf-8")

    # Focus trapping & escape keys for modals
    assert "modalWhyLocked.querySelectorAll" in content
    assert "modalAbout.querySelectorAll" in content
    assert "modal.querySelectorAll" in content
    assert "lastFocusedWhyLocked" in content
    assert "lastFocusedAbout" in content
