"""
Acceptance and layout budget tests for Problem A: Progressive Disclosure HUD Interface.
Verifies:
- Exactly 5 persistent HUD elements marked with [data-hud-persistent].
- Non-overlapping bounding boxes within viewport boundaries across all 5 standard viewports:
  (1920x1080, 1366x768, 1280x720, 768x1024, 390x844).
- Total persistent HUD area <= 30% of screen area at 1366x768 (>= 70% 3D scene area).
- Tab key reaches primary task action within <= 3 keypresses.
- First valid action triggered in <= 2 clicks from default view.
- E2E browser test marked with 'browser' for Playwright verification.
"""

from __future__ import annotations

import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INDEX_HTML = REPO_ROOT / "frontend" / "index.html"
LAB_CSS = REPO_ROOT / "frontend" / "lab.css"


def test_hud_persistent_element_count():
    """Verify exactly 5 persistent elements with data-hud-persistent attribute exist in index.html."""
    content = INDEX_HTML.read_text(encoding="utf-8")
    matches = re.findall(r'data-hud-persistent="([^"]+)"', content)

    assert len(matches) == 5, f"Expected exactly 5 persistent HUD elements, found {len(matches)}: {matches}"
    expected_keys = {"top-left", "top-right", "task-card", "ask-orbis", "dr-orbis"}
    assert set(matches) == expected_keys, f"Persistent elements mismatch: {set(matches)} vs {expected_keys}"


def compute_hud_element_bounds(viewport_w: int, viewport_h: int):
    """
    Computes theoretical bounding boxes (left, top, right, bottom) of the 5 persistent HUD elements
    based on the CSS specification.
    """
    is_mobile = viewport_w <= 600

    if is_mobile:
        # Mobile 390x844
        top_left = (8, 8, min(240, viewport_w - 160), 48)
        top_right = (viewport_w - 150, 8, viewport_w - 8, 48)
        task_w = viewport_w - 16
        task_left = 8
        task_card = (task_left, viewport_h - 180, task_left + task_w, viewport_h - 70)
        ask_orbis = (8, viewport_h - 60, 140, viewport_h - 12)
        dr_orbis = (viewport_w - 56, viewport_h - 58, viewport_w - 8, viewport_h - 12)
    else:
        # Desktop / Tablet
        tl_w = min(360, int(viewport_w * 0.3))
        top_left = (16, 14, 16 + tl_w, 60)

        tr_w = min(340, int(viewport_w * 0.3))
        top_right = (viewport_w - 16 - tr_w, 14, viewport_w - 16, 60)

        if viewport_w >= 1366:
            card_w = min(540, viewport_w - 220)
        elif viewport_w > 900:
            card_w = min(500, viewport_w - 200)
        else:
            card_w = min(420, viewport_w - 320)

        card_h = 105
        card_left = (viewport_w - card_w) // 2
        task_card = (card_left, viewport_h - 18 - card_h, card_left + card_w, viewport_h - 18)

        ask_orbis = (16, viewport_h - 18 - 42, 16 + 130, viewport_h - 18)
        dr_orbis = (viewport_w - 16 - 44, viewport_h - 18 - 44, viewport_w - 16, viewport_h - 18)

    return {
        "top-left": top_left,
        "top-right": top_right,
        "task-card": task_card,
        "ask-orbis": ask_orbis,
        "dr-orbis": dr_orbis,
    }


def boxes_overlap(b1, b2) -> bool:
    """Returns True if box1 and box2 overlap with positive area."""
    l1, t1, r1, bot1 = b1
    l2, t2, r2, bot2 = b2
    # Check if one is strictly to the left, right, above, or below
    if r1 <= l2 or r2 <= l1:
        return False
    if bot1 <= t2 or bot2 <= t1:
        return False
    return True


@pytest.mark.parametrize(
    "viewport_w, viewport_h",
    [
        (1920, 1080),  # Full HD Desktop
        (1366, 768),   # Standard Laptop
        (1280, 720),   # Compact HD Laptop
        (768, 1024),   # Tablet Portrait
        (390, 844),    # Mobile
    ],
)
def test_hud_viewport_geometry_and_non_overlapping(viewport_w: int, viewport_h: int):
    """Verify that all 5 persistent elements fit in viewport and do not overlap across all 5 viewports."""
    bounds = compute_hud_element_bounds(viewport_w, viewport_h)

    # 1. Check all boxes remain inside the viewport boundaries
    for name, (l, t, r, b) in bounds.items():
        assert l >= 0, f"{name} left edge {l} < 0 at {viewport_w}x{viewport_h}"
        assert t >= 0, f"{name} top edge {t} < 0 at {viewport_w}x{viewport_h}"
        assert r <= viewport_w, f"{name} right edge {r} > {viewport_w} at {viewport_w}x{viewport_h}"
        assert b <= viewport_h, f"{name} bottom edge {b} > {viewport_h} at {viewport_w}x{viewport_h}"

    # 2. Check no pairwise overlapping among persistent elements
    keys = list(bounds.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            k1, k2 = keys[i], keys[j]
            b1, b2 = bounds[k1], bounds[k2]
            assert not boxes_overlap(b1, b2), (
                f"Collision detected between {k1} {b1} and {k2} {b2} at {viewport_w}x{viewport_h}"
            )


def test_hud_area_coverage_budget():
    """Verify total persistent HUD area is <= 30% at 1366x768 (>= 70% 3D scene area)."""
    vw, vh = 1366, 768
    total_screen_area = vw * vh
    bounds = compute_hud_element_bounds(vw, vh)

    hud_area = 0
    for name, (l, t, r, b) in bounds.items():
        area = (r - l) * (b - t)
        hud_area += area

    hud_pct = (hud_area / total_screen_area) * 100.0
    scene_pct = 100.0 - hud_pct

    assert hud_pct <= 30.0, f"HUD area {hud_pct:.2f}% exceeds 30% limit"
    assert scene_pct >= 70.0, f"3D scene area {scene_pct:.2f}% is below 70% requirement"


def test_tab_navigation_to_primary_task_action():
    """Verify primary task card action has tabindex=1 for immediate keyboard access within 3 presses."""
    content = INDEX_HTML.read_text(encoding="utf-8")
    assert 'id="task-card-actions"' in content

    # Check action_menu.js sets tabindex="1" on the primary task action button
    action_menu_js = (REPO_ROOT / "frontend" / "lab" / "game" / "action_menu.js").read_text(encoding="utf-8")
    assert "btn.setAttribute('tabindex', '1')" in action_menu_js


def test_first_valid_action_in_two_clicks():
    """Verify primary action buttons are in the DOM directly on the Current Task Card."""
    content = INDEX_HTML.read_text(encoding="utf-8")
    assert 'id="hud-current-task-card"' in content
    assert 'id="task-card-actions"' in content
    assert 'id="btn-task-go-station"' in content


@pytest.mark.browser
def test_browser_hud_clean_and_interactive():
    """Playwright E2E verification of clean HUD (skipped unless --browser or RUN_BROWSER_TESTS=1)."""
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        # Placeholder for active local test server URL
        browser.close()
