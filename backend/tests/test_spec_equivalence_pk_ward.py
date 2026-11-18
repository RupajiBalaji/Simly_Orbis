"""
Golden-Equivalence Test Suite for Pharmacokinetics Clinical Ward (pk_ward).
Proves that the declarative spec runtime (SPEC_RUNTIME=True) produces identical
outcomes, scores, grade, and safety violations across 22 distinct scripted sequences
compared to the legacy engine path (SPEC_RUNTIME=False).
"""

from __future__ import annotations

from typing import Any
import pytest

from app.config import settings
from app.lab.engine import apply_action, create_session
from app.lab.models import ActionRequest, ActionType


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


SEQUENCES: list[dict[str, Any]] = [
    {
        "name": "01_perfect_ward_run",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.tare_balance, "digital_balance", {}),
            (ActionType.weigh, "digital_balance", {"dose_mg": 500.0}),
            (ActionType.dissolve, "dosing_cup", {}),
            (ActionType.label, "dosing_cup", {"text": "Alex - Paracetamol 500mg"}),
            (ActionType.administer_oral, "patient_bed", {}),
            (ActionType.advance_time, None, {"hours": 1.0}),
            (ActionType.label, "tube_1", {"text": "Alex - t=1h"}),
            (ActionType.draw_blood, "tube_1", {}),
            (ActionType.run_assay, "tube_1", {}),
            (ActionType.dispose_waste, "biohazard_bin", {}),
            (ActionType.wash_hands, "sink", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "02_weigh_without_ppe",
        "actions": [
            (ActionType.tare_balance, "digital_balance", {}),
            (ActionType.weigh, "digital_balance", {"dose_mg": 500.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "03_weigh_without_tare",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.weigh, "digital_balance", {"dose_mg": 500.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "04_high_dose_overdose_alarm",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.tare_balance, "digital_balance", {}),
            (ActionType.weigh, "digital_balance", {"dose_mg": 1500.0}),
            (ActionType.dissolve, "dosing_cup", {}),
            (ActionType.label, "dosing_cup", {"text": "Alex - Paracetamol 1500mg"}),
            (ActionType.administer_oral, "patient_bed", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "05_safe_1000mg_dose",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.tare_balance, "digital_balance", {}),
            (ActionType.weigh, "digital_balance", {"dose_mg": 1000.0}),
            (ActionType.dissolve, "dosing_cup", {}),
            (ActionType.label, "dosing_cup", {"text": "Alex - Paracetamol 1000mg"}),
            (ActionType.administer_oral, "patient_bed", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "06_administer_undissolved",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.tare_balance, "digital_balance", {}),
            (ActionType.weigh, "digital_balance", {"dose_mg": 500.0}),
            (ActionType.label, "dosing_cup", {"text": "Alex - Paracetamol 500mg"}),
            (ActionType.administer_oral, "patient_bed", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "07_administer_unlabeled",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.tare_balance, "digital_balance", {}),
            (ActionType.weigh, "digital_balance", {"dose_mg": 500.0}),
            (ActionType.dissolve, "dosing_cup", {}),
            (ActionType.administer_oral, "patient_bed", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "08_blood_draw_unlabeled_tube",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.tare_balance, "digital_balance", {}),
            (ActionType.weigh, "digital_balance", {"dose_mg": 500.0}),
            (ActionType.dissolve, "dosing_cup", {}),
            (ActionType.label, "dosing_cup", {"text": "Alex - Paracetamol"}),
            (ActionType.administer_oral, "patient_bed", {}),
            (ActionType.advance_time, None, {"hours": 1.0}),
            (ActionType.draw_blood, "tube_1", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "09_blood_draw_before_dose",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.label, "tube_1", {"text": "Baseline t=0"}),
            (ActionType.draw_blood, "tube_1", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "10_advance_time_multiple",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.tare_balance, "digital_balance", {}),
            (ActionType.weigh, "digital_balance", {"dose_mg": 500.0}),
            (ActionType.dissolve, "dosing_cup", {}),
            (ActionType.label, "dosing_cup", {"text": "Alex"}),
            (ActionType.administer_oral, "patient_bed", {}),
            (ActionType.advance_time, None, {"hours": 0.5}),
            (ActionType.advance_time, None, {"hours": 1.0}),
            (ActionType.advance_time, None, {"hours": 2.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "11_three_point_sampling_full",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.tare_balance, "digital_balance", {}),
            (ActionType.weigh, "digital_balance", {"dose_mg": 500.0}),
            (ActionType.dissolve, "dosing_cup", {}),
            (ActionType.label, "dosing_cup", {"text": "Alex - 500mg"}),
            (ActionType.administer_oral, "patient_bed", {}),
            (ActionType.advance_time, None, {"hours": 1.0}),
            (ActionType.label, "tube_1", {"text": "Alex - t=1h"}),
            (ActionType.draw_blood, "tube_1", {}),
            (ActionType.run_assay, "tube_1", {}),
            (ActionType.advance_time, None, {"hours": 2.0}),
            (ActionType.label, "tube_2", {"text": "Alex - t=3h"}),
            (ActionType.draw_blood, "tube_2", {}),
            (ActionType.run_assay, "tube_2", {}),
            (ActionType.advance_time, None, {"hours": 3.0}),
            (ActionType.label, "tube_3", {"text": "Alex - t=6h"}),
            (ActionType.draw_blood, "tube_3", {}),
            (ActionType.run_assay, "tube_3", {}),
            (ActionType.dispose_waste, "biohazard_bin", {}),
            (ActionType.wash_hands, "sink", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "12_early_submit_empty",
        "actions": [
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "13_ppe_only_then_submit",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "14_advance_time_without_dose",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.advance_time, None, {"hours": 2.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "15_draw_blood_already_drawn",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.tare_balance, "digital_balance", {}),
            (ActionType.weigh, "digital_balance", {"dose_mg": 500.0}),
            (ActionType.dissolve, "dosing_cup", {}),
            (ActionType.label, "dosing_cup", {"text": "Alex"}),
            (ActionType.administer_oral, "patient_bed", {}),
            (ActionType.advance_time, None, {"hours": 1.0}),
            (ActionType.label, "tube_1", {"text": "Alex - t=1h"}),
            (ActionType.draw_blood, "tube_1", {}),
            (ActionType.draw_blood, "tube_1", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "16_pour_water_into_cup",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.pour, "dosing_cup", {"volume_ml": 50.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "17_dispose_waste_then_clean",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.tare_balance, "digital_balance", {}),
            (ActionType.weigh, "digital_balance", {"dose_mg": 500.0}),
            (ActionType.dissolve, "dosing_cup", {}),
            (ActionType.label, "dosing_cup", {"text": "Alex"}),
            (ActionType.administer_oral, "patient_bed", {}),
            (ActionType.dispose_waste, "biohazard_bin", {}),
            (ActionType.wash_hands, "sink", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "18_wash_hands_early",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.wash_hands, "sink", {}),
            (ActionType.tare_balance, "digital_balance", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "19_weigh_small_dose_100mg",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.tare_balance, "digital_balance", {}),
            (ActionType.weigh, "digital_balance", {"dose_mg": 100.0}),
            (ActionType.dissolve, "dosing_cup", {}),
            (ActionType.label, "dosing_cup", {"text": "Alex - 100mg"}),
            (ActionType.administer_oral, "patient_bed", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "20_multi_dose_administration",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.tare_balance, "digital_balance", {}),
            (ActionType.weigh, "digital_balance", {"dose_mg": 500.0}),
            (ActionType.dissolve, "dosing_cup", {}),
            (ActionType.label, "dosing_cup", {"text": "Alex - dose 1"}),
            (ActionType.administer_oral, "patient_bed", {}),
            (ActionType.advance_time, None, {"hours": 4.0}),
            (ActionType.weigh, "digital_balance", {"dose_mg": 500.0}),
            (ActionType.dissolve, "dosing_cup", {}),
            (ActionType.administer_oral, "patient_bed", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "21_full_recovery_from_violations",
        "actions": [
            (ActionType.tare_balance, "digital_balance", {}),  # violation without PPE
            (ActionType.weigh, "digital_balance", {"dose_mg": 500.0}),  # violation
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.tare_balance, "digital_balance", {}),
            (ActionType.weigh, "digital_balance", {"dose_mg": 500.0}),
            (ActionType.dissolve, "dosing_cup", {}),
            (ActionType.label, "dosing_cup", {"text": "Alex - Paracetamol"}),
            (ActionType.administer_oral, "patient_bed", {}),
            (ActionType.advance_time, None, {"hours": 1.0}),
            (ActionType.label, "tube_1", {"text": "Alex - t=1h"}),
            (ActionType.draw_blood, "tube_1", {}),
            (ActionType.run_assay, "tube_1", {}),
            (ActionType.dispose_waste, "biohazard_bin", {}),
            (ActionType.wash_hands, "sink", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "22_empty_waste_bin_attempt",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.dispose_waste, "biohazard_bin", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
]


@pytest.mark.parametrize("seq_def", SEQUENCES, ids=[s["name"] for s in SEQUENCES])
def test_pk_ward_golden_equivalence(seq_def: dict[str, Any]):
    """
    Verify identical action outcomes, violations, scores, and grade between
    SPEC_RUNTIME=False (legacy engine) and SPEC_RUNTIME=True (spec runtime).
    """
    seq_name = seq_def["name"]
    actions = seq_def["actions"]

    # 1. Run under legacy engine path (SPEC_RUNTIME = False)
    settings.spec_runtime = False
    sess_old = create_session("pk_ward", f"Old_{seq_name}")
    old_step_results = []
    for action, target, params in actions:
        req = ActionRequest(action=action, target=target, params=params)
        res = apply_action(sess_old, req)
        tot, grd = compute_grade(sess_old.score_parts)
        old_step_results.append((res, dict(sess_old.score_parts), tot, grd))

    # 2. Run under declarative spec runtime (SPEC_RUNTIME = True)
    settings.spec_runtime = True
    sess_new = create_session("pk_ward", f"New_{seq_name}")
    sess_new.session_id = sess_old.session_id  # Align seed for deterministic assay noise comparison
    new_step_results = []
    for action, target, params in actions:
        req = ActionRequest(action=action, target=target, params=params)
        res = apply_action(sess_new, req)
        tot, grd = compute_grade(sess_new.score_parts)
        new_step_results.append((res, dict(sess_new.score_parts), tot, grd))

    # Reset flag to default
    settings.spec_runtime = False

    # 3. Step-by-step equivalence assertions
    assert len(old_step_results) == len(new_step_results)
    for idx, ((r_old, s_old, t_old, g_old), (r_new, s_new, t_new, g_new)) in enumerate(
        zip(old_step_results, new_step_results)
    ):
        step_label = f"Seq '{seq_name}' Step {idx} ({actions[idx][0].value})"

        # Outcome acceptance
        assert r_old.accepted == r_new.accepted, (
            f"{step_label}: accepted mismatch old={r_old.accepted} new={r_new.accepted}"
        )
        # Message
        assert r_old.message == r_new.message, (
            f"{step_label}: message mismatch\nOLD: {r_old.message}\nNEW: {r_new.message}"
        )
        # Violations count and rule IDs
        v_old_ids = [v.rule_id for v in r_old.violations]
        v_new_ids = [v.rule_id for v in r_new.violations]
        assert v_old_ids == v_new_ids, (
            f"{step_label}: violations mismatch old={v_old_ids} new={v_new_ids}"
        )
        # Visuals count
        assert len(r_old.visuals) == len(r_new.visuals), (
            f"{step_label}: visuals count mismatch old={len(r_old.visuals)} new={len(r_new.visuals)}"
        )
        # Dynamic score breakdown
        assert s_old == s_new, (
            f"{step_label}: score breakdown mismatch old={s_old} new={s_new}"
        )
        # Total score
        assert t_old == t_new, (
            f"{step_label}: total score mismatch old={t_old} new={t_new}"
        )
        # Letter grade
        assert g_old == g_new, (
            f"{step_label}: letter grade mismatch old={g_old} new={g_new}"
        )

    # Final session total score and grade equality
    tot_old, grd_old = compute_grade(sess_old.score_parts)
    tot_new, grd_new = compute_grade(sess_new.score_parts)
    assert tot_old == tot_new, (
        f"Final score mismatch in {seq_name}: old={tot_old} new={tot_new}"
    )
    assert grd_old == grd_new, (
        f"Final grade mismatch in {seq_name}: old={grd_old} new={grd_new}"
    )


def test_api_route_switch_under_spec_runtime_pk_ward():
    """Verify route behavior switches dynamically behind SPEC_RUNTIME flag for pk_ward."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # 1. Old path
    settings.spec_runtime = False
    res_old = client.get("/api/lab/experiments/pk_ward")
    assert res_old.status_code == 200
    data_old = res_old.json()
    assert data_old["id"] == "pk_ward"

    # 2. Spec runtime path
    settings.spec_runtime = True
    res_new = client.get("/api/lab/experiments/pk_ward")
    assert res_new.status_code == 200
    data_new = res_new.json()
    assert data_new["id"] == "pk_ward"
    assert "Spec v1.0.0" in data_new["description"]

    # 3. Fallback: reset to default
    settings.spec_runtime = False
    res_fallback = client.get("/api/lab/experiments/pk_ward")
    assert res_fallback.status_code == 200
    assert "Spec v1.0.0" not in res_fallback.json()["description"]
