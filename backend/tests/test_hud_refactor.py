"""Tests for HUD refactor, source chips, rules panel, and accessible actions (P1-T6)."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from pathlib import Path


@pytest.mark.asyncio
async def test_hud_docked_panels_and_source_chips():
    """Verify HUD docked panels, live-region log, rules panel, and source chips."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        html = res.text

        # Left docked panel & checklist
        assert 'id="hud-protocol-panel"' in html
        assert 'id="protocol-steps-list"' in html

        # Rules panel
        assert 'id="hud-rules-panel"' in html
        assert 'id="hud-rules-status-badge"' in html
        assert 'id="rule-title"' in html
        assert 'id="rule-status"' in html
        assert 'id="rule-reason"' in html

        # Right docked panel & live telemetry
        assert 'id="hud-right-panel"' in html
        assert 'id="hud-telemetry-section"' in html
        assert 'id="readout-concentration"' in html
        assert 'id="readout-mass"' in html

        # Source chips
        assert '[Engine]' in html
        assert '[Game]' in html

        # Accessible live-region log
        assert 'role="log"' in html
        assert 'aria-live="polite"' in html

        # Bottom docked action bar
        assert 'id="hud-bottom-dock"' in html
        assert 'id="hud-station-strip"' in html
        assert 'id="station-actions-list"' in html
        assert 'id="btn-toggle-more-actions"' in html


def test_action_menu_keyboard_and_disabled_reasons():
    """Verify action_menu.js sets tabindex, aria-disabled, disabledReason and keyboard listeners."""
    action_menu_file = Path(__file__).resolve().parent.parent.parent / "frontend" / "lab" / "game" / "action_menu.js"
    assert action_menu_file.exists()
    content = action_menu_file.read_text(encoding="utf-8")

    assert "tabindex" in content
    assert "aria-disabled" in content
    assert "disabledReason" in content
    assert "keydown" in content
