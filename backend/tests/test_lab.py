"""
Tests for Orbis Lab interactive session engine, safety rules, and endpoints.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.lab.engine import apply_action, create_session, get_available_actions
from app.lab.experiments import get_experiment, list_experiments
from app.lab.models import ActionRequest, ActionType, LabSession
from app.lab.rules import check_safety_rules
from app.modules.pharma_pk import PharmaPKModule, PharmaPKParams


# ---------------------------------------------------------------------------
# Experiments Catalog Tests
# ---------------------------------------------------------------------------

def test_list_and_get_experiments():
    exps = list_experiments()
    assert len(exps) == 2
    ids = {e.id for e in exps}
    assert "pk_ward" in ids
    assert "titration_bench" in ids

    pk = get_experiment("pk_ward")
    assert pk.district == "pharma"
    assert "digital_balance" in pk.apparatus
    assert "paracetamol_powder" in pk.inventory

    titr = get_experiment("titration_bench")
    assert titr.district == "chemistry"
    assert "burette" in titr.apparatus


@pytest.mark.asyncio
async def test_experiments_endpoints(client: AsyncClient):
    r1 = await client.get("/api/lab/experiments")
    assert r1.status_code == 200
    assert len(r1.json()) == 2

    r2 = await client.get("/api/lab/experiments/pk_ward")
    assert r2.status_code == 200
    assert r2.json()["id"] == "pk_ward"

    r3 = await client.get("/api/lab/experiments/unknown_experiment")
    assert r3.status_code == 404


# ---------------------------------------------------------------------------
# Safety Rules Unit Tests (R1 to R10)
# ---------------------------------------------------------------------------

def test_rule_r1_goggles_violation_and_compliance():
    sess = create_session("pk_ward", "Tester")
    # No goggles: hazardous action triggers R1
    req = ActionRequest(action=ActionType.weigh, params={"dose_mg": 500})
    vios = check_safety_rules(sess, req)
    assert any(v.rule_id == "R1_GOGGLES" for v in vios)

    # Compliant with goggles
    sess.ppe.add("goggles")
    vios2 = check_safety_rules(sess, req)
    assert not any(v.rule_id == "R1_GOGGLES" for v in vios2)


def test_rule_r2_gloves_violation_and_compliance():
    sess = create_session("pk_ward", "Tester")
    req = ActionRequest(action=ActionType.draw_blood, target="tube_1")
    vios = check_safety_rules(sess, req)
    assert any(v.rule_id == "R2_GLOVES" for v in vios)

    sess.ppe.add("gloves")
    vios2 = check_safety_rules(sess, req)
    assert not any(v.rule_id == "R2_GLOVES" for v in vios2)


def test_rule_r3_coat_violation_and_compliance():
    sess = create_session("pk_ward", "Tester")
    req = ActionRequest(action=ActionType.administer_oral)
    vios = check_safety_rules(sess, req)
    assert any(v.rule_id == "R3_LAB_COAT" for v in vios)

    sess.ppe.add("coat")
    vios2 = check_safety_rules(sess, req)
    assert not any(v.rule_id == "R3_LAB_COAT" for v in vios2)


def test_rule_r4_tare_first():
    sess = create_session("pk_ward", "Tester")
    sess.ppe.update(["goggles", "gloves", "coat"])
    # Balance not tared:
    req = ActionRequest(action=ActionType.weigh, params={"dose_mg": 500})
    vios = check_safety_rules(sess, req)
    assert any(v.rule_id == "R4_TARE_FIRST" for v in vios)

    # Tared balance:
    sess.apparatus_state["digital_balance"]["tared"] = True
    vios2 = check_safety_rules(sess, req)
    assert not any(v.rule_id == "R4_TARE_FIRST" for v in vios2)


def test_rule_r5_label_samples():
    sess = create_session("pk_ward", "Tester")
    sess.ppe.update(["goggles", "gloves", "coat"])
    req = ActionRequest(action=ActionType.draw_blood, target="tube_1")
    vios = check_safety_rules(sess, req)
    assert any(v.rule_id == "R5_LABEL_SAMPLES" for v in vios)

    sess.apparatus_state["tube_1"]["labeled"] = True
    vios2 = check_safety_rules(sess, req)
    assert not any(v.rule_id == "R5_LABEL_SAMPLES" for v in vios2)


def test_rule_r6_acid_into_water():
    sess = create_session("titration_bench", "Tester")
    sess.ppe.update(["goggles", "gloves", "coat"])
    sess.apparatus_state["conical_flask"]["analyte"] = "hcl_0.1M"
    # Adding water to acid:
    req = ActionRequest(action=ActionType.pour, params={"source": "water", "destination": "conical_flask"})
    vios = check_safety_rules(sess, req)
    assert any(v.rule_id == "R6_ACID_INTO_WATER" for v in vios)


def test_rule_r7_burette_overfill_and_rinsing():
    sess = create_session("titration_bench", "Tester")
    sess.ppe.update(["goggles", "gloves", "coat"])
    # Not rinsed:
    req = ActionRequest(action=ActionType.fill_burette, params={"volume_ml": 50})
    vios = check_safety_rules(sess, req)
    assert any(v.rule_id == "R7_BURETTE_OVERFILL" for v in vios)

    # Rinsed but overfilled (>50mL):
    sess.apparatus_state["burette"]["rinsed"] = True
    sess.apparatus_state["burette"]["volume_ml"] = 30.0
    req2 = ActionRequest(action=ActionType.fill_burette, params={"volume_ml": 30})
    vios2 = check_safety_rules(sess, req2)
    assert any(v.rule_id == "R7_BURETTE_OVERFILL" for v in vios2)


def test_rule_r8_dose_limit():
    sess = create_session("pk_ward", "Tester")
    sess.ppe.update(["goggles", "gloves", "coat"])
    # Toxic overdose (1500 mg > 1000 mg limit):
    req = ActionRequest(action=ActionType.weigh, params={"dose_mg": 1500})
    vios = check_safety_rules(sess, req)
    assert any(v.rule_id == "R8_DOSE_LIMIT" for v in vios)

    # Safe therapeutic dose:
    req2 = ActionRequest(action=ActionType.weigh, params={"dose_mg": 500})
    sess.apparatus_state["digital_balance"]["tared"] = True
    vios2 = check_safety_rules(sess, req2)
    assert not any(v.rule_id == "R8_DOSE_LIMIT" for v in vios2)


def test_rule_r9_waste_bins():
    sess = create_session("pk_ward", "Tester")
    # Discarding blood tube into chemical bin:
    req = ActionRequest(action=ActionType.dispose_waste, target="chemical_waste_bin", params={"item": "blood_tube_1"})
    vios = check_safety_rules(sess, req)
    assert any(v.rule_id == "R9_WASTE_BINS" for v in vios)

    # Correct biohazard disposal:
    req2 = ActionRequest(action=ActionType.dispose_waste, target="biohazard_bin", params={"item": "blood_tube_1"})
    vios2 = check_safety_rules(sess, req2)
    assert not any(v.rule_id == "R9_WASTE_BINS" for v in vios2)


def test_rule_r10_clean_finish():
    sess = create_session("pk_ward", "Tester")
    sess.ppe.update(["goggles", "gloves", "coat"])
    # Submitting report before washing hands and with PPE still on:
    req = ActionRequest(action=ActionType.submit_report)
    vios = check_safety_rules(sess, req)
    assert any(v.rule_id == "R10_CLEAN_FINISH" for v in vios)

    # Compliant clean finish:
    sess.apparatus_state["sink"]["hands_washed"] = True
    sess.ppe.clear()
    vios2 = check_safety_rules(sess, req)
    assert not any(v.rule_id == "R10_CLEAN_FINISH" for v in vios2)


# ---------------------------------------------------------------------------
# Critical Violation Failure Test
# ---------------------------------------------------------------------------

def test_two_critical_violations_terminate_session():
    sess = create_session("pk_ward", "Tester")
    # First critical violation: weigh without goggles
    res1 = apply_action(sess, ActionRequest(action=ActionType.weigh, params={"dose_mg": 500}))
    assert any(v.severity == "critical" for v in res1.violations)
    assert sess.status == "active"

    # Second critical violation: draw blood without goggles
    res2 = apply_action(sess, ActionRequest(action=ActionType.draw_blood, target="tube_1"))
    assert any(v.severity == "critical" for v in res2.violations)
    assert sess.status == "failed"
    assert res2.status == "failed"
    assert not res2.accepted


# ---------------------------------------------------------------------------
# Scripted Perfect Runs (Grade A)
# ---------------------------------------------------------------------------

def test_scripted_perfect_run_pk_ward():
    sess = create_session("pk_ward", "PerfectMedic")

    # 1. Wear PPE
    r = apply_action(sess, ActionRequest(action=ActionType.wear_ppe, target="all"))
    assert r.accepted and len(r.violations) == 0

    # 2. Tare balance
    r = apply_action(sess, ActionRequest(action=ActionType.tare_balance))
    assert r.accepted and len(r.violations) == 0

    # 3. Weigh 500 mg dose
    r = apply_action(sess, ActionRequest(action=ActionType.weigh, params={"dose_mg": 500.0}))
    assert r.accepted and len(r.violations) == 0

    # 4. Dissolve in cup
    r = apply_action(sess, ActionRequest(action=ActionType.dissolve, params={"volume_ml": 50.0}))
    assert r.accepted and len(r.violations) == 0

    # 5. Label cup
    r = apply_action(sess, ActionRequest(action=ActionType.label, target="dosing_cup", params={"text": "Paracetamol 500mg"}))
    assert r.accepted and len(r.violations) == 0

    # 6. Administer oral
    r = apply_action(sess, ActionRequest(action=ActionType.administer_oral))
    assert r.accepted and len(r.violations) == 0

    # 7. Advance time by 1.2 h (near peak)
    r = apply_action(sess, ActionRequest(action=ActionType.advance_time, params={"hours": 1.2}))
    assert r.accepted and len(r.violations) == 0

    # 8. Label tube 1
    r = apply_action(sess, ActionRequest(action=ActionType.label, target="tube_1", params={"text": "Pt Alex t=1.2h"}))
    assert r.accepted and len(r.violations) == 0

    # 9. Draw blood into tube 1
    r = apply_action(sess, ActionRequest(action=ActionType.draw_blood, target="tube_1"))
    assert r.accepted and len(r.violations) == 0

    # 10. Run assay on tube 1
    r = apply_action(sess, ActionRequest(action=ActionType.run_assay, target="tube_1"))
    assert r.accepted and len(r.violations) == 0

    # 11. Dispose biomedical waste into biohazard bin
    r = apply_action(sess, ActionRequest(action=ActionType.dispose_waste, target="biohazard_bin", params={"item": "blood_tube_1"}))
    assert r.accepted and len(r.violations) == 0

    # 12. Remove PPE
    r = apply_action(sess, ActionRequest(action=ActionType.remove_ppe, target="all"))
    assert r.accepted and len(r.violations) == 0

    # 13. Wash hands
    r = apply_action(sess, ActionRequest(action=ActionType.wash_hands))
    assert r.accepted and len(r.violations) == 0

    # 14. Submit report
    r = apply_action(sess, ActionRequest(action=ActionType.submit_report))
    assert r.accepted and len(r.violations) == 0
    assert sess.status == "completed"

    total_score = sum(sess.score_parts.values())
    assert total_score >= 85, f"Expected Grade A (>=85), got {total_score}"


def test_scripted_perfect_run_titration_bench():
    sess = create_session("titration_bench", "ChemistPro")

    # 1. Wear PPE
    r = apply_action(sess, ActionRequest(action=ActionType.wear_ppe, target="all"))
    assert r.accepted and len(r.violations) == 0

    # 2. Rinse burette
    r = apply_action(sess, ActionRequest(action=ActionType.rinse_burette))
    assert r.accepted and len(r.violations) == 0

    # 3. Fill burette with 50 mL
    r = apply_action(sess, ActionRequest(action=ActionType.fill_burette, params={"volume_ml": 50.0}))
    assert r.accepted and len(r.violations) == 0

    # 4. Pipette 25 mL analyte into conical flask
    r = apply_action(sess, ActionRequest(action=ActionType.pipette_analyte, target="acid_bottle_hcl"))
    assert r.accepted and len(r.violations) == 0

    # 5. Add phenolphthalein indicator
    r = apply_action(sess, ActionRequest(action=ActionType.add_indicator, target="phenolphthalein"))
    assert r.accepted and len(r.violations) == 0

    # 6. Titrate 20 mL
    r = apply_action(sess, ActionRequest(action=ActionType.titrate, params={"volume_ml": 20.0}))
    assert r.accepted and len(r.violations) == 0

    # 7. Swirl
    r = apply_action(sess, ActionRequest(action=ActionType.swirl))
    assert r.accepted and len(r.violations) == 0

    # 8. Titrate carefully +5.0 mL to hit exact 25.0 mL equivalence
    r = apply_action(sess, ActionRequest(action=ActionType.titrate, params={"volume_ml": 5.0}))
    assert r.accepted and len(r.violations) == 0

    # 9. Swirl
    r = apply_action(sess, ActionRequest(action=ActionType.swirl))
    assert r.accepted and len(r.violations) == 0

    # 10. Record endpoint at 25.0 mL
    r = apply_action(sess, ActionRequest(action=ActionType.record_endpoint, params={"volume_ml": 25.0}))
    assert r.accepted and len(r.violations) == 0

    # 11. Dispose waste in chemical waste bin
    r = apply_action(sess, ActionRequest(action=ActionType.dispose_waste, target="chemical_waste_bin", params={"item": "flask_contents"}))
    assert r.accepted and len(r.violations) == 0

    # 12. Remove PPE
    r = apply_action(sess, ActionRequest(action=ActionType.remove_ppe, target="all"))
    assert r.accepted and len(r.violations) == 0

    # 13. Wash hands
    r = apply_action(sess, ActionRequest(action=ActionType.wash_hands))
    assert r.accepted and len(r.violations) == 0

    # 14. Submit report
    r = apply_action(sess, ActionRequest(action=ActionType.submit_report))
    assert r.accepted and len(r.violations) == 0
    assert sess.status == "completed"

    total_score = sum(sess.score_parts.values())
    assert total_score >= 85, f"Expected Grade A (>=85), got {total_score}"


# ---------------------------------------------------------------------------
# Draw Blood Concentration Matches Simulation Within Noise Band
# ---------------------------------------------------------------------------

def test_draw_blood_concentration_within_noise_band():
    sess = create_session("pk_ward", "NoiseTester")
    sess.ppe.update(["goggles", "gloves", "coat"])
    sess.apparatus_state["digital_balance"]["tared"] = True
    apply_action(sess, ActionRequest(action=ActionType.weigh, params={"dose_mg": 500.0}))
    apply_action(sess, ActionRequest(action=ActionType.dissolve, params={"volume_ml": 50.0}))
    apply_action(sess, ActionRequest(action=ActionType.label, target="dosing_cup"))
    apply_action(sess, ActionRequest(action=ActionType.administer_oral))
    apply_action(sess, ActionRequest(action=ActionType.advance_time, params={"hours": 1.2}))
    apply_action(sess, ActionRequest(action=ActionType.label, target="tube_1"))

    res = apply_action(sess, ActionRequest(action=ActionType.draw_blood, target="tube_1"))
    assert res.accepted

    # Direct simulation reference
    module = PharmaPKModule()
    sim_res = module.run(PharmaPKParams(drug_id="paracetamol", weight_kg=70.0, clearance_multiplier=1.0, dose_mg=500.0, n_doses=1, interval_h=24.0))

    tube = sess.apparatus_state["tube_1"]
    true_c = tube["concentration_mg_l"]
    assayed_c = tube["assayed_concentration_mg_l"]

    # True concentration must be non-zero near peak
    assert true_c > 3.0
    # Assayed noise is within ~10% (3-sigma of 3% noise)
    assert abs(assayed_c - true_c) / true_c < 0.10


# ---------------------------------------------------------------------------
# Available Actions Context-Aware Disabling
# ---------------------------------------------------------------------------

def test_available_actions_disabled_reasons():
    sess = create_session("pk_ward", "ActionTester")
    actions = get_available_actions(sess)
    action_map = {a.action: a for a in actions}

    # Tare is enabled initially
    assert action_map[ActionType.tare_balance].enabled is True

    # Once tared, tare is disabled with explanation
    sess.apparatus_state["digital_balance"]["tared"] = True
    actions2 = get_available_actions(sess)
    action_map2 = {a.action: a for a in actions2}
    assert action_map2[ActionType.tare_balance].enabled is False
    assert "already zeroed" in action_map2[ActionType.tare_balance].disabled_reason


# ---------------------------------------------------------------------------
# Full Endpoint Lifecycle & Leaderboard Integration
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_lab_session_api_lifecycle(client: AsyncClient):
    # 1. Start session
    start_resp = await client.post("/api/lab/sessions", json={"experiment_id": "pk_ward", "nickname": "ApiTester"})
    assert start_resp.status_code == 201
    s_data = start_resp.json()
    session_id = s_data["session_id"]

    # 2. Query available actions
    act_resp = await client.get(f"/api/lab/sessions/{session_id}/available-actions")
    assert act_resp.status_code == 200
    assert len(act_resp.json()) > 5

    # 3. Post an action (wear PPE)
    act_post = await client.post(f"/api/lab/sessions/{session_id}/actions", json={"action": "wear_ppe", "target": "all"})
    assert act_post.status_code == 200
    assert act_post.json()["accepted"] is True

    # 4. Finish session
    fin_resp = await client.post(f"/api/lab/sessions/{session_id}/finish")
    assert fin_resp.status_code == 200
    fin_data = fin_resp.json()
    assert "grade" in fin_data
    assert "score" in fin_data

    # 5. Leaderboard
    lb_resp = await client.get("/api/lab/leaderboard?experiment_id=pk_ward")
    assert lb_resp.status_code == 200
    lb_data = lb_resp.json()
    assert any(e["nickname"] == "ApiTester" for e in lb_data)


def test_all_experiments_protocol_steps_have_titles_and_hints():
    """Requirement Stage 3.9 Item 2: Every protocol step in all experiments must have a human title and hint."""
    exps = list_experiments()
    assert len(exps) >= 2
    for exp in exps:
        assert len(exp.protocol) > 0, f"Experiment {exp.id} must define protocol steps"
        for idx, step in enumerate(exp.protocol, start=1):
            step_id = step.get("id")
            assert step_id, f"Experiment {exp.id} step #{idx} is missing 'id'"

            title = step.get("title")
            assert title, f"Experiment {exp.id} step #{idx} ({step_id}) is missing human-readable 'title'"
            assert isinstance(title, str) and len(title.strip()) > 3, f"Experiment {exp.id} step #{idx} has invalid title: {title}"
            assert title != step_id, f"Experiment {exp.id} step #{idx} title cannot simply be raw step id '{step_id}'"

            hint = step.get("hint_text") or step.get("hint")
            assert hint, f"Experiment {exp.id} step #{idx} ({step_id}) is missing 'hint_text' or 'hint'"
            assert isinstance(hint, str) and len(hint.strip()) > 5, f"Experiment {exp.id} step #{idx} has invalid hint: {hint}"

