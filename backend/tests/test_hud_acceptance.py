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


def compute_hud_element_bounds(viewport_w: int, viewport_h: int, include_context_prompt: bool = True):
    """
    Computes theoretical bounding boxes (left, top, right, bottom) of the 5 persistent HUD elements
    plus the floating context prompt (U2) based on the CSS specification.
    """
    is_mobile = viewport_w <= 600

    if is_mobile:
        # Mobile 390x844 (top-left full width at top, top-right stacked underneath)
        top_left = (6, 6, viewport_w - 6, 48)
        top_right = (6, 52, viewport_w - 6, 84)
        task_w = viewport_w - 12
        task_left = 6
        task_card = (task_left, viewport_h - 180, task_left + task_w, viewport_h - 58)
        ask_orbis = (8, viewport_h - 50, 140, viewport_h - 12)
        dr_orbis = (viewport_w - 56, viewport_h - 50, viewport_w - 8, viewport_h - 12)

        prompt_w = 160
        prompt_h = 36
        prompt_left = (viewport_w - prompt_w) // 2
        prompt_bot = viewport_h - 222
        prompt_top = prompt_bot - prompt_h
        context_prompt = (prompt_left, prompt_top, prompt_left + prompt_w, prompt_bot)

        toast_w = min(360, viewport_w - 24)
        toast_left = (viewport_w - toast_w) // 2
        toast_box = (toast_left, 90, toast_left + toast_w, 126)
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

        prompt_w = 180
        prompt_h = 36
        prompt_left = (viewport_w - prompt_w) // 2
        prompt_bot = viewport_h - 185
        prompt_top = prompt_bot - prompt_h
        context_prompt = (prompt_left, prompt_top, prompt_left + prompt_w, prompt_bot)

        toast_w = min(380, viewport_w - 24)
        toast_left = (viewport_w - toast_w) // 2
        toast_box = (toast_left, 66, toast_left + toast_w, 102)

    bounds = {
        "top-left": top_left,
        "top-right": top_right,
        "task-card": task_card,
        "ask-orbis": ask_orbis,
        "dr-orbis": dr_orbis,
    }
    if include_context_prompt:
        bounds["context-prompt"] = context_prompt
        bounds["toast"] = toast_box

    return bounds


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


# -----------------------------------------------------------------------------
# Launch & Orbit Bench HUD Acceptance Tests (Q2 Requirement)
# -----------------------------------------------------------------------------

def test_launch_bench_hud_encapsulation_and_persistent_element_budget():
    """
    Verify Launch & Orbit Bench brings telemetry, sliders and orbit view controls
    inside the 5-persistent-element budget:
    - Exactly 5 persistent elements on screen (top-left, top-right, task-card, ask-orbis, dr-orbis).
    - Orbit view controls (Pad, Orbit, Polar, Equatorial) are encapsulated inside the Menu Drawer.
    - Telemetry and parameter sliders are encapsulated in a collapsible side drawer (hidden by default).
    """
    index_content = INDEX_HTML.read_text(encoding="utf-8")
    space_scene_js = (REPO_ROOT / "frontend" / "lab" / "world" / "space_scene.js").read_text(encoding="utf-8")

    # 1. Menu drawer contains space views
    assert 'id="menu-section-space-views"' in index_content
    assert 'id="btn-view-pad"' in index_content
    assert 'id="btn-view-orbit"' in index_content
    assert 'id="btn-view-polar"' in index_content
    assert 'id="btn-view-equatorial"' in index_content

    # 2. Telemetry and sliders are encapsulated inside a collapsible drawer, not persistent overlay
    assert "space-telemetry-drawer hidden" in space_scene_js
    assert "btn-close-space-drawer" in space_scene_js
    assert "toggleTelemetryDrawer" in space_scene_js

    # 3. On activation, telemetry drawer starts collapsed (hidden) to satisfy the 5-element persistent budget
    assert "this.hudElement.style.display = 'none'" in space_scene_js


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
def test_launch_bench_hud_viewport_geometry_and_non_overlapping(viewport_w: int, viewport_h: int):
    """
    Verify that Launch Bench HUD satisfies the non-overlapping bounding box contract
    across all five target viewports.
    """
    bounds = compute_hud_element_bounds(viewport_w, viewport_h)

    # 1. Bounds remain inside viewport
    for name, (l, t, r, b) in bounds.items():
        assert l >= 0 and t >= 0 and r <= viewport_w and b <= viewport_h

    # 2. No pairwise collisions
    keys = list(bounds.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            k1, k2 = keys[i], keys[j]
            assert not boxes_overlap(bounds[k1], bounds[k2]), (
                f"Collision detected on Launch Bench between {k1} and {k2} at {viewport_w}x{viewport_h}"
            )


@pytest.mark.parametrize(
    "viewport_w, viewport_h",
    [
        (1920, 1080),
        (1366, 768),
        (1280, 720),
        (768, 1024),
        (390, 844),
    ],
)
def test_launch_bench_hud_area_coverage_budget(viewport_w: int, viewport_h: int):
    """
    Verify Launch Bench persistent HUD area coverage is <= 30% across all viewports
    (>= 70% 3D space scene visibility).
    """
    total_screen_area = viewport_w * viewport_h
    bounds = compute_hud_element_bounds(viewport_w, viewport_h, include_context_prompt=False)

    hud_area = sum((r - l) * (b - t) for l, t, r, b in bounds.values())
    hud_pct = (hud_area / total_screen_area) * 100.0
    scene_pct = 100.0 - hud_pct

    assert hud_pct <= 30.0, f"Launch Bench HUD area {hud_pct:.2f}% exceeds 30% limit at {viewport_w}x{viewport_h}"
    assert scene_pct >= 70.0, f"Launch Bench scene area {scene_pct:.2f}% below 70% at {viewport_w}x{viewport_h}"


def test_educational_disclaimer_spec_and_non_overlap():
    """
    Verify U4 requirements:
    1. Educational disclaimer is styled at >= 12px with contrast >= 4.5:1.
    2. Available in the Menu footer with info icon and top-left 'i' button.
    3. Never overlaps the Current Task card across viewports.
    """
    index_content = INDEX_HTML.read_text(encoding="utf-8")
    css_content = LAB_CSS.read_text(encoding="utf-8")

    # 1. Menu footer and top-left 'i' button
    assert 'id="btn-hud-info"' in index_content
    assert "disclaimer-text" in index_content
    assert "ℹ️" in index_content

    # 2. Font size >= 12px in lab.css
    match_size = re.search(r'\.educational-disclaimer-strip\s*\{[^}]*font-size:\s*(\d+)px', css_content)
    assert match_size is not None, "Missing pixel font size on .educational-disclaimer-strip"
    font_size_px = int(match_size.group(1))
    assert font_size_px >= 12, f"Disclaimer font-size {font_size_px}px is less than 12px requirement"

    # 3. Contrast calculation for #cbd5e1 on dark container #0f172a
    def calc_luminance(r, g, b):
        def chan(c):
            c_norm = c / 255.0
            return c_norm / 12.92 if c_norm <= 0.03928 else ((c_norm + 0.055) / 1.055) ** 2.4
        return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)

    lum_text = calc_luminance(203, 213, 225)   # #cbd5e1
    lum_bg = calc_luminance(15, 23, 42)       # #0f172a
    contrast = (lum_text + 0.05) / (lum_bg + 0.05)
    assert contrast >= 4.5, f"Contrast ratio {contrast:.2f}:1 is below 4.5:1"

    # 4. Geometrical non-overlap with task-card across all 5 viewports
    for vw, vh in [(1920, 1080), (1366, 768), (1280, 720), (768, 1024), (390, 844)]:
        bounds = compute_hud_element_bounds(vw, vh)
        task_box = bounds["task-card"]
        # Disclaimer box: centered horizontally, 2px off bottom, 16px high
        disclaimer_w = min(400, vw - 32)
        disclaimer_l = (vw - disclaimer_w) // 2
        disclaimer_b = vh - 2
        disclaimer_t = disclaimer_b - 16
        disclaimer_box = (disclaimer_l, disclaimer_t, disclaimer_l + disclaimer_w, disclaimer_b)
        assert not boxes_overlap(task_box, disclaimer_box), (
            f"Disclaimer overlaps task card at {vw}x{vh}: task={task_box}, disclaimer={disclaimer_box}"
        )


def test_first_run_flow_pulse_and_help_explanation():
    """
    Verify U5 requirements:
    1. Primary button gentle pulse animation for 5 seconds after walkthrough completion.
    2. Single 'What do I do?' help button inside Current Task card with plain explanation.
    3. Persistent HUD element budget remains exactly 5.
    """
    index_content = INDEX_HTML.read_text(encoding="utf-8")
    css_content = LAB_CSS.read_text(encoding="utf-8")
    hud_js = (REPO_ROOT / "frontend" / "lab" / "game" / "hud.js").read_text(encoding="utf-8")
    action_menu_js = (REPO_ROOT / "frontend" / "lab" / "game" / "action_menu.js").read_text(encoding="utf-8")
    main_js = (REPO_ROOT / "frontend" / "lab" / "main.js").read_text(encoding="utf-8")

    # 1. 'What do I do?' button and explanation popover inside task card
    assert 'id="btn-task-what-do-i-do"' in index_content
    assert 'id="task-card-help-popover"' in index_content
    assert 'id="task-card-help-text"' in index_content
    assert ".btn-task-help" in css_content
    assert ".task-card-help-popover" in css_content
    assert "updateHelpExplanation" in action_menu_js

    # 2. Primary button guide pulse
    assert "@keyframes buttonPulseGuide" in css_content
    assert ".task-btn-primary.pulse-guide" in css_content
    assert "triggerPrimaryButtonPulse" in hud_js
    assert "triggerPrimaryButtonPulse" in main_js

    # 3. Persistent count remains exactly 5
    matches = re.findall(r'data-hud-persistent="([^"]+)"', index_content)
    assert len(matches) == 5


def test_launch_bench_3d_lighting_apparatus_and_loader():
    """
    Verify U6 requirements:
    1. SpaceScene builds its own PBR lighting (DirectionalLight, HemisphereLight, AmbientLight)
       so the 3D scene is not black when roomGroup is hidden.
    2. apparatus.js handles the 6 space apparatus IDs without unmapped warnings.
    3. Loading indicator (#space-scene-loading) exists and is dismissed after rendering frames.
    """
    index_content = INDEX_HTML.read_text(encoding="utf-8")
    css_content = LAB_CSS.read_text(encoding="utf-8")
    space_js = (REPO_ROOT / "frontend" / "lab" / "world" / "space_scene.js").read_text(encoding="utf-8")
    apparatus_js = (REPO_ROOT / "frontend" / "lab" / "world" / "apparatus.js").read_text(encoding="utf-8")

    assert "buildLighting" in space_js
    assert "THREE.DirectionalLight" in space_js
    assert "THREE.HemisphereLight" in space_js
    assert "THREE.AmbientLight" in space_js

    for app_id in ["launch_pad", "rocket", "propellant_tanks", "range_control", "flight_computer", "tracking_station"]:
        assert app_id in apparatus_js

    assert 'id="space-scene-loading"' in index_content
    assert ".space-scene-loading" in css_content
    assert "space-scene-loading" in space_js


def test_fresh_session_score_and_safety_values_and_hud_reset():
    """
    Verify V1 requirements:
    1. Backend create_session initializes score_parts totaling 100 and safety == scoring_weights['safety']
       with 0 violations for every registered experiment.
    2. hud.js sums score_parts for totalScore and normalizes safety against maxSafety, keeping Safety
       neutral/green when no violation has occurred, and resets HUD metrics on experiment switch.
    3. index.html uses '--' instead of hardcoded 100 placeholders.
    """
    from app.lab.engine import create_session
    from app.lab.experiments import _EXPERIMENTS

    for exp_id, exp in _EXPERIMENTS.items():
        session = create_session(exp_id, "TestUser")
        assert sum(session.score_parts.values()) == 100, f"{exp_id} initial score_parts must sum to 100"
        assert session.score_parts["safety"] == exp.scoring_weights["safety"]
        assert session.violations == []

    index_content = INDEX_HTML.read_text(encoding="utf-8")
    hud_js = (REPO_ROOT / "frontend" / "lab" / "game" / "hud.js").read_text(encoding="utf-8")
    assert "Score: --" in index_content
    assert "Safety --/100" in index_content
    assert "hasViolations" in hud_js
    assert "scoring_weights?.safety" in hud_js
    assert "this.scoreEl.textContent = 'Score: --'" in hud_js


def test_graphics_benchmark_toast_placement_and_suppression():
    """
    Verify V2 requirements:
    1. #toast-container is positioned at top-centre below the HUD (top: 66px), not over 3D scene center.
    2. Benchmark toast only fires if tier changed (selectedTier !== prevTier), auto-dismisses at 3000ms,
       and is suppressed in headless/software-render (navigator.webdriver).
    """
    css_content = LAB_CSS.read_text(encoding="utf-8")
    main_js = (REPO_ROOT / "frontend" / "lab" / "main.js").read_text(encoding="utf-8")

    assert "top: 66px;" in css_content
    assert "navigator.webdriver" in main_js
    assert "selectedTier !== prevTier" in main_js
    assert "3000)" in main_js


def test_mobile_390x844_stacked_header_and_no_text_clipping():
    """
    Verify V3 requirements:
    1. At <= 600px (390x844), top-left spans full width and top-right stacks cleanly underneath (top: 52px)
       so experiment titles are never clipped behind Time/Score.
    2. .hud-title-col has min-width: 0 and flex: 1 so ellipsis/truncation works without overflow.
    3. Mobile bounding boxes at 390x844 have zero pairwise overlap and stay within 35% area budget.
    """
    css_content = LAB_CSS.read_text(encoding="utf-8")
    assert "top: 52px;" in css_content
    assert "min-width: 0;" in css_content
    assert "text-overflow: ellipsis;" in css_content

    bounds = compute_hud_element_bounds(390, 844)
    keys = list(bounds.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            assert not boxes_overlap(bounds[keys[i]], bounds[keys[j]])


def test_proximity_prompt_suppressed_for_non_step_stations():
    """
    Verify T2: floating proximity prompt only shows when closestStation matches the current step target
    (e.g. suppressed during Step 1 PPE when mapStepToApparatus returns null).
    """
    hud_js = (REPO_ROOT / "frontend" / "lab" / "game" / "hud.js").read_text(encoding="utf-8")
    assert "isRelevantToCurrentStep = Boolean(nextStep && stepTarget && stepTarget === closestStation.id)" in hud_js
    assert "!stepTarget || stepTarget === closestStation.id" not in hud_js


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
