"""Tests for phone-playable touch layout and responsive bottom sheet (P1-T7)."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from pathlib import Path


@pytest.mark.asyncio
async def test_touch_elements_in_html():
    """Verify touch joystick and bottom sheet handle are present in HTML."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        html = res.text

        # Touch joystick
        assert 'id="touch-joystick-zone"' in html
        assert 'id="touch-joystick-base"' in html
        assert 'id="touch-joystick-knob"' in html

        # Bottom sheet drag handle
        assert 'id="bottom-sheet-drag-handle"' in html
        assert 'class="bottom-sheet-handle"' in html


def test_responsive_phone_css_rules():
    """Verify lab.css defines media queries for 768px, 480px/390px, safe areas, and 44px touch targets."""
    lab_css = Path(__file__).resolve().parent.parent.parent / "frontend" / "lab.css"
    assert lab_css.exists()
    content = lab_css.read_text(encoding="utf-8")

    # Responsive media queries
    assert "@media (max-width: 768px)" in content
    assert "@media (max-width: 480px)" in content

    # Safe area insets
    assert "safe-area-inset-bottom" in content
    assert "safe-area-inset-top" in content

    # 44px WCAG target sizes
    assert "min-height: 44px;" in content
    assert "min-width: 44px;" in content

    # Bottom sheet transformation
    assert ".bottom-sheet-handle" in content
    assert ".touch-joystick-zone" in content
    assert "overflow-x: hidden" in content
