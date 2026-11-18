"""
Golden-Equivalence Test Suite for Dose Response Lab (dose_lab).
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
        "name": "01_perfect_theophylline_oral",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Jordan", "weight_kg": 70.0, "age_yr": 35.0, "crcl_ml_min": 100.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "theophylline", "route": "oral"}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 300.0}),
            (ActionType.check_renal, "patient_monitor", {}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [0, 1, 2, 4, 8, 12, 24]}),
            (ActionType.predict_window, "prediction_slate", {"predicted_cmax": 6.8, "predicted_time_in_window_h": 10.0}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.debrief_pkpd, "debrief_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "02_vancomycin_2comp_infusion",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Alex", "weight_kg": 75.0, "age_yr": 45.0, "crcl_ml_min": 90.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "vancomycin", "route": "iv_infusion"}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 1000.0, "infusion_duration_h": 1.0}),
            (ActionType.check_renal, "patient_monitor", {}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [0.5, 1, 2, 4, 8, 12, 24]}),
            (ActionType.predict_window, "prediction_slate", {"predicted_cmax": 25.0, "predicted_time_in_window_h": 8.0}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.debrief_pkpd, "debrief_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "03_gentamicin_renal_impairment_violation",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Morgan", "weight_kg": 65.0, "age_yr": 72.0, "crcl_ml_min": 35.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "gentamicin", "route": "iv_infusion"}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 350.0}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [0.5, 1, 4, 8, 12, 24]}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "04_gentamicin_renal_adjusted",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Morgan", "weight_kg": 65.0, "age_yr": 72.0, "crcl_ml_min": 35.0}),
            (ActionType.check_renal, "patient_monitor", {}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "gentamicin", "route": "iv_infusion"}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 150.0}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [0.5, 1, 4, 8, 12, 24]}),
            (ActionType.predict_window, "prediction_slate", {"predicted_cmax": 7.0, "predicted_time_in_window_h": 6.0}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.debrief_pkpd, "debrief_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "05_paracetamol_oral_standard",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Taylor", "weight_kg": 70.0, "age_yr": 30.0, "crcl_ml_min": 110.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "paracetamol", "route": "oral"}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 500.0}),
            (ActionType.check_renal, "patient_monitor", {}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [0.5, 1, 2, 4, 6]}),
            (ActionType.predict_window, "prediction_slate", {"predicted_cmax": 12.0, "predicted_time_in_window_h": 4.0}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.debrief_pkpd, "debrief_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "06_toxic_overdose_alarm",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Jordan", "weight_kg": 70.0, "age_yr": 35.0, "crcl_ml_min": 100.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "theophylline", "route": "oral"}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 1200.0}),
            (ActionType.check_renal, "patient_monitor", {}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [1, 2, 4]}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "07_incompatible_route_error",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Jordan", "weight_kg": 70.0, "age_yr": 35.0, "crcl_ml_min": 100.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "vancomycin", "route": "oral"}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "08_infusion_too_fast_warning",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Alex", "weight_kg": 75.0, "age_yr": 45.0, "crcl_ml_min": 90.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "vancomycin", "route": "iv_infusion"}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 1000.0, "infusion_duration_h": 0.1}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [1, 2, 4]}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "09_simulation_without_prediction",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Jordan", "weight_kg": 70.0, "age_yr": 35.0, "crcl_ml_min": 100.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "theophylline", "route": "oral"}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 300.0}),
            (ActionType.check_renal, "patient_monitor", {}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [0, 1, 2, 4]}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.debrief_pkpd, "debrief_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "10_insufficient_tdm_sampling",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Morgan", "weight_kg": 65.0, "age_yr": 40.0, "crcl_ml_min": 90.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "gentamicin", "route": "iv_infusion"}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 200.0}),
            (ActionType.check_renal, "patient_monitor", {}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [1.0]}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.debrief_pkpd, "debrief_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "11_multi_dose_accumulation",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Alex", "weight_kg": 75.0, "age_yr": 45.0, "crcl_ml_min": 90.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "vancomycin", "route": "iv_infusion"}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 1000.0, "infusion_duration_h": 1.0}),
            (ActionType.set_regimen, "infusion_pump", {"n_doses": 4, "interval_h": 12.0}),
            (ActionType.check_renal, "patient_monitor", {}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [0, 1, 12, 24, 36, 48]}),
            (ActionType.predict_window, "prediction_slate", {"predicted_cmax": 30.0, "predicted_time_in_window_h": 24.0}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.debrief_pkpd, "debrief_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "12_compare_regimens_overlay",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Jordan", "weight_kg": 70.0, "age_yr": 35.0, "crcl_ml_min": 100.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "theophylline", "route": "oral"}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 300.0}),
            (ActionType.check_renal, "patient_monitor", {}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [0, 1, 2, 4, 8, 12]}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.compare_regimens, "pkpd_chart_display", {}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 400.0}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.debrief_pkpd, "debrief_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "13_early_submit_empty",
        "actions": [
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "14_patient_only_then_submit",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Jordan", "weight_kg": 70.0, "age_yr": 35.0, "crcl_ml_min": 100.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "15_amoxicillin_iv_bolus",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Casey", "weight_kg": 68.0, "age_yr": 28.0, "crcl_ml_min": 105.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "amoxicillin", "route": "iv_bolus"}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 500.0}),
            (ActionType.check_renal, "patient_monitor", {}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [0.25, 0.5, 1, 2, 4]}),
            (ActionType.predict_window, "prediction_slate", {"predicted_cmax": 35.0, "predicted_time_in_window_h": 2.0}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.debrief_pkpd, "debrief_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "16_metformin_oral_covariates",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Sam", "weight_kg": 85.0, "age_yr": 55.0, "crcl_ml_min": 75.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "metformin", "route": "oral"}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 850.0}),
            (ActionType.check_renal, "patient_monitor", {}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [1, 2, 4, 8]}),
            (ActionType.predict_window, "prediction_slate", {"predicted_cmax": 2.5, "predicted_time_in_window_h": 4.0}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.debrief_pkpd, "debrief_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "17_debrief_without_simulation",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Jordan", "weight_kg": 70.0, "age_yr": 35.0, "crcl_ml_min": 100.0}),
            (ActionType.debrief_pkpd, "debrief_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "18_elderly_covariates_scaling",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Pat", "weight_kg": 60.0, "age_yr": 82.0, "crcl_ml_min": 45.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "gentamicin", "route": "iv_infusion"}),
            (ActionType.check_renal, "patient_monitor", {}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 120.0}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [1, 4, 8, 12, 24]}),
            (ActionType.predict_window, "prediction_slate", {"predicted_cmax": 6.0, "predicted_time_in_window_h": 5.0}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.debrief_pkpd, "debrief_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "19_high_weight_covariates",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Robin", "weight_kg": 130.0, "age_yr": 40.0, "crcl_ml_min": 120.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "vancomycin", "route": "iv_infusion"}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 1500.0, "infusion_duration_h": 1.5}),
            (ActionType.check_renal, "patient_monitor", {}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [1, 2, 4, 8, 12]}),
            (ActionType.predict_window, "prediction_slate", {"predicted_cmax": 30.0, "predicted_time_in_window_h": 8.0}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.debrief_pkpd, "debrief_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "20_prediction_accuracy_tight",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Jordan", "weight_kg": 70.0, "age_yr": 35.0, "crcl_ml_min": 100.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "theophylline", "route": "oral"}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 300.0}),
            (ActionType.check_renal, "patient_monitor", {}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [0, 1, 2, 4, 8, 12, 24]}),
            (ActionType.predict_window, "prediction_slate", {"predicted_cmax": 6.86, "predicted_time_in_window_h": 8.5}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.debrief_pkpd, "debrief_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "21_multiple_covariate_adjustments",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Jordan", "weight_kg": 70.0, "age_yr": 35.0, "crcl_ml_min": 100.0}),
            (ActionType.set_covariates, "patient_monitor", {"weight_kg": 80.0, "age_yr": 40.0, "crcl_ml_min": 95.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "theophylline", "route": "oral"}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 300.0}),
            (ActionType.check_renal, "patient_monitor", {}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [0, 1, 2, 4, 8]}),
            (ActionType.predict_window, "prediction_slate", {"predicted_cmax": 6.5, "predicted_time_in_window_h": 8.0}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.debrief_pkpd, "debrief_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "22_full_recovery_from_violations",
        "actions": [
            (ActionType.select_patient, "patient_monitor", {"name": "Jordan", "weight_kg": 70.0, "age_yr": 35.0, "crcl_ml_min": 100.0}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 1500.0}),
            (ActionType.select_drug, "infusion_pump", {"drug_id": "theophylline", "route": "oral"}),
            (ActionType.set_dose, "infusion_pump", {"dose_mg": 300.0}),
            (ActionType.check_renal, "patient_monitor", {}),
            (ActionType.set_sampling, "sampling_schedule", {"sample_times_h": [0, 1, 2, 4, 8]}),
            (ActionType.predict_window, "prediction_slate", {"predicted_cmax": 6.8, "predicted_time_in_window_h": 8.0}),
            (ActionType.run_simulation, "pkpd_chart_display", {}),
            (ActionType.debrief_pkpd, "debrief_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
]


@pytest.mark.parametrize("seq_def", SEQUENCES, ids=[s["name"] for s in SEQUENCES])
def test_dose_lab_golden_equivalence(seq_def: dict[str, Any]):
    """
    Verify identical action outcomes, violations, scores, and grade between
    SPEC_RUNTIME=False (legacy engine) and SPEC_RUNTIME=True (spec runtime).
    """
    seq_name = seq_def["name"]
    actions = seq_def["actions"]

    # 1. Run under legacy engine path (SPEC_RUNTIME = False)
    settings.spec_runtime = False
    sess_old = create_session("dose_lab", f"Old_{seq_name}")
    old_step_results = []
    for action, target, params in actions:
        req = ActionRequest(action=action, target=target, params=params)
        res = apply_action(sess_old, req)
        tot, grd = compute_grade(sess_old.score_parts)
        old_step_results.append((res, dict(sess_old.score_parts), tot, grd))

    # 2. Run under declarative spec runtime (SPEC_RUNTIME = True)
    settings.spec_runtime = True
    sess_new = create_session("dose_lab", f"New_{seq_name}")
    sess_new.session_id = sess_old.session_id
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


def test_api_route_switch_under_spec_runtime_dose_lab():
    """Verify route behavior switches dynamically behind SPEC_RUNTIME flag for dose_lab."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # 1. Old path
    settings.spec_runtime = False
    res_old = client.get("/api/lab/experiments/dose_lab")
    assert res_old.status_code == 200
    data_old = res_old.json()
    assert data_old["id"] == "dose_lab"

    # 2. Spec runtime path
    settings.spec_runtime = True
    res_new = client.get("/api/lab/experiments/dose_lab")
    assert res_new.status_code == 200
    data_new = res_new.json()
    assert data_new["id"] == "dose_lab"
    assert "Spec v1.0.0" in data_new["description"]

    # 3. Fallback: reset to default
    settings.spec_runtime = False
    res_fallback = client.get("/api/lab/experiments/dose_lab")
    assert res_fallback.status_code == 200
    assert "Spec v1.0.0" not in res_fallback.json()["description"]
