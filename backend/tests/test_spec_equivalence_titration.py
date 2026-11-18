"""
Golden-Equivalence Test Suite for Titration Bench.
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


SEQUENCES: list[dict[str, Any]] = [
    {
        "name": "01_perfect_titration_hcl",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.rinse_burette, "burette", {}),
            (ActionType.fill_burette, "burette", {}),
            (ActionType.pipette_analyte, "conical_flask", {}),
            (ActionType.add_indicator, "conical_flask", {}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.swirl, "conical_flask", {}),
            (ActionType.record_endpoint, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.dispose_waste, "chemical_waste_bin", {}),
            (ActionType.wash_hands, "sink", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "02_no_ppe_chemical_handling",
        "actions": [
            (ActionType.rinse_burette, "burette", {}),
            (ActionType.fill_burette, "burette", {}),
            (ActionType.pipette_analyte, "conical_flask", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "03_fill_without_rinse",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.fill_burette, "burette", {}),
            (ActionType.pipette_analyte, "conical_flask", {}),
            (ActionType.add_indicator, "conical_flask", {}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.record_endpoint, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "04_slight_overshoot_26ml",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.rinse_burette, "burette", {}),
            (ActionType.fill_burette, "burette", {}),
            (ActionType.pipette_analyte, "conical_flask", {}),
            (ActionType.add_indicator, "conical_flask", {}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 26.0}),
            (ActionType.swirl, "conical_flask", {}),
            (ActionType.record_endpoint, "conical_flask", {"volume_ml": 26.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "05_severe_overshoot_40ml",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.rinse_burette, "burette", {}),
            (ActionType.fill_burette, "burette", {}),
            (ActionType.pipette_analyte, "conical_flask", {}),
            (ActionType.add_indicator, "conical_flask", {}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 40.0}),
            (ActionType.swirl, "conical_flask", {}),
            (ActionType.record_endpoint, "conical_flask", {"volume_ml": 40.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "06_under_titration_18ml",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.rinse_burette, "burette", {}),
            (ActionType.fill_burette, "burette", {}),
            (ActionType.pipette_analyte, "conical_flask", {}),
            (ActionType.add_indicator, "conical_flask", {}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 18.0}),
            (ActionType.swirl, "conical_flask", {}),
            (ActionType.record_endpoint, "conical_flask", {"volume_ml": 18.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "07_titrate_without_indicator",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.rinse_burette, "burette", {}),
            (ActionType.fill_burette, "burette", {}),
            (ActionType.pipette_analyte, "conical_flask", {}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.record_endpoint, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "08_titrate_without_analyte",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.rinse_burette, "burette", {}),
            (ActionType.fill_burette, "burette", {}),
            (ActionType.add_indicator, "conical_flask", {}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 10.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "09_no_swirl_performed",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.rinse_burette, "burette", {}),
            (ActionType.fill_burette, "burette", {}),
            (ActionType.pipette_analyte, "conical_flask", {}),
            (ActionType.add_indicator, "conical_flask", {}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.record_endpoint, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "10_stepwise_incremental_titration",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.rinse_burette, "burette", {}),
            (ActionType.fill_burette, "burette", {}),
            (ActionType.pipette_analyte, "conical_flask", {}),
            (ActionType.add_indicator, "conical_flask", {}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 10.0}),
            (ActionType.swirl, "conical_flask", {}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 10.0}),
            (ActionType.swirl, "conical_flask", {}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 5.0}),
            (ActionType.swirl, "conical_flask", {}),
            (ActionType.record_endpoint, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "11_early_submit_empty",
        "actions": [
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "12_ppe_only_then_submit",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "13_methyl_orange_indicator",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.rinse_burette, "burette", {}),
            (ActionType.fill_burette, "burette", {}),
            (ActionType.pipette_analyte, "conical_flask", {}),
            (ActionType.add_indicator, "conical_flask", {"indicator": "methyl_orange"}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.swirl, "conical_flask", {}),
            (ActionType.record_endpoint, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "14_bromothymol_blue_indicator",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.rinse_burette, "burette", {}),
            (ActionType.fill_burette, "burette", {}),
            (ActionType.pipette_analyte, "conical_flask", {}),
            (ActionType.add_indicator, "conical_flask", {"indicator": "bromothymol_blue"}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.swirl, "conical_flask", {}),
            (ActionType.record_endpoint, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "15_ph_meter_potentiometric_readings",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.rinse_burette, "burette", {}),
            (ActionType.fill_burette, "burette", {}),
            (ActionType.pipette_analyte, "conical_flask", {}),
            (ActionType.read_ph_meter, "conical_flask", {}),
            (ActionType.add_indicator, "conical_flask", {}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.read_ph_meter, "conical_flask", {}),
            (ActionType.record_endpoint, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "16_dispose_waste_then_clean",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.rinse_burette, "burette", {}),
            (ActionType.fill_burette, "burette", {}),
            (ActionType.pipette_analyte, "conical_flask", {}),
            (ActionType.add_indicator, "conical_flask", {}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.swirl, "conical_flask", {}),
            (ActionType.record_endpoint, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.dispose_waste, "chemical_waste_bin", {}),
            (ActionType.wash_hands, "sink", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "17_wash_hands_early",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.wash_hands, "sink", {}),
            (ActionType.rinse_burette, "burette", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "18_overfilling_burette",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.fill_burette, "burette", {"volume_ml": 60.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "19_pipette_twice",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.pipette_analyte, "conical_flask", {}),
            (ActionType.pipette_analyte, "conical_flask", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "20_weak_acid_acetic",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.rinse_burette, "burette", {}),
            (ActionType.fill_burette, "burette", {}),
            (ActionType.pipette_analyte, "conical_flask", {"analyte": "acetic_0.1M"}),
            (ActionType.add_indicator, "conical_flask", {}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.swirl, "conical_flask", {}),
            (ActionType.record_endpoint, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "21_fine_endpoint_precision_25_05",
        "actions": [
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.rinse_burette, "burette", {}),
            (ActionType.fill_burette, "burette", {}),
            (ActionType.pipette_analyte, "conical_flask", {}),
            (ActionType.add_indicator, "conical_flask", {}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.swirl, "conical_flask", {}),
            (ActionType.record_endpoint, "conical_flask", {"volume_ml": 25.05}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "22_full_recovery_from_violations",
        "actions": [
            (ActionType.rinse_burette, "burette", {}),  # violation without PPE
            (ActionType.fill_burette, "burette", {}),
            (ActionType.wear_ppe, "goggles", {}),
            (ActionType.wash_hands, "sink", {}),
            (ActionType.pipette_analyte, "conical_flask", {}),
            (ActionType.add_indicator, "conical_flask", {}),
            (ActionType.titrate, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.swirl, "conical_flask", {}),
            (ActionType.record_endpoint, "conical_flask", {"volume_ml": 25.0}),
            (ActionType.dispose_waste, "chemical_waste_bin", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
]


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


@pytest.mark.parametrize("seq_def", SEQUENCES, ids=[s["name"] for s in SEQUENCES])
def test_titration_bench_golden_equivalence(seq_def: dict[str, Any]):
    """
    Verify identical action outcomes, violations, scores, and grade between
    SPEC_RUNTIME=False (legacy engine) and SPEC_RUNTIME=True (spec runtime).
    """
    seq_name = seq_def["name"]
    actions = seq_def["actions"]

    # 1. Run under legacy engine path (SPEC_RUNTIME = False)
    settings.spec_runtime = False
    sess_old = create_session("titration_bench", f"Old_{seq_name}")
    old_step_results = []
    for action, target, params in actions:
        req = ActionRequest(action=action, target=target, params=params)
        res = apply_action(sess_old, req)
        tot, grd = compute_grade(sess_old.score_parts)
        old_step_results.append((res, dict(sess_old.score_parts), tot, grd))

    # 2. Run under declarative spec runtime (SPEC_RUNTIME = True)
    settings.spec_runtime = True
    sess_new = create_session("titration_bench", f"New_{seq_name}")
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


def test_api_route_switch_under_spec_runtime():
    """Verify route behavior switches dynamically behind SPEC_RUNTIME flag with fallback."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # 1. Old path
    settings.spec_runtime = False
    res_old = client.get("/api/lab/experiments/titration_bench")
    assert res_old.status_code == 200
    data_old = res_old.json()
    assert data_old["id"] == "titration_bench"

    # 2. Spec runtime path
    settings.spec_runtime = True
    res_new = client.get("/api/lab/experiments/titration_bench")
    assert res_new.status_code == 200
    data_new = res_new.json()
    assert data_new["id"] == "titration_bench"
    assert "Spec v1.0.0" in data_new["description"]

    # 3. Fallback: reset to default
    settings.spec_runtime = False
    res_fallback = client.get("/api/lab/experiments/titration_bench")
    assert res_fallback.status_code == 200
    assert "Spec v1.0.0" not in res_fallback.json()["description"]
