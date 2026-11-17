"""
backend/tests/test_ui_components.py
DOM and Structure Tests for Simly Orbis Shared Component Library (Section 7.3 & P1-T2).

Verifies:
1. frontend/ui/components.css exists and defines all 17 component classes.
2. frontend/ui/components.js exports reusable constructors.
3. frontend/ui/index.html showcase exists and contains every component in every state.
4. HTTP endpoints serve all UI assets cleanly with HTTP 200.
"""

from __future__ import annotations

from pathlib import Path
import re
import pytest
from httpx import AsyncClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
UI_DIR = REPO_ROOT / "frontend" / "ui"
COMPONENTS_CSS = UI_DIR / "components.css"
COMPONENTS_JS = UI_DIR / "components.js"
SHOWCASE_HTML = UI_DIR / "index.html"
FONTS_DIR = REPO_ROOT / "frontend" / "vendor" / "fonts"


def test_ui_component_files_exist():
    """Verify core UI component library files exist."""
    assert COMPONENTS_CSS.exists(), "frontend/ui/components.css missing"
    assert COMPONENTS_JS.exists(), "frontend/ui/components.js missing"
    assert SHOWCASE_HTML.exists(), "frontend/ui/index.html showcase missing"
    assert (FONTS_DIR / "OFL.txt").exists(), "frontend/vendor/fonts/OFL.txt missing"


def test_components_css_declares_all_spec_classes():
    """Verify that components.css covers all required Section 7.3 components."""
    content = COMPONENTS_CSS.read_text(encoding="utf-8")
    required_classes = [
        ".btn",
        ".btn-primary",
        ".btn-secondary",
        ".btn-ghost",
        ".btn-danger",
        ".card",
        ".panel",
        ".panel-header",
        ".modal",
        ".modal-overlay",
        ".toast",
        ".tab",
        ".tablist",
        ".tabpanel",
        ".slider-group",
        ".slider-input",
        ".slider-number",
        ".stepper",
        ".step-badge",
        ".readout-card",
        ".source-chip",
        ".chip-engine",
        ".chip-game",
        ".chip-lit",
        ".chip-ai",
        ".badge",
        ".progress-bar",
        ".disclaimer-banner",
        ".skeleton",
        ".empty-state",
        ".command-bar",
        ".chart-container",
        ".sr-only",
    ]
    for cls in required_classes:
        assert cls in content, f"components.css missing class definition for '{cls}'"


def test_components_js_exports():
    """Verify components.js exports constructor functions for UI components."""
    content = COMPONENTS_JS.read_text(encoding="utf-8")
    expected_exports = [
        "createButton",
        "createCard",
        "createModal",
        "showToast",
        "initTabs",
        "createSliderInput",
        "createStepper",
        "createReadout",
        "createBadge",
        "createBanner",
        "createCommandBar",
    ]
    for fn in expected_exports:
        assert f"export function {fn}" in content, f"components.js missing export '{fn}'"


def test_showcase_html_dom_structure():
    """Verify that index.html contains all components in all required states."""
    html = SHOWCASE_HTML.read_text(encoding="utf-8")

    # 1. Buttons
    assert 'class="btn btn-primary"' in html
    assert 'class="btn btn-secondary"' in html
    assert 'class="btn btn-ghost"' in html
    assert 'class="btn btn-danger"' in html
    assert 'disabled' in html, "Missing disabled button state"

    # 2. Disclaimer banner
    assert 'class="disclaimer-banner"' in html
    assert 'role="note"' in html

    # 3. Cards and Panels
    assert 'class="card"' in html
    assert 'class="panel"' in html
    assert 'class="panel-header"' in html

    # 4. Readouts with 4 source chips
    assert 'class="source-chip chip-engine"' in html
    assert 'class="source-chip chip-game"' in html
    assert 'class="source-chip chip-lit"' in html
    assert 'class="source-chip chip-ai"' in html

    # 5. Paired Slider and Number
    assert 'type="range"' in html
    assert 'type="number"' in html

    # 6. Stepper with completed and active steps
    assert 'class="stepper"' in html
    assert 'class="step-item completed"' in html
    assert 'class="step-item active"' in html

    # 7. Accessible tabs with ARIA
    assert 'role="tablist"' in html
    assert 'role="tab"' in html
    assert 'role="tabpanel"' in html
    assert 'aria-selected="true"' in html

    # 8. Command bar with / shortcut
    assert 'role="search"' in html
    assert '<kbd class="command-kbd">/</kbd>' in html

    # 9. Skeletons and Feedback states
    assert 'class="skeleton"' in html
    assert 'class="empty-state"' in html

    # 10. Chart with screen-reader accessible table fallback
    assert 'class="chart-container"' in html
    assert '<table class="sr-only"' in html


@pytest.mark.asyncio
async def test_ui_showcase_served_by_backend(client: AsyncClient):
    """Verify that /ui/index.html and its CSS/JS assets are served with HTTP 200."""
    res_html = await client.get("/ui/index.html")
    assert res_html.status_code == 200
    assert "Component Library Showcase" in res_html.text

    res_css = await client.get("/ui/components.css")
    assert res_css.status_code == 200
    assert ".btn" in res_css.text

    res_js = await client.get("/ui/components.js")
    assert res_js.status_code == 200
    assert "createButton" in res_js.text
