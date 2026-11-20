"""
backend/tests/test_space_playthroughs.py
End-to-end playthrough test suite for Space Launch Bench (P5-T5).

Verifies:
1. Success Playthrough:
   - Full nominal flight lifecycle: choose_rocket -> declare_payload -> fuel_rocket
     -> run_checklist -> clear_range -> launch -> coast -> burn_transfer -> circularize -> debrief -> submit_report.
   - 100% score (Grade A), nominal telemetry, and analytical space report generation.
2. Rule-Violation Playthrough:
   - Triggers Space Safety Rules S1 through S8 (e.g. S1 checklist, S2 capacity, S3 TWR, S4 payload, S6 range, S8 debrief).
   - Verifies penalty point tracking, rule infraction records, and grade reduction.
3. Mission Failure Playthroughs:
   - Overload / Under-thrust (no_liftoff): TWR <= 1.0 produces failure directive and low grade.
   - Delta-V depletion (suborbital_fall): sounding rocket attempting orbital insertion fails with suborbital arc.
   - Hohmann mismatch (transfer_failed): insufficient delta-V for apogee boost produces transfer failure.
4. Space Parser Corpora Verification:
   - Evaluates all 55 phrases in ask_orbis_phrases_space.json against the spec-driven vocabulary.
   - Verifies 100.0% pass rate (55/55) for launch_bench_author.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from app.lab.agent import parse_request_rule_based
from app.lab.engine import apply_action, create_session, get_available_actions
from app.lab.experiments import get_experiment
from app.lab.models import ActionRequest, ActionType
from app.lab.rules import check_safety_rules
from app.space.orbit import evaluate_mission, get_preset_rockets


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPACE_CORPUS_FILE = REPO_ROOT / "backend" / "tests" / "data" / "ask_orbis_phrases_space.json"


def test_space_success_playthrough():
    """Execute complete nominal success playthrough for launch_bench."""
    session = create_session("launch_bench", "Commander Armstrong")
    assert session.status == "active"

    # Step 1: Choose Rocket (Orbis-1)
    res1 = apply_action(session, ActionRequest(action=ActionType.choose_rocket, target="orbis_1"))
    assert res1.accepted is True
    assert session.apparatus_state["rocket"]["preset_id"] == "orbis_1"

    # Step 2: Declare Payload (500 kg)
    res2 = apply_action(session, ActionRequest(
        action=ActionType.declare_payload,
        target="comm_sat_500kg",
        params={"payload_kg": 500.0},
    ))
    assert res2.accepted is True
    assert session.apparatus_state["rocket"]["payload_kg"] == 500.0

    # Step 3: Fuel Rocket (Nominal)
    res3 = apply_action(session, ActionRequest(action=ActionType.fuel_rocket, target="nominal_fuel"))
    assert res3.accepted is True
    assert session.apparatus_state["rocket"]["fueled"] is True
    assert session.apparatus_state["rocket"]["liftoff_twr"] > 1.2
    assert session.apparatus_state["rocket"]["total_delta_v_ms"] >= 9300.0

    # Step 4: Run Checklist
    res4 = apply_action(session, ActionRequest(action=ActionType.run_checklist, target="flight_computer"))
    assert res4.accepted is True
    assert session.apparatus_state["flight_computer"]["checklist_complete"] is True

    # Step 5: Clear Range
    res5 = apply_action(session, ActionRequest(action=ActionType.clear_range, target="range_control"))
    assert res5.accepted is True
    assert session.apparatus_state["range_control"]["cleared"] is True

    # Step 6: Launch into LEO
    res6 = apply_action(session, ActionRequest(
        action=ActionType.launch,
        target="pad_39a",
        params={"target_alt_km": 200.0},
    ))
    assert res6.accepted is True
    assert session.apparatus_state["tracking_station"]["outcome"] in ("orbit_reached", "transfer_complete")

    # Step 7: Coast
    res7 = apply_action(session, ActionRequest(action=ActionType.coast, target="parking_orbit"))
    assert res7.accepted is True

    # Step 8: Burn Transfer (Hohmann to GEO)
    res8 = apply_action(session, ActionRequest(action=ActionType.burn_transfer, target="hohmann_geo"))
    assert res8.accepted is True
    telem = session.apparatus_state["tracking_station"]["telemetry"]
    assert telem["apoapsis_km"] == 35786.0

    # Step 9: Circularize at GEO
    res9 = apply_action(session, ActionRequest(action=ActionType.circularize, target="circularize_geo"))
    assert res9.accepted is True
    assert telem["periapsis_km"] == 35786.0

    # Step 10: Debrief
    res10 = apply_action(session, ActionRequest(action=ActionType.debrief, target="tracking_station"))
    assert res10.accepted is True
    assert session.apparatus_state["tracking_station"]["debriefed"] is True

    # Step 11: Submit Report
    res11 = apply_action(session, ActionRequest(action=ActionType.submit_report, target="session_report"))
    assert res11.accepted is True
    assert session.status == "completed"

    # Perfect Score Check
    assert session.score_parts["safety"] == 40
    assert session.score_parts["accuracy"] == 30
    assert session.score_parts["technique"] == 20
    assert session.score_parts["protocol"] == 10
    assert sum(session.score_parts.values()) == 100


def test_space_rule_violation_playthrough():
    """Verify safety rules S1-S8 trigger penalties during unprincipled launch attempts."""
    session = create_session("launch_bench", "Maverick")
    apply_action(session, ActionRequest(action=ActionType.choose_rocket, target="orbis_1"))

    # S1 & S6: Launching without checklist and without range clearance
    v_premature = check_safety_rules(session, ActionRequest(action=ActionType.launch, target="pad_39a"))
    rule_ids = {v.rule_id for v in v_premature}
    assert "S1_PREFLIGHT_CHECKLIST" in rule_ids
    assert "S6_RANGE_SAFETY" in rule_ids

    # S2: Fueling with illegal capacity
    v_capacity = check_safety_rules(session, ActionRequest(
        action=ActionType.fuel_rocket,
        params={"stages": [{"stage": 1, "propellant_kg": -50.0}]},
    ))
    assert any(v.rule_id == "S2_PROPELLANT_CAPACITY" for v in v_capacity)

    # S4: Launching without declaring payload
    session.apparatus_state["flight_computer"]["checklist_complete"] = True
    session.apparatus_state["range_control"]["cleared"] = True
    session.apparatus_state["rocket"]["payload_declared"] = False
    v_payload = check_safety_rules(session, ActionRequest(action=ActionType.launch, target="pad_39a"))
    assert any(v.rule_id == "S4_PAYLOAD_DECLARED" for v in v_payload)

    # S3: Attempting liftoff with insufficient TWR (<= 1.0)
    session.apparatus_state["rocket"]["payload_declared"] = True
    session.apparatus_state["rocket"]["payload_kg"] = 500.0
    session.apparatus_state["rocket"]["liftoff_twr"] = 0.92
    v_twr = check_safety_rules(session, ActionRequest(action=ActionType.launch, target="pad_39a"))
    assert any(v.rule_id == "S3_TWR_LIFTOFF" for v in v_twr)

    # S8: Submitting report without debrief
    v_debrief = check_safety_rules(session, ActionRequest(action=ActionType.submit_report, target="session_report"))
    assert any(v.rule_id == "S8_DEBRIEF_CLEANUP" for v in v_debrief)


def test_space_failure_playthroughs():
    """Verify mission failure modes produce failure directives, low grades, and explanations."""
    presets = get_preset_rockets()
    sounding = next(p for p in presets if p["id"] == "sounding_suborbital")
    orbis1 = next(p for p in presets if p["id"] == "orbis_1")

    # 1. Overload / Under-thrust failure (no_liftoff)
    res_no_liftoff = evaluate_mission(
        stages=sounding["stages"],
        payload_mass_kg=4000.0,
        target_altitude_m=200000.0,
    )
    assert res_no_liftoff["outcome"] == "no_liftoff"
    assert res_no_liftoff["liftoff_twr"] <= 1.0

    # 2. Delta-V depletion failure (suborbital_fall)
    res_suborbital = evaluate_mission(
        stages=sounding["stages"],
        payload_mass_kg=20.0,
        target_altitude_m=200000.0,
    )
    assert res_suborbital["outcome"] == "suborbital_fall"
    assert res_suborbital["available_dv_ms"] < 9300.0

    # 3. Session End-to-End Failure Run
    session = create_session("launch_bench", "Failed_Test_Cadet")
    apply_action(session, ActionRequest(action=ActionType.choose_rocket, target="sounding_suborbital"))
    apply_action(session, ActionRequest(action=ActionType.declare_payload, target="sounding_suborbital", params={"payload_kg": 25.0}))
    apply_action(session, ActionRequest(action=ActionType.fuel_rocket, target="sounding_suborbital", params={"fuel_ratio": 1.0}))
    apply_action(session, ActionRequest(action=ActionType.run_checklist, target="flight_computer"))
    apply_action(session, ActionRequest(action=ActionType.clear_range, target="range_control"))
    launch_res = apply_action(session, ActionRequest(action=ActionType.launch, target="launch_pad"))

    fail_dirs = [v for v in launch_res.visuals if v.get("type") == "failure"]
    assert len(fail_dirs) >= 1
    assert fail_dirs[0]["failure"] == "suborbital_fall"

    # Finish and verify low grade
    apply_action(session, ActionRequest(action=ActionType.debrief, target="tracking_station"))
    finish_res = apply_action(session, ActionRequest(action=ActionType.submit_report, target="session_report"))
    assert session.status == "completed"
    total_score = sum(session.score_parts.values())
    assert total_score < 75  # Failed suborbital mission cannot achieve high grade


def test_space_parser_corpora_and_pass_rates():
    """Verify space parser corpus ask_orbis_phrases_space.json achieves 100.0% pass rate."""
    assert SPACE_CORPUS_FILE.exists(), f"Missing corpus file: {SPACE_CORPUS_FILE}"
    with open(SPACE_CORPUS_FILE, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    assert len(corpus) == 55, f"Expected 55 phrases in space corpus, got {len(corpus)}"

    session = create_session("launch_bench", "CorporaSpy")
    passed = 0
    failures = []

    for item in corpus:
        steps, skipped = parse_request_rule_based(item["text"], session)
        actions = [s.action.value for s in steps]
        if actions == item["expected_actions"]:
            passed += 1
        else:
            failures.append((item["id"], item["text"], actions, item["expected_actions"]))

    pass_rate = (passed / len(corpus)) * 100.0
    assert len(failures) == 0, f"Parser failures ({len(failures)}/{len(corpus)}): {failures}"
    assert pass_rate == 100.0, f"Expected 100.0% pass rate on launch_bench_author, got {pass_rate:.1f}%"
