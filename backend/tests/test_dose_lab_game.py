"""
backend/tests/test_dose_lab_game.py
Comprehensive test suite for Dose Response Lab experiment ("dose_lab").
Covers safety rules D1-D8, scoring components, visual directives,
report card generation, and action progression.
"""

from __future__ import annotations

import pytest
from app.lab.engine import create_session, apply_action, get_available_actions
from app.lab.experiments import get_experiment, list_experiments
from app.lab.models import ActionRequest, ActionType, LabSession
from app.lab.rules import check_safety_rules


# ---------------------------------------------------------------------------
# 1. Registration & Initial State
# ---------------------------------------------------------------------------

def test_dose_lab_registered():
    """Verify dose_lab is registered and discoverable in pharma district."""
    exp = get_experiment("dose_lab")
    assert exp is not None
    assert exp.id == "dose_lab"
    assert exp.district == "pharma"
    assert len(exp.protocol) >= 5
    assert "select_drug" in exp.allowed_actions

    # Check pharma district experiments
    pharma_exps = list_experiments(district="pharma")
    assert any(e.id == "dose_lab" for e in pharma_exps)


def test_dose_lab_initial_state():
    """Verify initial apparatus state and default score breakdown."""
    session = create_session("dose_lab", nickname="DrDose")
    assert session.experiment_id == "dose_lab"
    assert session.status == "active"
    assert session.score_parts["safety"] == 40
    assert session.score_parts["technique"] == 20
    assert session.score_parts["protocol"] == 10
    assert session.score_parts["accuracy"] == 30

    assert "patient_monitor" in session.apparatus_state
    assert "infusion_pump" in session.apparatus_state
    assert "sampling_schedule" in session.apparatus_state
    assert "prediction_slate" in session.apparatus_state
    assert "pkpd_chart_display" in session.apparatus_state


# ---------------------------------------------------------------------------
# 2. Covariates and Rule D4
# ---------------------------------------------------------------------------

def test_dose_lab_select_patient_and_covariates():
    """Test declaring patient profile and updating adult covariates."""
    session = create_session("dose_lab", nickname="DrDose")
    res = apply_action(session, ActionRequest(action=ActionType.select_patient, target="preset_standard_70kg"))
    assert res.accepted
    mon = session.apparatus_state["patient_monitor"]
    assert mon["patient_declared"] is True
    assert mon["weight_kg"] == 70.0
    assert any(v.get("covariate_card") is not None for v in res.visuals)


def test_dose_lab_set_covariates_within_bounds():
    """Test modifying covariates within valid adult bounds."""
    session = create_session("dose_lab", nickname="DrDose")
    res = apply_action(session, ActionRequest(
        action=ActionType.set_covariates,
        params={"weight_kg": 85.0, "age_yr": 55.0, "crcl_ml_min": 75.0}
    ))
    assert res.accepted
    assert len(res.violations) == 0
    mon = session.apparatus_state["patient_monitor"]
    assert mon["weight_kg"] == 85.0
    assert mon["age_yr"] == 55.0
    assert mon["crcl_ml_min"] == 75.0


def test_dose_lab_rule_d4_covariate_bounds():
    """D4: Requesting out-of-bounds covariates triggers penalty -5 and clamps to boundary."""
    session = create_session("dose_lab", nickname="DrDose")
    # Attempt pediatric age (10 yr), sub-40kg weight (30kg), low CrCl (5 mL/min)
    res = apply_action(session, ActionRequest(
        action=ActionType.set_covariates,
        params={"weight_kg": 30.0, "age_yr": 10.0, "crcl_ml_min": 5.0}
    ))
    assert res.accepted
    d4_viols = [v for v in res.violations if v.rule_id == "D4"]
    assert len(d4_viols) == 1
    assert d4_viols[0].penalty_points == 5
    assert d4_viols[0].severity == "warning"

    # Verify clamped to boundaries
    mon = session.apparatus_state["patient_monitor"]
    assert mon["weight_kg"] == 40.0
    assert mon["age_yr"] == 18.0
    assert mon["crcl_ml_min"] == 15.0


# ---------------------------------------------------------------------------
# 3. Drug Selection, Route, and Rule D3
# ---------------------------------------------------------------------------

def test_dose_lab_select_drug_and_route():
    """Test selecting a valid drug and compatible route."""
    session = create_session("dose_lab", nickname="DrDose")
    res1 = apply_action(session, ActionRequest(action=ActionType.select_drug, target="paracetamol"))
    assert res1.accepted
    pump = session.apparatus_state["infusion_pump"]
    assert pump["drug_id"] == "paracetamol"

    res2 = apply_action(session, ActionRequest(action=ActionType.set_route, target="oral"))
    assert res2.accepted
    assert len(res2.violations) == 0
    assert pump["route"] == "oral"


def test_dose_lab_rule_d3_route_mismatch():
    """D3: Oral route given for zero-bioavailability drug triggers penalty -10."""
    session = create_session("dose_lab", nickname="DrDose")
    apply_action(session, ActionRequest(action=ActionType.select_drug, target="gentamicin"))
    res = apply_action(session, ActionRequest(action=ActionType.set_route, target="oral"))
    d3_viols = [v for v in res.violations if v.rule_id == "D3"]
    assert len(d3_viols) == 1
    assert d3_viols[0].penalty_points == 10
    assert d3_viols[0].severity == "major"


# ---------------------------------------------------------------------------
# 4. Dose, Regimen, and Rule D1, D6
# ---------------------------------------------------------------------------

def test_dose_lab_rule_d1_max_dose():
    """D1: Setting dose above max_game_dose_mg triggers penalty -15."""
    session = create_session("dose_lab", nickname="DrDose")
    apply_action(session, ActionRequest(action=ActionType.select_drug, target="theophylline"))  # max 400 mg
    res = apply_action(session, ActionRequest(action=ActionType.set_dose, params={"dose_mg": 800.0}))
    d1_viols = [v for v in res.violations if v.rule_id == "D1"]
    assert len(d1_viols) == 1
    assert d1_viols[0].penalty_points == 15
    assert d1_viols[0].severity == "major"


def test_dose_lab_rule_d6_infusion_rate():
    """D6: IV infusion duration < 15 min (0.25h) triggers penalty -15."""
    session = create_session("dose_lab", nickname="DrDose")
    apply_action(session, ActionRequest(action=ActionType.select_drug, target="vancomycin"))
    apply_action(session, ActionRequest(action=ActionType.set_route, target="iv_infusion"))
    apply_action(session, ActionRequest(action=ActionType.set_dose, params={"dose_mg": 1000.0}))
    res = apply_action(session, ActionRequest(
        action=ActionType.set_regimen,
        params={"infusion_duration_h": 0.10, "interval_h": 12.0}
    ))
    d6_viols = [v for v in res.violations if v.rule_id == "D6"]
    assert len(d6_viols) == 1
    assert d6_viols[0].penalty_points == 15
    assert d6_viols[0].severity == "major"


# ---------------------------------------------------------------------------
# 5. Renal Impairment and Rule D2
# ---------------------------------------------------------------------------

def test_dose_lab_rule_d2_renal_impairment_unadjusted():
    """D2: Unadjusted dose in renal impairment (CrCl < 60, fe > 0.4) triggers penalty -20."""
    session = create_session("dose_lab", nickname="DrDose")
    # Patient with severe renal impairment (CrCl 30)
    apply_action(session, ActionRequest(
        action=ActionType.set_covariates,
        params={"weight_kg": 70.0, "age_yr": 70.0, "crcl_ml_min": 30.0}
    ))
    # Gentamicin: fe = 0.95, max 350 mg. Recommended renal dose = 350 * (30/120) = 87.5 mg
    apply_action(session, ActionRequest(action=ActionType.select_drug, target="gentamicin"))
    apply_action(session, ActionRequest(action=ActionType.set_route, target="iv_bolus"))
    # Attempting full 300 mg unadjusted dose without renal check acknowledgement
    res = apply_action(session, ActionRequest(action=ActionType.set_dose, params={"dose_mg": 300.0}))
    d2_viols = [v for v in res.violations if v.rule_id == "D2"]
    assert len(d2_viols) == 1
    assert d2_viols[0].penalty_points == 20
    assert d2_viols[0].severity == "critical"


def test_dose_lab_check_renal_and_adjusted_dose():
    """Acknowledge renal impairment and reduce dose avoids D2 penalty."""
    session = create_session("dose_lab", nickname="DrDose")
    apply_action(session, ActionRequest(
        action=ActionType.set_covariates,
        params={"weight_kg": 70.0, "age_yr": 70.0, "crcl_ml_min": 30.0}
    ))
    apply_action(session, ActionRequest(action=ActionType.select_drug, target="gentamicin"))
    # Acknowledge renal function
    res_ack = apply_action(session, ActionRequest(action=ActionType.check_renal))
    assert res_ack.accepted
    assert session.apparatus_state["patient_monitor"]["renal_check_acknowledged"] is True

    # Titrate dose to 80 mg (within 87.5 mg renal limit)
    res_dose = apply_action(session, ActionRequest(action=ActionType.set_dose, params={"dose_mg": 80.0}))
    d2_viols = [v for v in res_dose.violations if v.rule_id == "D2"]
    assert len(d2_viols) == 0


# ---------------------------------------------------------------------------
# 6. Sampling Schedule, Prediction, and Rules D5, D7, D8
# ---------------------------------------------------------------------------

def test_dose_lab_rule_d5_nti_sampling():
    """D5: Narrow therapeutic index drug with < 3 sampling timepoints triggers penalty -10."""
    session = create_session("dose_lab", nickname="DrDose")
    apply_action(session, ActionRequest(action=ActionType.select_patient, target="preset_standard_70kg"))
    apply_action(session, ActionRequest(action=ActionType.select_drug, target="theophylline"))  # NTI drug
    apply_action(session, ActionRequest(action=ActionType.set_route, target="oral"))
    apply_action(session, ActionRequest(action=ActionType.set_dose, params={"dose_mg": 300.0}))
    apply_action(session, ActionRequest(action=ActionType.predict_window, params={"predicted_cmax": 12.0, "predicted_time_in_window_h": 8.0}))

    # Sampling with only 2 points
    apply_action(session, ActionRequest(action=ActionType.set_sampling, params={"schedule": "1.0, 4.0"}))
    res = apply_action(session, ActionRequest(action=ActionType.run_simulation))
    d5_viols = [v for v in res.violations if v.rule_id == "D5"]
    assert len(d5_viols) == 1
    assert d5_viols[0].penalty_points == 10


def test_dose_lab_rule_d7_missing_prediction():
    """D7: Running simulation without predicting window response triggers penalty -5."""
    session = create_session("dose_lab", nickname="DrDose")
    apply_action(session, ActionRequest(action=ActionType.select_patient, target="preset_standard_70kg"))
    apply_action(session, ActionRequest(action=ActionType.select_drug, target="paracetamol"))
    apply_action(session, ActionRequest(action=ActionType.set_route, target="oral"))
    apply_action(session, ActionRequest(action=ActionType.set_dose, params={"dose_mg": 500.0}))
    apply_action(session, ActionRequest(action=ActionType.set_sampling, params={"schedule": "0, 1, 2, 4, 8, 12, 24"}))

    # Omit predict_window
    res = apply_action(session, ActionRequest(action=ActionType.run_simulation))
    d7_viols = [v for v in res.violations if v.rule_id == "D7"]
    assert len(d7_viols) == 1
    assert d7_viols[0].penalty_points == 5


def test_dose_lab_rule_d8_toxic_peak():
    """D8: High dose causing Cmax > c_toxic triggers penalty -25 and toxicity risk."""
    session = create_session("dose_lab", nickname="DrDose")
    apply_action(session, ActionRequest(action=ActionType.select_patient, target="preset_standard_70kg"))
    apply_action(session, ActionRequest(action=ActionType.select_drug, target="theophylline"))  # window 10-20, toxic > 30
    apply_action(session, ActionRequest(action=ActionType.set_route, target="oral"))
    # Setting high dose causing severe toxicity
    session.apparatus_state["infusion_pump"]["dose_mg"] = 1600.0
    apply_action(session, ActionRequest(action=ActionType.set_sampling, params={"schedule": "0, 1, 2, 4, 8, 12, 24"}))
    apply_action(session, ActionRequest(action=ActionType.predict_window, params={"predicted_cmax": 35.0, "predicted_time_in_window_h": 2.0}))

    res = apply_action(session, ActionRequest(action=ActionType.run_simulation))
    d8_viols = [v for v in res.violations if v.rule_id == "D8"]
    assert len(d8_viols) == 1
    assert d8_viols[0].penalty_points == 25
    assert d8_viols[0].severity == "critical"


# ---------------------------------------------------------------------------
# 7. Visual Directives and Regimen Comparison
# ---------------------------------------------------------------------------

def test_dose_lab_visual_directives():
    """Verify visual directives emitted during run_simulation (curve, effect_curve, window)."""
    session = create_session("dose_lab", nickname="DrDose")
    apply_action(session, ActionRequest(action=ActionType.select_patient, target="preset_standard_70kg"))
    apply_action(session, ActionRequest(action=ActionType.select_drug, target="paracetamol"))
    apply_action(session, ActionRequest(action=ActionType.set_route, target="oral"))
    apply_action(session, ActionRequest(action=ActionType.set_dose, params={"dose_mg": 500.0}))
    apply_action(session, ActionRequest(action=ActionType.set_sampling, params={"schedule": "0, 1, 2, 4, 8, 12, 24"}))
    apply_action(session, ActionRequest(action=ActionType.predict_window, params={"predicted_cmax": 7.0, "predicted_time_in_window_h": 0.0}))

    res = apply_action(session, ActionRequest(action=ActionType.run_simulation))
    assert res.accepted
    readout = next(v for v in res.visuals if v.get("label") == "PK/PD RESULTS")
    assert "curve" in readout and len(readout["curve"]) > 10
    assert "effect_curve" in readout and len(readout["effect_curve"]) > 10
    assert "window" in readout


def test_dose_lab_compare_regimens():
    """Verify comparing active regimen pins baseline curve for overlay."""
    session = create_session("dose_lab", nickname="DrDose")
    apply_action(session, ActionRequest(action=ActionType.select_patient, target="preset_standard_70kg"))
    apply_action(session, ActionRequest(action=ActionType.select_drug, target="paracetamol"))
    apply_action(session, ActionRequest(action=ActionType.set_route, target="oral"))
    apply_action(session, ActionRequest(action=ActionType.set_dose, params={"dose_mg": 500.0}))
    apply_action(session, ActionRequest(action=ActionType.set_sampling, params={"schedule": "0, 1, 2, 4, 8, 12, 24"}))
    apply_action(session, ActionRequest(action=ActionType.predict_window, params={"predicted_cmax": 7.0, "predicted_time_in_window_h": 0.0}))
    apply_action(session, ActionRequest(action=ActionType.run_simulation))

    res_comp = apply_action(session, ActionRequest(action=ActionType.compare_regimens))
    assert res_comp.accepted
    chart = session.apparatus_state["pkpd_chart_display"]
    assert chart["comparison_result"] is not None
    assert chart["comparison_result"]["dose_mg"] == 500.0


def test_dose_lab_debrief_pkpd():
    """Verify pharmacometric debrief action updates debrief station and protocol."""
    session = create_session("dose_lab", nickname="DrDose")
    res = apply_action(session, ActionRequest(action=ActionType.debrief_pkpd))
    assert res.accepted
    assert session.apparatus_state["debrief_station"]["debriefed"] is True
    assert "debrief_pkpd" in session.protocol_progress


# ---------------------------------------------------------------------------
# 8. Scoring Engine Tests
# ---------------------------------------------------------------------------

def test_dose_lab_scoring_accuracy_and_technique():
    """Verify scoring logic awards maximum points for accurate prediction and good technique."""
    session = create_session("dose_lab", nickname="DrDose")
    apply_action(session, ActionRequest(action=ActionType.select_patient, target="preset_standard_70kg"))
    apply_action(session, ActionRequest(action=ActionType.check_renal))
    apply_action(session, ActionRequest(action=ActionType.select_drug, target="theophylline"))
    apply_action(session, ActionRequest(action=ActionType.set_route, target="oral"))
    apply_action(session, ActionRequest(action=ActionType.set_dose, params={"dose_mg": 350.0}))
    apply_action(session, ActionRequest(action=ActionType.set_sampling, params={"schedule": "0, 1, 2, 4, 8, 12, 24"}))

    # Accurate prediction for 350 mg theophylline (Cmax around 8-9 mg/L)
    apply_action(session, ActionRequest(action=ActionType.predict_window, params={"predicted_cmax": 8.5, "predicted_time_in_window_h": 0.0}))
    apply_action(session, ActionRequest(action=ActionType.run_simulation))

    # Technique: renal checked (7), dose set (7), multi-point sampling (6) = 20 max
    assert session.score_parts["technique"] == 20
    # Accuracy: Cmax error < 15% and time in window error < 20% -> 30 max
    assert session.score_parts["accuracy"] >= 25
    # Safety: no violations -> 40
    assert session.score_parts["safety"] == 40


def test_dose_lab_scoring_poor_prediction():
    """Verify poor student prediction yields lower accuracy score."""
    session = create_session("dose_lab", nickname="DrDose")
    apply_action(session, ActionRequest(action=ActionType.select_patient, target="preset_standard_70kg"))
    apply_action(session, ActionRequest(action=ActionType.select_drug, target="paracetamol"))
    apply_action(session, ActionRequest(action=ActionType.set_route, target="oral"))
    apply_action(session, ActionRequest(action=ActionType.set_dose, params={"dose_mg": 500.0}))
    apply_action(session, ActionRequest(action=ActionType.set_sampling, params={"schedule": "0, 1, 2, 4"}))

    # Wildly inaccurate prediction
    apply_action(session, ActionRequest(action=ActionType.predict_window, params={"predicted_cmax": 50.0, "predicted_time_in_window_h": 20.0}))
    apply_action(session, ActionRequest(action=ActionType.run_simulation))

    assert session.score_parts["accuracy"] <= 10


# ---------------------------------------------------------------------------
# 9. Report Card Generation and Finish Session
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dose_lab_report_card_generation():
    """Verify /sessions/{session_id}/finish generates comprehensive markdown debrief."""
    from app.routes.lab import finish_session
    from app import db as _db

    await _db.init_db()
    session = create_session("dose_lab", nickname="PharmStudent")
    await _db.upsert_lab_session(session.model_dump())

    # Walk through minimal clean protocol
    apply_action(session, ActionRequest(action=ActionType.select_patient, target="preset_standard_70kg"))
    apply_action(session, ActionRequest(action=ActionType.check_renal))
    apply_action(session, ActionRequest(action=ActionType.select_drug, target="paracetamol"))
    apply_action(session, ActionRequest(action=ActionType.set_route, target="oral"))
    apply_action(session, ActionRequest(action=ActionType.set_dose, params={"dose_mg": 500.0}))
    apply_action(session, ActionRequest(action=ActionType.set_sampling, params={"schedule": "0, 1, 2, 4, 8, 12, 24"}))
    apply_action(session, ActionRequest(action=ActionType.predict_window, params={"predicted_cmax": 6.8, "predicted_time_in_window_h": 0.0}))
    apply_action(session, ActionRequest(action=ActionType.run_simulation))
    apply_action(session, ActionRequest(action=ActionType.debrief_pkpd))
    await _db.upsert_lab_session(session.model_dump())

    res = await finish_session(session.session_id)
    assert res.experiment_id == "dose_lab"
    assert res.score >= 70
    assert res.report_markdown is not None
    assert "Orbis Lab Pharmacometric Analytical Report: Dose Response Lab" in res.report_markdown
    assert "Simulated vs. Predicted Metrics" in res.report_markdown
    assert "Educational simulation, not medical advice, not clinical evidence" in res.report_markdown


# ---------------------------------------------------------------------------
# 10. Available Actions Progression
# ---------------------------------------------------------------------------

def test_dose_lab_available_actions_progression():
    """Verify context-aware action enablement and disabled reasons."""
    session = create_session("dose_lab", nickname="DrDose")
    actions = get_available_actions(session)
    act_map = {a.action: a for a in actions}

    # Initially, select_patient is enabled, but run_simulation is disabled
    assert act_map[ActionType.select_patient].enabled is True
    assert act_map[ActionType.run_simulation].enabled is False
    assert "Declare patient" in (act_map[ActionType.run_simulation].disabled_reason or "")

    # Declare patient
    apply_action(session, ActionRequest(action=ActionType.select_patient, target="preset_standard_70kg"))
    actions2 = get_available_actions(session)
    act_map2 = {a.action: a for a in actions2}
    assert act_map2[ActionType.check_renal].enabled is True
