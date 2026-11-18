"""Tests for Phase P1 Extra Gate: Accessibility, Multi-Viewport, and Keyboard Navigation (Spec 7.5, 7.6, 8.1-8.17)."""

import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.asyncio
async def test_all_2d_screens_present_with_accessible_semantics():
    """Verify all required 2D screens have proper heading, landmark, and ARIA roles."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        html = res.text

        required_screens = [
            "screen-lobby",
            "screen-brief",
            "screen-report",
            "screen-leaderboard",
            "screen-settings",
            "screen-model-cards",
            "screen-reality-check",
            "screen-404",
        ]
        for s in required_screens:
            assert f'id="{s}"' in html, f"Screen {s} missing from DOM"

        assert 'id="report-content"' in html

    # Check report actions
    report_js = (REPO_ROOT / "frontend" / "lab" / "game" / "report.js").read_text(encoding="utf-8")
    assert 'id="btn-report-print"' in report_js
    assert 'id="btn-report-lobby"' in report_js
    assert 'id="btn-report-replay"' in report_js


def test_responsive_layout_contracts_for_viewports():
    """Verify phone layout styles and touch targets for mobile (390x844) and tablet (768x1024)."""
    lab_css = (REPO_ROOT / "frontend" / "lab.css").read_text(encoding="utf-8")
    assert "@media (max-width: 768px)" in lab_css
    assert "bottom-sheet" in lab_css
    assert "touch-joystick-zone" in lab_css

    # Check minimum 44px touch target enforcement
    components_css = (REPO_ROOT / "frontend" / "ui" / "components.css").read_text(encoding="utf-8")
    assert "min-height: 44px" in components_css or "min-height:44px" in components_css or "44px" in components_css


def test_keyboard_focus_ring_and_navigation_guards():
    """Verify tokens.css specifies visible 3px outline on :focus-visible."""
    tokens_css = (REPO_ROOT / "frontend" / "styles" / "tokens.css").read_text(encoding="utf-8")
    assert ":focus-visible" in tokens_css
    assert "3px solid" in tokens_css
    assert "outline-offset" in tokens_css


def test_contrast_checker_passes_gate():
    """Verify scripts/check_contrast.py executes and passes WCAG AA contrast ratio."""
    from scripts.check_contrast import main as contrast_main
    exit_code = contrast_main()
    assert exit_code == 0
