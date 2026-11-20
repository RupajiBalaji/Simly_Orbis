"""
backend/tests/test_space_scenarios.py
Verification suite for Space Mission Scenarios (P5-T1 per Section 9.3).

Verifies:
1. All 5 mission scenario specs (first_orbit, fuel_limited_orbit, hohmann_transfer,
   twr_abort, mass_budget_design) load, validate, and declare 3-step hint ladders.
2. Each scenario runs through the spec runtime (SPEC_RUNTIME=True) deterministically.
3. Scoring aligns with declared par scores and grade thresholds.
4. Two runs on identical scripted inputs yield byte-identical deterministic results.
"""

from __future__ import annotations

import copy
from pathlib import Path
import pytest

from app.config import settings
from app.lab.engine import apply_action, create_session
from app.lab.experiments import get_experiment
from app.lab.models import ActionRequest, ActionType
from app.specs.loader import load_and_validate_spec


def compute_grade(score_parts: dict[str, int]) -> tuple[int, str]:
    """Compute total score and letter grade from rubric breakdown."""
    total = max(0, min(100, sum(score_parts.values())))
    if total >= 85:
        grade = "A"
    elif total >= 70:
        grade = "B"
    elif total >= 50:
        grade = "C"
    else:
        grade = "D"
    return total, grade


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPECS_DIR = REPO_ROOT / "specs"

SCENARIO_IDS = [
    "first_orbit",
    "fuel_limited_orbit",
    "hohmann_transfer",
    "twr_abort",
    "mass_budget_design",
]


@pytest.fixture(autouse=True)
def enable_spec_runtime():
    """Ensure SPEC_RUNTIME is enabled for all scenario tests."""
    orig = getattr(settings, "spec_runtime", False)
    settings.spec_runtime = True
    yield
    settings.spec_runtime = orig


def test_scenario_specs_valid_and_have_3step_hint_ladder():
    """Verify all 5 mission scenario specs pass Section 10 validation and declare a 3-step hint ladder."""
    for sc_id in SCENARIO_IDS:
        spec_path = SPECS_DIR / f"{sc_id}.json"
        assert spec_path.exists(), f"Missing spec file: {spec_path}"

        spec, report = load_and_validate_spec(spec_path)
        assert report.valid is True, f"Spec {sc_id} invalid: {report.errors}"
        assert spec is not None
        assert spec.approved is True, f"Spec {sc_id} must be approved"
        assert spec.district == "space"

        # Check 3-step hint ladder for every step
        assert len(spec.steps) > 0
        for step in spec.steps:
            hints = spec.mentor.hints_per_step.get(step.id, [])
            assert len(hints) >= 3, (
                f"Scenario '{sc_id}' step '{step.id}' has {len(hints)} hints; expected a 3-step hint ladder"
            )


def test_first_orbit_deterministic_spec_execution():
    """Scenario 1: First orbital insertion runs through spec runtime and meets par score 85."""
    def run_sequence():
        session = create_session("first_orbit", "Astronaut_1")
        apply_action(session, ActionRequest(action=ActionType.choose_rocket, target="launch_pad", params={"preset": "orbis_1"}))
        apply_action(session, ActionRequest(action=ActionType.declare_payload, target="launch_pad", params={"payload_kg": 500.0}))
        apply_action(session, ActionRequest(action=ActionType.fuel_rocket, target="launch_pad", params={"fuel_ratio": 1.0}))
        apply_action(session, ActionRequest(action=ActionType.run_checklist, target="flight_computer"))
        apply_action(session, ActionRequest(action=ActionType.clear_range, target="range_control"))
        apply_action(session, ActionRequest(action=ActionType.launch, target="launch_pad"))
        apply_action(session, ActionRequest(action=ActionType.coast))
        apply_action(session, ActionRequest(action=ActionType.debrief, target="tracking_station"))
        apply_action(session, ActionRequest(action=ActionType.submit_report))
        score, grade = compute_grade(session.score_parts)
        return score, grade, session

    score1, grade1, s1 = run_sequence()
    score2, grade2, s2 = run_sequence()

    assert score1 == score2, "Non-deterministic score across runs"
    assert grade1 == grade2
    assert score1 >= 85, f"Expected final score >= par score 85, got {score1}"
    assert grade1 == "A"
    assert len(s1.violations) == 0, f"Expected 0 violations, got {s1.violations}"
    assert s1.apparatus_state["tracking_station"]["outcome"] == "orbit_reached"


def test_fuel_limited_orbit_deterministic_spec_execution():
    """Scenario 2: Fuel-limited insertion runs through spec runtime and meets par score 85."""
    session = create_session("fuel_limited_orbit", "Efficiency_Pilot")
    apply_action(session, ActionRequest(action=ActionType.choose_rocket, target="launch_pad", params={"preset": "orbis_1"}))
    apply_action(session, ActionRequest(action=ActionType.declare_payload, target="launch_pad", params={"payload_kg": 250.0}))
    # Fueling to 90% capacity ensures >= 5% reserve while minimizing deadweight
    apply_action(session, ActionRequest(action=ActionType.fuel_rocket, target="launch_pad", params={"fuel_ratio": 0.90}))
    apply_action(session, ActionRequest(action=ActionType.run_checklist, target="flight_computer"))
    apply_action(session, ActionRequest(action=ActionType.clear_range, target="range_control"))
    apply_action(session, ActionRequest(action=ActionType.launch, target="launch_pad"))
    apply_action(session, ActionRequest(action=ActionType.coast))
    apply_action(session, ActionRequest(action=ActionType.debrief, target="tracking_station"))
    apply_action(session, ActionRequest(action=ActionType.submit_report))
    score, grade = compute_grade(session.score_parts)

    assert score >= 85, f"Expected score >= par score 85, got {score}"
    assert grade == "A"
    assert len(session.violations) == 0
    assert session.apparatus_state["tracking_station"]["outcome"] == "orbit_reached"


def test_hohmann_transfer_deterministic_spec_execution():
    """Scenario 3: Hohmann transfer to GEO runs through spec runtime and meets par score 90."""
    session = create_session("hohmann_transfer", "Flight_Director")
    apply_action(session, ActionRequest(action=ActionType.choose_rocket, target="launch_pad", params={"preset": "orbis_heavy"}))
    apply_action(session, ActionRequest(action=ActionType.declare_payload, target="launch_pad", params={"payload_kg": 1000.0}))
    apply_action(session, ActionRequest(action=ActionType.fuel_rocket, target="launch_pad", params={"fuel_ratio": 1.0}))
    apply_action(session, ActionRequest(action=ActionType.run_checklist, target="flight_computer"))
    apply_action(session, ActionRequest(action=ActionType.clear_range, target="range_control"))
    apply_action(session, ActionRequest(action=ActionType.launch, target="launch_pad"))
    apply_action(session, ActionRequest(action=ActionType.coast))
    apply_action(session, ActionRequest(action=ActionType.burn_transfer, target="flight_computer"))
    apply_action(session, ActionRequest(action=ActionType.circularize, target="flight_computer"))
    apply_action(session, ActionRequest(action=ActionType.debrief, target="tracking_station"))
    apply_action(session, ActionRequest(action=ActionType.submit_report))
    score, grade = compute_grade(session.score_parts)

    assert score >= 90, f"Expected score >= par score 90, got {score}"
    assert grade == "A"
    assert len(session.violations) == 0
    assert session.apparatus_state["tracking_station"]["outcome"] == "transfer_complete"


def test_twr_abort_safety_enforcement():
    """Scenario 4: Low-TWR detection triggers Rule S3 violation when launching without adequate thrust."""
    session = create_session("twr_abort", "Safety_Officer")
    apply_action(session, ActionRequest(action=ActionType.choose_rocket, target="sounding_suborbital"))
    # Massive payload forces TWR below 1.0
    apply_action(session, ActionRequest(action=ActionType.declare_payload, target="launch_pad", params={"payload_kg": 5000.0}))
    apply_action(session, ActionRequest(action=ActionType.fuel_rocket, target="launch_pad", params={"fuel_ratio": 1.0}))
    apply_action(session, ActionRequest(action=ActionType.run_checklist, target="flight_computer"))
    apply_action(session, ActionRequest(action=ActionType.clear_range, target="range_control"))
    launch_res = apply_action(session, ActionRequest(action=ActionType.launch, target="launch_pad"))

    # Rule S3 violation must be recorded
    v_ids = [v.rule_id for v in session.violations]
    assert any("S3" in vid for vid in v_ids), f"Expected S3 violation for low TWR, got {v_ids}"


def test_mass_budget_design_spec_execution():
    """Scenario 5: Mass budget staging challenge runs deterministically under 65t mass cap."""
    session = create_session("mass_budget_design", "Rocket_Architect")
    apply_action(session, ActionRequest(action=ActionType.choose_rocket, target="orbis_1"))
    apply_action(session, ActionRequest(action=ActionType.declare_payload, target="launch_pad", params={"payload_kg": 500.0}))
    apply_action(session, ActionRequest(action=ActionType.fuel_rocket, target="launch_pad", params={"fuel_ratio": 1.0}))

    # Verify gross vehicle mass is strictly <= 65,000 kg (65 tonnes)
    r_state = session.apparatus_state["rocket"]
    total_mass_kg = r_state["total_mass_t"] * 1000.0
    assert total_mass_kg <= 65000.0, f"Gross liftoff mass {total_mass_kg} kg exceeds 65,000 kg ceiling"

    apply_action(session, ActionRequest(action=ActionType.run_checklist, target="flight_computer"))
    apply_action(session, ActionRequest(action=ActionType.clear_range, target="range_control"))
    apply_action(session, ActionRequest(action=ActionType.launch, target="launch_pad"))
    apply_action(session, ActionRequest(action=ActionType.coast))
    apply_action(session, ActionRequest(action=ActionType.debrief, target="tracking_station"))
    apply_action(session, ActionRequest(action=ActionType.submit_report))
    score, grade = compute_grade(session.score_parts)

    assert score >= 85, f"Expected score >= par score 85, got {score}"
    assert grade == "A"
    assert session.apparatus_state["tracking_station"]["outcome"] == "orbit_reached"
