"""
backend/app/lab/experiments/dose_lab.py
Dose Response Lab Experiment Definition ("dose_lab").

Simulate one- and two-compartment pharmacokinetics, intravenous bolus/infusion
and oral routes, concentration-effect pharmacodynamics (Emax / Hill), and
adult covariate adjustments (weight, age, CrCl renal impairment).
Educational simulation platform. Not medical advice. Not clinical evidence.
"""

from __future__ import annotations

from app.lab.experiments.base import ExperimentDefinition


DOSE_LAB_EXPERIMENT = ExperimentDefinition(
    id="dose_lab",
    title="Dose Response Lab",
    district="pharma",
    description=(
        "Explore multi-compartment PK/PD dynamics across oral and IV routes. "
        "Analyze patient covariates (body weight, age, creatinine clearance), predict target concentration windows, "
        "and observe therapeutic effect curves without risking real human patients."
    ),
    learning_goals=[
        "Differentiate 1-compartment vs 2-compartment distribution phases and multi-exponential decay.",
        "Compare oral absorption kinetics against zero-order IV infusion and instantaneous IV bolus.",
        "Apply allometric weight scaling and calculate CrCl renal impairment dose adjustments.",
        "Forecast peak concentration (Cmax) and time in target therapeutic window.",
        "Link plasma concentration to physiological effect using sigmoid Emax pharmacodynamics.",
        "Analyze multi-dose accumulation ratios and steady-state kinetics.",
    ],
    required_ppe=[],
    apparatus={
        "patient_monitor": {
            "type": "patient_monitor",
            "patient_declared": False,
            "patient_name": "Jordan",
            "weight_kg": 70.0,
            "age_yr": 35.0,
            "crcl_ml_min": 100.0,
            "renal_check_acknowledged": False,
        },
        "infusion_pump": {
            "type": "infusion_pump",
            "drug_id": None,
            "route": None,
            "dose_mg": 0.0,
            "infusion_duration_h": 1.0,
            "n_doses": 1,
            "interval_h": 8.0,
            "status": "ready",
        },
        "sampling_schedule": {
            "type": "sampling_schedule",
            "schedule_declared": False,
            "sample_times_h": [],
        },
        "prediction_slate": {
            "type": "prediction_slate",
            "predicted_cmax": None,
            "predicted_time_in_window_h": None,
            "submitted": False,
        },
        "pkpd_chart_display": {
            "type": "pkpd_chart_display",
            "last_result": None,
            "comparison_result": None,
            "sim_count": 0,
        },
        "debrief_station": {
            "type": "debrief_station",
            "debriefed": False,
        },
    },
    inventory={
        "paracetamol": {
            "type": "drug",
            "name": "Paracetamol",
            "routes": ["oral", "iv_infusion"],
            "max_dose_mg": 1000.0,
        },
        "gentamicin": {
            "type": "drug",
            "name": "Gentamicin",
            "routes": ["iv_bolus", "iv_infusion"],
            "max_dose_mg": 350.0,
        },
        "vancomycin": {
            "type": "drug",
            "name": "Vancomycin",
            "routes": ["iv_infusion"],
            "max_dose_mg": 1500.0,
        },
        "metformin": {
            "type": "drug",
            "name": "Metformin",
            "routes": ["oral"],
            "max_dose_mg": 1000.0,
        },
        "amoxicillin": {
            "type": "drug",
            "name": "Amoxicillin",
            "routes": ["oral", "iv_bolus"],
            "max_dose_mg": 1000.0,
        },
        "theophylline": {
            "type": "drug",
            "name": "Theophylline",
            "routes": ["oral", "iv_infusion"],
            "max_dose_mg": 400.0,
        },
    },
    allowed_actions=[
        "select_patient",
        "select_drug",
        "set_route",
        "set_dose",
        "set_regimen",
        "set_covariates",
        "check_renal",
        "set_sampling",
        "predict_window",
        "run_simulation",
        "compare_regimens",
        "debrief_pkpd",
        "submit_report",
    ],
    protocol=[
        {
            "id": "select_patient",
            "title": "Declare Patient Profile",
            "hint_text": "Select an adult patient profile and confirm baseline weight, age, and renal status.",
            "hint": "Select an adult patient profile and confirm baseline weight, age, and renal status.",
        },
        {
            "id": "select_drug",
            "title": "Select Drug & Administration Route",
            "hint_text": "Select drug and valid route from the clinical formulary (e.g. Paracetamol oral or Gentamicin IV).",
            "hint": "Select drug and valid route from the clinical formulary (e.g. Paracetamol oral or Gentamicin IV).",
        },
        {
            "id": "set_dose",
            "title": "Set Dose & Regimen Parameters",
            "hint_text": "Specify dose within safety boundaries and configure infusion duration or dosing intervals.",
            "hint": "Specify dose within safety boundaries and configure infusion duration or dosing intervals.",
        },
        {
            "id": "check_renal",
            "title": "Acknowledge Renal Function Status",
            "hint_text": "Check creatinine clearance (CrCl); if < 60 mL/min, confirm renal dose adjustment.",
            "hint": "Check creatinine clearance (CrCl); if < 60 mL/min, confirm renal dose adjustment.",
        },
        {
            "id": "set_sampling",
            "title": "Choose Sampling Schedule",
            "hint_text": "Choose blood sampling schedule (e.g. 0-24h monitoring) to capture Cmax and terminal elimination.",
            "hint": "Choose blood sampling schedule (e.g. 0-24h monitoring) to capture Cmax and terminal elimination.",
        },
        {
            "id": "predict_window",
            "title": "Predict Target Window Response",
            "hint_text": "Record your scientific prediction for peak concentration and duration in target window.",
            "hint": "Record your scientific prediction for peak concentration and duration in target window.",
        },
        {
            "id": "run_simulation",
            "title": "Execute PK/PD Simulation",
            "hint_text": "Run the deterministic simulation engine and examine concentration and effect curves.",
            "hint": "Run the deterministic simulation engine and examine concentration and effect curves.",
        },
        {
            "id": "debrief_pkpd",
            "title": "Debrief Pharmacometric Telemetry",
            "hint_text": "Analyze observed Cmax, AUC, and time-in-target window before finalizing session report.",
            "hint": "Analyze observed Cmax, AUC, and time-in-target window before finalizing session report.",
        },
    ],
    scoring_weights={
        "safety": 40,
        "accuracy": 30,
        "technique": 20,
        "protocol": 10,
    },
    rules=[
        {"rule_id": "D1", "title": "Maximum Safe Single Dose", "explanation": "Administered dose must not exceed the maximum recommended adult single dose from drug specifications."},
        {"rule_id": "D2", "title": "Renal Impairment Adjustment", "explanation": "Patients with renal impairment (CrCl < 60 mL/min) receiving renally cleared drugs require dose reduction."},
        {"rule_id": "D3", "title": "Bioavailability & Route Compatibility", "explanation": "Selected administration route must be compatible with drug bioavailability."},
        {"rule_id": "D4", "title": "Adult Covariate Boundaries", "explanation": "Patient parameters must remain within adult boundary limits (Age 18-90, Weight 40-150 kg, CrCl 15-150 mL/min)."},
        {"rule_id": "D5", "title": "Therapeutic Drug Monitoring Sampling", "explanation": "Narrow therapeutic index drugs require at least 3 blood sampling observation timepoints."},
        {"rule_id": "D6", "title": "Safe Infusion Duration", "explanation": "Intravenous infusions must not be administered in under 15 minutes (< 0.25h) to avoid adverse reactions."},
        {"rule_id": "D7", "title": "Target Window Prediction", "explanation": "Enter predicted peak concentration and target window duration before executing simulation."},
        {"rule_id": "D8", "title": "Toxic Peak Concentration Avoidance", "explanation": "Simulated Cmax must not exceed the toxic concentration threshold."},
    ],
)
