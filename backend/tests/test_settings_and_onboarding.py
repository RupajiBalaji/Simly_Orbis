"""Tests for Settings screen and Onboarding Tutorial modal (P1-T5)."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from pathlib import Path


@pytest.mark.asyncio
async def test_settings_screen_controls_present():
    """Verify settings screen contains quality tier, audio controls, font scale, high contrast, and colorblind mode."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        html = res.text

        # Settings elements
        assert 'id="screen-settings"' in html
        assert 'id="setting-quality-tier"' in html
        assert 'id="setting-sound-volume"' in html
        assert 'id="setting-audio-mute"' in html
        assert 'id="setting-font-scale"' in html
        assert 'id="setting-high-contrast"' in html
        assert 'id="setting-colorblind-mode"' in html
        assert 'id="btn-settings-reset"' in html
        assert 'id="btn-replay-tutorial"' in html


@pytest.mark.asyncio
async def test_onboarding_tutorial_modal_structure():
    """Verify 90-second onboarding modal has focus trapping, 3 stepped slides, keyboard controls, and skip button."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        html = res.text

        # Modal attributes
        assert 'id="modal-onboarding"' in html
        assert 'role="dialog"' in html
        assert 'aria-modal="true"' in html
        assert 'id="btn-skip-tutorial"' in html

        # 3 Slides
        assert 'id="tutorial-slide-1"' in html
        assert 'id="tutorial-slide-2"' in html
        assert 'id="tutorial-slide-3"' in html

        # Controls
        assert 'id="btn-tutorial-prev"' in html
        assert 'id="btn-tutorial-next"' in html
        assert 'id="tutorial-dots"' in html


def test_accessibility_classes_in_tokens_css():
    """Verify tokens.css defines high-contrast, font-scale, and colorblind mode rules."""
    tokens_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "styles" / "tokens.css"
    assert tokens_path.exists()
    content = tokens_path.read_text(encoding="utf-8")

    assert "body.high-contrast" in content
    assert "body.font-scale-normal" in content
    assert "body.font-scale-large" in content
    assert "body.font-scale-xlarge" in content
    assert 'body[data-colorblind="protanopia"]' in content
    assert 'body[data-colorblind="deuteranopia"]' in content
    assert 'body[data-colorblind="tritanopia"]' in content
