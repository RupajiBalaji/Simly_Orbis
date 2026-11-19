"""
backend/tests/test_kinetics_bench.py
Unit and Integration tests for Reaction Kinetics Bench (chem.kinetics, P3-T4).

Verifies:
- Complete protocol execution (success path with high score & A grade)
- Safety rule violations (R1 PPE violation, K1 uncalibrated detector, K2 overtemperature)
- Accuracy scoring for order and rate constant estimate submission
- Technique scoring for spectrophotometer blank calibration and linear plot analysis
- Failure path resulting in low score / D grade
"""

import pytest
from httpx import AsyncClient

from app.lab.engine import create_session
from app.lab.experiments.kinetics_bench import apply_kinetics_action
from app.lab.models import ActionRequest


# ===========================================================================
# 1. Engine Action Runner Tests
# ===========================================================================

def test_kinetics_bench_session_initialization():
    session = create_session("kinetics_bench", "Chemist")
    assert session.experiment_id == "kinetics_bench"
    assert "reaction_vessel" in session.apparatus_state
    assert "spectrophotometer" in session.apparatus_state
    assert "thermostat_bath" in session.apparatus_state


def test_kinetics_bench_success_workflow():
    session = create_session("kinetics_bench", "Chemist")

    # 1. Wear PPE
    r1 = apply_kinetics_action(session, ActionRequest(action="wear_ppe", params={"item": "all"}))
    assert r1.accepted
    assert len(r1.violations) == 0

    # 2. Set Temperature
    r2 = apply_kinetics_action(session, ActionRequest(action="set_temperature", params={"temperature_c": 25.0}))
    assert r2.accepted

    # 3. Prepare Reactant
    r3 = apply_kinetics_action(session, ActionRequest(action="prepare_reactant", params={"initial_conc_m": 1.0, "volume_ml": 50.0}))
    assert r3.accepted
    assert len(r3.violations) == 0

    # 4. Calibrate Spectrophotometer
    r4 = apply_kinetics_action(session, ActionRequest(action="calibrate_spectrophotometer", params={}))
    assert r4.accepted
    assert session.apparatus_state["spectrophotometer"]["calibrated"] is True

    # 5. Start Reaction (Order 1)
    r5 = apply_kinetics_action(session, ActionRequest(action="start_reaction", params={"order": 1}))
    assert r5.accepted
    assert session.apparatus_state["reaction_vessel"]["running"] is True

    # 6. Record Sampling
    r6 = apply_kinetics_action(session, ActionRequest(action="record_sampling", params={"duration_s": 60.0, "num_samples": 10, "noise_sd": 0.01, "seed": 42}))
    assert r6.accepted
    ts = session.apparatus_state["spectrophotometer"]["time_series"]
    assert len(ts) == 10

    # 7. Analyze Linear Plots
    r7 = apply_kinetics_action(session, ActionRequest(action="analyze_linear_plots", params={}))
    assert r7.accepted
    fits = session.apparatus_state["spectrophotometer"]["linear_fits"]
    assert "order_1" in fits
    # For order 1 data, order 1 R^2 must be highest
    assert fits["order_1"]["r_squared"] > fits["order_0"]["r_squared"]

    # 8. Submit Estimate (Order 1, close k)
    true_k = session.apparatus_state["reaction_vessel"]["true_k"]
    r8 = apply_kinetics_action(session, ActionRequest(action="submit_order_estimate", params={"estimated_order": 1, "estimated_k": true_k}))
    assert r8.accepted
    assert session.score_parts["accuracy"] == 40  # Full 40 pts

    # 9. Dispose Waste
    r9 = apply_kinetics_action(session, ActionRequest(action="dispose_waste", params={}))
    assert r9.accepted

    # 10. Wash Hands
    r10 = apply_kinetics_action(session, ActionRequest(action="wash_hands", params={}))
    assert r10.accepted

    # 11. Submit Report
    r11 = apply_kinetics_action(session, ActionRequest(action="submit_report", params={}))
    assert r11.accepted
    assert r11.status == "completed"

    tot_score = sum(session.score_parts.values())
    assert tot_score >= 90  # Grade A


def test_kinetics_bench_rule_violations():
    session = create_session("kinetics_bench", "Violator")

    # Rule K1: Handling reactant without PPE
    r1 = apply_kinetics_action(session, ActionRequest(action="prepare_reactant", params={"initial_conc_m": 1.0}))
    assert len(r1.violations) == 1
    assert r1.violations[0].rule_id == "K1"
    assert session.score_parts["safety"] < 30

    # Rule K2: Sampling without calibration
    apply_kinetics_action(session, ActionRequest(action="start_reaction", params={"order": 0}))
    r2 = apply_kinetics_action(session, ActionRequest(action="record_sampling", params={"num_samples": 5}))
    assert len(r2.violations) == 1
    assert r2.violations[0].rule_id == "K2"
    assert session.score_parts["technique"] < 20

    # Rule K3: Excess temperature > 80°C
    r3 = apply_kinetics_action(session, ActionRequest(action="set_temperature", params={"temperature_c": 95.0}))
    assert len(r3.violations) == 1
    assert r3.violations[0].rule_id == "K3"


def test_kinetics_bench_failure_workflow():
    session = create_session("kinetics_bench", "FailedStudent")

    # Violations without PPE and with bad temp
    apply_kinetics_action(session, ActionRequest(action="set_temperature", params={"temperature_c": 90.0}))
    apply_kinetics_action(session, ActionRequest(action="prepare_reactant", params={"initial_conc_m": 1.0}))
    apply_kinetics_action(session, ActionRequest(action="start_reaction", params={"order": 1}))
    apply_kinetics_action(session, ActionRequest(action="record_sampling", params={"num_samples": 5}))

    # Submit completely wrong order and rate constant
    apply_kinetics_action(session, ActionRequest(action="submit_order_estimate", params={"estimated_order": 0, "estimated_k": 99.0}))
    assert session.score_parts["accuracy"] == 0

    # Submit report directly without waste disposal or handwashing
    apply_kinetics_action(session, ActionRequest(action="submit_report", params={}))
    tot_score = sum(session.score_parts.values())
    assert tot_score < 50  # Grade D


# ===========================================================================
# 2. HTTP Endpoint Integration Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_api_kinetics_bench_full_flow(client: AsyncClient):
    # Create session
    create_res = await client.post("/api/lab/sessions", json={"experiment_id": "kinetics_bench", "nickname": "DrKinetics"})
    assert create_res.status_code == 201
    sid = create_res.json()["session_id"]

    # Check available actions
    avail_res = await client.get(f"/api/lab/sessions/{sid}/available-actions")
    assert avail_res.status_code == 200
    avail_actions = [a["action"] for a in avail_res.json()]
    assert "wear_ppe" in avail_actions
    assert "set_temperature" in avail_actions

    # Execute full sequence via API
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "wear_ppe", "params": {"item": "all"}})
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "set_temperature", "params": {"temperature_c": 25.0}})
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "prepare_reactant", "params": {"initial_conc_m": 1.0}})
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "calibrate_spectrophotometer", "params": {}})
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "start_reaction", "params": {"order": 1}})
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "record_sampling", "params": {"duration_s": 60.0, "num_samples": 10}})
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "analyze_linear_plots", "params": {}})
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "submit_order_estimate", "params": {"estimated_order": 1, "estimated_k": 0.05}})
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "dispose_waste", "params": {}})
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "wash_hands", "params": {}})

    # Finish session & get report
    finish_res = await client.post(f"/api/lab/sessions/{sid}/finish")
    assert finish_res.status_code == 200
    report = finish_res.json()
    assert report["grade"] in ("A", "B")
    assert report["score"] >= 70
