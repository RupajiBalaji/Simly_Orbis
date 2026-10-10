"""
Pharmacokinetics Clinical Ward Experiment Definition ("pk_ward").
"""

from __future__ import annotations

from app.lab.experiments.base import ExperimentDefinition


PK_WARD_EXPERIMENT = ExperimentDefinition(
    id="pk_ward",
    title="Pharmacokinetics Clinical Ward",
    district="pharma",
    description=(
        "Manage clinical oral drug dosing, timed venous plasma blood draws, "
        "and analytical centrifuge assays for an inpatient receiving paracetamol."
    ),
    learning_goals=[
        "Master laboratory personal protective equipment (PPE) requirements.",
        "Accurately tare and weigh medicinal powders on an analytical digital balance.",
        "Perform aseptic dissolution and rigorous sample labelling.",
        "Administer oral pharmacotherapy and monitor plasma concentration dynamics.",
        "Conduct timed venous sampling and clinical centrifuge/fluorescence assays.",
        "Segregate biomedical and chemical waste according to safety standards.",
    ],
    required_ppe=["goggles", "gloves", "coat"],
    apparatus={
        "digital_balance": {
            "type": "balance",
            "power": "on",
            "tared": False,
            "reading_g": 0.0,
        },
        "dosing_cup": {
            "type": "container",
            "labeled": False,
            "label_text": "",
            "contents": {},
            "volume_ml": 0.0,
            "dissolved": False,
            "clean": True,
        },
        "water_jug": {
            "type": "source",
            "volume_ml": 1000.0,
        },
        "patient_bed": {
            "type": "patient_station",
            "patient": {
                "id": "patient_alex",
                "name": "Alex",
                "weight_kg": 70.0,
                "clearance_multiplier": 1.0,
                "drug_id": "paracetamol",
                "doses_administered": [],
            },
        },
        "tube_1": {
            "type": "sample_tube",
            "id": "tube_1",
            "labeled": False,
            "label_text": "",
            "drawn": False,
            "analyzed": False,
            "sample_time_h": None,
            "concentration_mg_l": None,
            "assayed_concentration_mg_l": None,
        },
        "tube_2": {
            "type": "sample_tube",
            "id": "tube_2",
            "labeled": False,
            "label_text": "",
            "drawn": False,
            "analyzed": False,
            "sample_time_h": None,
            "concentration_mg_l": None,
            "assayed_concentration_mg_l": None,
        },
        "tube_3": {
            "type": "sample_tube",
            "id": "tube_3",
            "labeled": False,
            "label_text": "",
            "drawn": False,
            "analyzed": False,
            "sample_time_h": None,
            "concentration_mg_l": None,
            "assayed_concentration_mg_l": None,
        },
        "label_pen": {
            "type": "tool",
            "ready": True,
        },
        "assay_analyzer": {
            "type": "analyzer",
            "powered": True,
            "busy": False,
            "last_result": None,
        },
        "biohazard_bin": {
            "type": "waste_bin",
            "waste_type": "biohazard",
            "items": [],
        },
        "chemical_waste_bin": {
            "type": "waste_bin",
            "waste_type": "chemical",
            "items": [],
        },
        "sink": {
            "type": "utility",
            "clean": True,
        },
    },
    inventory={
        "paracetamol_powder": {
            "amount_mg": 5000.0,
            "unit": "mg",
            "max_safe_single_dose_mg": 1000.0,
            "standard_single_dose_mg": 500.0,
        },
        "water": {
            "amount_ml": 1000.0,
            "unit": "ml",
        },
        "vacutainer_needles": {
            "count": 10,
        },
        "alcohol_swabs": {
            "count": 10,
        },
    },
    allowed_actions=[
        "wear_ppe",
        "remove_ppe",
        "tare_balance",
        "weigh",
        "dissolve",
        "pour",
        "label",
        "administer_oral",
        "advance_time",
        "draw_blood",
        "run_assay",
        "dispose_waste",
        "wash_hands",
        "submit_report",
    ],
    protocol=[
        {
            "id": "wear_ppe",
            "title": "Wear Personal Protective Equipment (PPE)",
            "hint_text": "Put on all required PPE (safety goggles, lab gloves, and lab coat).",
            "hint": "Put on all required PPE (safety goggles, lab gloves, and lab coat).",
        },
        {
            "id": "tare_balance",
            "title": "Tare Analytical Balance",
            "hint_text": "Tare the analytical digital balance before placing powder.",
            "hint": "Tare the analytical digital balance before placing powder.",
        },
        {
            "id": "weigh_dose",
            "title": "Weigh Active Drug Dose",
            "hint_text": "Weigh a safe therapeutic dose of paracetamol powder (e.g. 500 mg).",
            "hint": "Weigh a safe therapeutic dose of paracetamol powder (e.g. 500 mg).",
        },
        {
            "id": "dissolve_dose",
            "title": "Dissolve Powder in Water",
            "hint_text": "Dissolve the weighed drug powder into water inside the dosing cup.",
            "hint": "Dissolve the weighed drug powder into water inside the dosing cup.",
        },
        {
            "id": "label_cup",
            "title": "Label Oral Dosing Cup",
            "hint_text": "Label the dosing cup with patient ID and medication info.",
            "hint": "Label the dosing cup with patient ID and medication info.",
        },
        {
            "id": "administer_oral",
            "title": "Administer Oral Suspension",
            "hint_text": "Administer the prepared oral medication to the patient.",
            "hint": "Administer the prepared oral medication to the patient.",
        },
        {
            "id": "advance_time",
            "title": "Advance Simulated Clock",
            "hint_text": "Advance simulated time (e.g. 1.0 h) to allow gastrointestinal absorption.",
            "hint": "Advance simulated time (e.g. 1.0 h) to allow gastrointestinal absorption.",
        },
        {
            "id": "label_tube",
            "title": "Label Venous Blood Sampling Tube",
            "hint_text": "Label a blood collection tube before performing the venous draw.",
            "hint": "Label a blood collection tube before performing the venous draw.",
        },
        {
            "id": "draw_blood",
            "title": "Collect Venous Blood Sample",
            "hint_text": "Draw a sterile venous blood sample from the patient into the tube.",
            "hint": "Draw a sterile venous blood sample from the patient into the tube.",
        },
        {
            "id": "run_assay",
            "title": "Run Centrifuge Drug Assay",
            "hint_text": "Load the blood sample into the centrifuge/assay analyzer to measure plasma level.",
            "hint": "Load the blood sample into the centrifuge/assay analyzer to measure plasma level.",
        },
        {
            "id": "dispose_waste",
            "title": "Dispose Biomedical Waste",
            "hint_text": "Dispose of biomedical waste (used tubes, needles) into the biohazard bin.",
            "hint": "Dispose of biomedical waste (used tubes, needles) into the biohazard bin.",
        },
        {
            "id": "wash_hands",
            "title": "Wash Hands at Utility Sink",
            "hint_text": "Remove PPE and wash hands thoroughly at the sink.",
            "hint": "Remove PPE and wash hands thoroughly at the sink.",
        },
        {
            "id": "submit_report",
            "title": "Submit Clinical Ward Report",
            "hint_text": "Submit the completed pharmacokinetics clinical ward report.",
            "hint": "Submit the completed pharmacokinetics clinical ward report.",
        },
    ],
    scoring_weights={
        "safety": 40,
        "accuracy": 30,
        "technique": 20,
        "protocol": 10,
    },
)
