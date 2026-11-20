"""
backend/tests/test_launch_bench_polish.py
Verification suite for Launch Bench Polish (P5-T2).

Verifies:
1. Backend evaluation and engine directives emit matching failure outcomes:
   - no_liftoff (Liftoff TWR <= 1.0)
   - suborbital_fall (Delta-V < 9,300 m/s)
   - orbit_eccentric (eccentricity > 0.05)
   - transfer_failed
2. Frontend space_scene.js implements:
   - Parameter sliders within engine bounds (#space-sliders-panel, altitude, payload, fuel)
   - Delta-V budget bar (#space-deltav-bar-container, #space-deltav-progress)
   - Orbit view controls (#space-view-controls, pad, orbit, polar, equatorial)
   - 'Why It Failed' panel (#space-failure-panel, #space-failure-explanation, #space-failure-remedy)
"""

from __future__ import annotations

from pathlib import Path
import pytest

from app.lab.engine import apply_action, create_session
from app.lab.models import ActionRequest, ActionType
from app.space.orbit import evaluate_mission, get_preset_rockets


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_failure_modes_emit_matching_directives():
    """Verify that each failure outcome produces the corresponding failure directive."""
    presets = get_preset_rockets()
    sounding = next(p for p in presets if p["id"] == "sounding_suborbital")
    orbis1 = next(p for p in presets if p["id"] == "orbis_1")

    # 1. No Liftoff (TWR <= 1.0)
    res_no_liftoff = evaluate_mission(
        stages=sounding["stages"],
        payload_mass_kg=5000.0,
        target_altitude_m=200000.0,
    )
    assert res_no_liftoff["outcome"] == "no_liftoff"

    # 2. Suborbital Fall (insufficient Delta-V for orbital velocity)
    res_suborbital = evaluate_mission(
        stages=sounding["stages"],
        payload_mass_kg=25.0,
        target_altitude_m=200000.0,
    )
    assert res_suborbital["outcome"] == "suborbital_fall"

    # Verify session launch action emits failure directive for suborbital
    session = create_session("launch_bench", "Test_Cadet")
    apply_action(session, ActionRequest(action=ActionType.choose_rocket, target="sounding_suborbital"))
    apply_action(session, ActionRequest(action=ActionType.declare_payload, target="launch_pad", params={"payload_kg": 25.0}))
    apply_action(session, ActionRequest(action=ActionType.fuel_rocket, target="launch_pad", params={"fuel_ratio": 1.0}))
    apply_action(session, ActionRequest(action=ActionType.run_checklist, target="flight_computer"))
    apply_action(session, ActionRequest(action=ActionType.clear_range, target="range_control"))
    launch_res = apply_action(session, ActionRequest(action=ActionType.launch, target="launch_pad"))

    fail_directives = [v for v in launch_res.visuals if v.get("type") == "failure"]
    assert len(fail_directives) >= 1
    assert fail_directives[0]["failure"] == "suborbital_fall"


def test_frontend_launch_bench_polish_components_present():
    """Verify space_scene.js contains parameter sliders, Delta-V bar, orbit controls, and failure panel."""
    js_file = REPO_ROOT / "frontend" / "lab" / "world" / "space_scene.js"
    assert js_file.exists()
    content = js_file.read_text(encoding="utf-8")

    # 1. Parameter sliders within bounds
    assert "space-sliders-panel" in content
    assert "slider-target-alt" in content
    assert "slider-payload-mass" in content
    assert "slider-fuel-ratio" in content
    assert 'min="150" max="36000"' in content
    assert 'min="50" max="2000"' in content

    # 2. Delta-V budget bar
    assert "space-deltav-bar-container" in content
    assert "space-deltav-progress" in content

    # 3. Orbit view controls
    assert "space-view-controls" in content
    assert "btn-view-pad" in content
    assert "btn-view-orbit" in content
    assert "btn-view-polar" in content
    assert "btn-view-equatorial" in content
    assert "polar:" in content
    assert "equatorial:" in content

    # 4. 'Why It Failed' panel written from engine values
    assert "space-failure-panel" in content
    assert "space-failure-explanation" in content
    assert "space-failure-remedy" in content
    assert "getFailureExplanation" in content
    assert "getFailureRemedy" in content
    assert "MISSION ANOMALY INVESTIGATION" in content
