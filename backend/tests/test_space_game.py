"""
Tests for Space Game Layer: Launch & Orbit Bench experiment, safety rules S1-S8,
action dispatch, scoring, visual directives, and report generation.
"""

from __future__ import annotations

import pytest

from app.lab.engine import apply_action, create_session, get_available_actions
from app.lab.experiments import get_experiment
from app.lab.models import ActionRequest, ActionType, LabSession
from app.lab.rules import check_safety_rules


def test_launch_bench_experiment_definition():
    exp = get_experiment("launch_bench")
    assert exp.id == "launch_bench"
    assert exp.district == "space"
    assert "launch_pad" in exp.apparatus
    assert "rocket" in exp.apparatus
    assert "flight_computer" in exp.apparatus
    assert "range_control" in exp.apparatus
    assert "tracking_station" in exp.apparatus
    assert len(exp.protocol) == 10
    protocol_ids = [p["id"] for p in exp.protocol]
    assert protocol_ids == [
        "choose_rocket",
        "declare_payload",
        "fuel_rocket",
        "run_checklist",
        "clear_range",
        "launch",
        "coast",
        "burn_transfer",
        "circularize",
        "debrief",
    ]


def test_space_session_lifecycle_and_actions():
    session = create_session("launch_bench", "Commander Alex")
    assert session.experiment_id == "launch_bench"
    assert session.status == "active"

    # 1. Available actions before selecting vehicle
    actions = get_available_actions(session)
    act_map = {a.action: a for a in actions}
    assert ActionType.choose_rocket in act_map
    assert act_map[ActionType.choose_rocket].enabled is True
    assert act_map[ActionType.launch].enabled is False

    # 2. Choose Rocket
    res = apply_action(session, ActionRequest(action=ActionType.choose_rocket, target="orbis_1"))
    assert res.accepted is True
    assert "orbis_1" in session.apparatus_state["rocket"]["preset_id"]
    # Visual directive check
    rocket_vis = [v for v in res.visuals if v.get("type") == "rocket"]
    assert len(rocket_vis) == 1
    assert rocket_vis[0]["rocket"]["preset_id"] == "orbis_1"

    # 3. Declare Payload
    res = apply_action(session, ActionRequest(action=ActionType.declare_payload, target="comm_sat_500kg"))
    assert res.accepted is True
    assert session.apparatus_state["rocket"]["payload_kg"] == 500.0

    # 4. Fuel Rocket
    res = apply_action(session, ActionRequest(action=ActionType.fuel_rocket, target="nominal_fuel"))
    assert res.accepted is True
    assert session.apparatus_state["rocket"]["fueled"] is True
    assert session.apparatus_state["rocket"]["liftoff_twr"] > 1.2
    assert session.apparatus_state["rocket"]["total_delta_v_ms"] > 9000.0

    # 5. Run Checklist
    res = apply_action(session, ActionRequest(action=ActionType.run_checklist, target="flight_computer"))
    assert res.accepted is True
    assert session.apparatus_state["flight_computer"]["checklist_complete"] is True

    # 6. Clear Range
    res = apply_action(session, ActionRequest(action=ActionType.clear_range, target="range_control"))
    assert res.accepted is True
    assert session.apparatus_state["range_control"]["cleared"] is True

    # 7. Launch
    res = apply_action(session, ActionRequest(action=ActionType.launch, target="pad_39a"))
    assert res.accepted is True
    outcome = session.apparatus_state["tracking_station"]["outcome"]
    assert outcome in ("orbit_reached", "transfer_complete")
    # Verify orbit path in visuals
    orbit_vis = [v for v in res.visuals if v.get("type") == "orbit_path"]
    assert len(orbit_vis) == 1
    assert len(orbit_vis[0]["orbit_path"]) > 0

    # 8. Coast
    res = apply_action(session, ActionRequest(action=ActionType.coast, target="parking_orbit"))
    assert res.accepted is True

    # 9. Burn Transfer
    res = apply_action(session, ActionRequest(action=ActionType.burn_transfer, target="hohmann_geo"))
    assert res.accepted is True
    telem = session.apparatus_state["tracking_station"]["telemetry"]
    assert telem["apoapsis_km"] == 35786.0

    # 10. Circularize
    res = apply_action(session, ActionRequest(action=ActionType.circularize, target="circularize_geo"))
    assert res.accepted is True
    assert telem["periapsis_km"] == 35786.0

    # 11. Debrief
    res = apply_action(session, ActionRequest(action=ActionType.debrief, target="tracking_station"))
    assert res.accepted is True
    assert session.apparatus_state["tracking_station"]["debriefed"] is True

    # 12. Submit Report
    res = apply_action(session, ActionRequest(action=ActionType.submit_report, target="session_report"))
    assert res.accepted is True
    assert session.status == "completed"

    # Score checks
    assert session.score_parts["safety"] == 40
    assert session.score_parts["accuracy"] == 30
    assert session.score_parts["technique"] == 20
    assert session.score_parts["protocol"] == 10
    total_score = sum(session.score_parts.values())
    assert total_score == 100


def test_space_safety_rules_s1_to_s8():
    session = create_session("launch_bench", "Careless Cadet")

    # Select rocket
    apply_action(session, ActionRequest(action=ActionType.choose_rocket, target="orbis_1"))

    # S1: Launch without checklist
    v_s1 = check_safety_rules(session, ActionRequest(action=ActionType.launch, target="pad_39a"))
    s1_rule_ids = [v.rule_id for v in v_s1]
    assert "S1_PREFLIGHT_CHECKLIST" in s1_rule_ids
    assert "S6_RANGE_SAFETY" in s1_rule_ids  # Range also not cleared

    # S2: Fuel with <= 0 or over capacity
    v_s2 = check_safety_rules(session, ActionRequest(
        action=ActionType.fuel_rocket,
        params={"stages": [{"stage": 1, "propellant_kg": -100.0}]}
    ))
    assert any(v.rule_id == "S2_PROPELLANT_CAPACITY" for v in v_s2)

    # S3: TWR <= 1.0
    session.apparatus_state["rocket"]["liftoff_twr"] = 0.85
    session.apparatus_state["flight_computer"]["checklist_complete"] = True
    session.apparatus_state["range_control"]["cleared"] = True
    session.apparatus_state["rocket"]["payload_declared"] = True
    session.apparatus_state["rocket"]["payload_kg"] = 500.0
    v_s3 = check_safety_rules(session, ActionRequest(action=ActionType.launch, target="pad_39a"))
    assert any(v.rule_id == "S3_TWR_LIFTOFF" for v in v_s3)

    # S4: Undeclared payload
    session.apparatus_state["rocket"]["payload_declared"] = False
    v_s4 = check_safety_rules(session, ActionRequest(action=ActionType.launch, target="pad_39a"))
    assert any(v.rule_id == "S4_PAYLOAD_DECLARED" for v in v_s4)

    # S8: Submit report without debrief
    v_s8 = check_safety_rules(session, ActionRequest(action=ActionType.submit_report, target="session_report"))
    assert any(v.rule_id == "S8_DEBRIEF_CLEANUP" for v in v_s8)


@pytest.mark.asyncio
async def test_space_api_session_and_report(client):
    from httpx import AsyncClient

    # 1. Get experiment
    r_exp = await client.get("/api/lab/experiments/launch_bench")
    assert r_exp.status_code == 200
    assert r_exp.json()["id"] == "launch_bench"

    # 2. Start session
    r_start = await client.post("/api/lab/sessions", json={"experiment_id": "launch_bench", "nickname": "Major Tom"})
    assert r_start.status_code == 201
    session_id = r_start.json()["session_id"]

    # 3. Actions through API
    # Choose rocket
    r_act1 = await client.post(f"/api/lab/sessions/{session_id}/actions", json={"action": "choose_rocket", "target": "orbis_1"})
    assert r_act1.status_code == 200

    # Fuel rocket
    r_act2 = await client.post(f"/api/lab/sessions/{session_id}/actions", json={"action": "fuel_rocket", "target": "nominal_fuel"})
    assert r_act2.status_code == 200

    # Run checklist
    r_act3 = await client.post(f"/api/lab/sessions/{session_id}/actions", json={"action": "run_checklist", "target": "flight_computer"})
    assert r_act3.status_code == 200

    # Clear range
    r_act4 = await client.post(f"/api/lab/sessions/{session_id}/actions", json={"action": "clear_range", "target": "range_control"})
    assert r_act4.status_code == 200

    # Launch
    r_act5 = await client.post(f"/api/lab/sessions/{session_id}/actions", json={"action": "launch", "target": "pad_39a"})
    assert r_act5.status_code == 200

    # Debrief
    r_act6 = await client.post(f"/api/lab/sessions/{session_id}/actions", json={"action": "debrief", "target": "tracking_station"})
    assert r_act6.status_code == 200

    # Finish session & compile report
    r_finish = await client.post(f"/api/lab/sessions/{session_id}/finish", json={})
    assert r_finish.status_code == 200
    rep = r_finish.json()
    assert rep["experiment_id"] == "launch_bench"
    assert rep["nickname"] == "Major Tom"
    assert "space_result" in rep and rep["space_result"] is not None
    assert rep["space_result"]["outcome"] in ("orbit_reached", "transfer_complete")
    assert "report_markdown" in rep and rep["report_markdown"] is not None
    assert "# Orbis Lab Space Mission Analytical Report" in rep["report_markdown"]
    assert "## 1. Rocket Design & Mass Budget" in rep["report_markdown"]
    assert "## 2. Orbital Parameters: Achieved vs Nominal LEO" in rep["report_markdown"]
    assert "## 3. Delta-V Budget Breakdown" in rep["report_markdown"]
