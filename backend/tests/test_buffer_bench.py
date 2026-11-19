"""
backend/tests/test_buffer_bench.py
Unit and integration tests for Buffer Solutions & Capacity Bench (P3-T5).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.lab.engine import create_session
from app.lab.experiments.buffer_bench import (
    BUFFER_BENCH_EXPERIMENT,
    apply_buffer_action,
    get_buffer_available_actions,
)
from app.lab.models import ActionRequest, ActionType, LabSession


def test_buffer_bench_session_initialization():
    session = create_session("buffer_bench", nickname="DrBuffer")
    assert session.experiment_id == "buffer_bench"
    assert session.nickname == "DrBuffer"
    assert len(session.violations) == 0

    actions = get_buffer_available_actions(session)
    act_types = [a.action for a in actions]
    assert ActionType.wear_ppe in act_types
    assert ActionType.select_buffer_system in act_types
    assert ActionType.prepare_buffer in act_types


def test_buffer_bench_success_workflow():
    session = create_session("buffer_bench", nickname="StudentBuffer")

    # 1. Wear PPE
    r1 = apply_buffer_action(session, ActionRequest(action=ActionType.wear_ppe, params={"item": "all"}))
    assert r1.accepted
    assert "wear_ppe" in session.protocol_progress

    # 2. Select Buffer System (acetate, pKa 4.76, target pH 4.75)
    r2 = apply_buffer_action(
        session,
        ActionRequest(action=ActionType.select_buffer_system, params={"system": "acetate", "target_ph": 4.75}),
    )
    assert r2.accepted
    assert "select_buffer_system" in session.protocol_progress

    # 3. Prepare Buffer
    r3 = apply_buffer_action(
        session,
        ActionRequest(
            action=ActionType.prepare_buffer,
            params={"target_ph": 4.75, "total_conc_m": 0.2, "volume_ml": 100.0},
        ),
    )
    assert r3.accepted
    beaker = session.apparatus_state["buffer_beaker"]
    assert beaker["prepared"] is True
    assert abs(beaker["ph"] - 4.75) < 0.1
    assert beaker["buffer_capacity_beta"] > 0.05

    # 4. Test Capacity / Calibrate Meter
    r4 = apply_buffer_action(session, ActionRequest(action=ActionType.test_capacity, params={}))
    assert r4.accepted
    ph_meter = session.apparatus_state["ph_meter"]
    assert ph_meter["calibrated"] is True
    assert ph_meter["reading"] is not None

    # 5. Stress Buffer (Add 1.0 M HCl)
    r5 = apply_buffer_action(
        session,
        ActionRequest(
            action=ActionType.stress_buffer,
            params={"titrant": "hcl", "titrant_conc_m": 1.0, "max_added_ml": 15.0, "num_steps": 25},
        ),
    )
    assert r5.accepted
    burette = session.apparatus_state["stress_burette"]
    assert burette["stress_tested"] is True
    assert len(burette["stress_curve"]) == 25
    # Adding acid decreases pH
    assert burette["stress_curve"][-1]["ph"] < burette["stress_curve"][0]["ph"]

    # 6. Submit Buffer Design
    r6 = apply_buffer_action(session, ActionRequest(action=ActionType.submit_buffer_design, params={}))
    assert r6.accepted

    # 7. Dispose Waste
    r7 = apply_buffer_action(session, ActionRequest(action=ActionType.dispose_waste, params={}))
    assert r7.accepted

    # 8. Wash Hands
    r8 = apply_buffer_action(session, ActionRequest(action=ActionType.wash_hands, params={}))
    assert r8.accepted

    # 9. Submit Report
    r9 = apply_buffer_action(session, ActionRequest(action=ActionType.submit_report, params={}))
    assert r9.accepted
    assert session.status == "completed"
    assert sum(session.score_parts.values()) >= 80
    assert len(session.violations) == 0


def test_buffer_bench_rule_violations():
    session = create_session("buffer_bench", nickname="CarelessResearcher")

    # Action without PPE (Rule R1)
    r1 = apply_buffer_action(
        session,
        ActionRequest(action=ActionType.select_buffer_system, params={"system": "acetate", "target_ph": 4.75}),
    )
    assert r1.accepted
    assert any(v.rule_id == "R1" for v in session.violations)

    # Suboptimal pKa selection (acetate pKa 4.76 for target pH 8.0) -> Rule B2
    session.ppe = {"goggles", "gloves", "coat"}
    r2 = apply_buffer_action(
        session,
        ActionRequest(action=ActionType.select_buffer_system, params={"system": "acetate", "target_ph": 8.0}),
    )
    assert r2.accepted
    assert any(v.rule_id == "B2" for v in session.violations)

    # Prepare buffer
    apply_buffer_action(
        session,
        ActionRequest(action=ActionType.prepare_buffer, params={"target_ph": 4.75, "total_conc_m": 0.2}),
    )

    # Stress buffer without calibrating pH meter (Rule B3)
    session.apparatus_state["ph_meter"]["calibrated"] = False
    r3 = apply_buffer_action(
        session,
        ActionRequest(action=ActionType.stress_buffer, params={"titrant": "hcl", "max_added_ml": 10.0}),
    )
    assert r3.accepted
    assert any(v.rule_id == "B3" for v in session.violations)

    # Exit without washing hands (Rule R4)
    apply_buffer_action(session, ActionRequest(action=ActionType.submit_buffer_design, params={}))
    r4 = apply_buffer_action(session, ActionRequest(action=ActionType.submit_report, params={}))
    assert r4.accepted
    assert any(v.rule_id == "R4" for v in session.violations)


def test_buffer_bench_failure_workflow():
    session = create_session("buffer_bench", nickname="UnpreparedStudent")

    # Cannot test capacity without preparing buffer
    r1 = apply_buffer_action(session, ActionRequest(action=ActionType.test_capacity, params={}))
    assert not r1.accepted
    assert "Prepare buffer solution" in r1.message

    # Cannot stress buffer without preparing buffer
    r2 = apply_buffer_action(session, ActionRequest(action=ActionType.stress_buffer, params={}))
    assert not r2.accepted

    # Cannot submit design without stress test
    r3 = apply_buffer_action(session, ActionRequest(action=ActionType.submit_buffer_design, params={}))
    assert not r3.accepted


@pytest.mark.asyncio
async def test_api_buffer_bench_full_flow(client: AsyncClient):
    # Create session
    create_res = await client.post(
        "/api/lab/sessions",
        json={"experiment_id": "buffer_bench", "nickname": "DrBufferApi"},
    )
    assert create_res.status_code == 201
    sid = create_res.json()["session_id"]

    # Check available actions
    avail_res = await client.get(f"/api/lab/sessions/{sid}/available-actions")
    assert avail_res.status_code == 200
    avail_actions = [a["action"] for a in avail_res.json()]
    assert "wear_ppe" in avail_actions
    assert "select_buffer_system" in avail_actions

    # Execute full sequence via API
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "wear_ppe", "params": {"item": "all"}})
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "select_buffer_system", "params": {"system": "acetate", "target_ph": 4.75}})
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "prepare_buffer", "params": {"target_ph": 4.75, "total_conc_m": 0.2, "volume_ml": 100.0}})
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "test_capacity", "params": {}})
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "stress_buffer", "params": {"titrant": "hcl", "titrant_conc_m": 1.0, "max_added_ml": 10.0, "num_steps": 20}})
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "submit_buffer_design", "params": {}})
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "dispose_waste", "params": {}})
    await client.post(f"/api/lab/sessions/{sid}/actions", json={"action": "wash_hands", "params": {}})

    # Finish session & get report
    finish_res = await client.post(f"/api/lab/sessions/{sid}/finish")
    assert finish_res.status_code == 200
    report = finish_res.json()
    assert report["grade"] in ("A", "B")
    assert report["score"] >= 70
    assert any("Buffer Equilibrium" in lesson for lesson in report["lessons_learned"])
