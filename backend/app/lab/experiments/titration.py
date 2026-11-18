"""
Acid-Base Titration Bench Experiment Definition ("titration_bench").
"""

from __future__ import annotations

from app.lab.experiments.base import ExperimentDefinition


TITRATION_BENCH_EXPERIMENT = ExperimentDefinition(
    id="titration_bench",
    title="Acid-Base Titration Bench",
    district="chemistry",
    description=(
        "Perform precision volumetric neutralization titration using a graduated burette, "
        "conical flask, volumetric transfer pipette, and chemical indicator endpoint detection."
    ),
    learning_goals=[
        "Maintain strict chemical lab PPE compliance (goggles, gloves, lab coat).",
        "Rinse and condition the burette with titrant before volumetric filling.",
        "Accurately pipette standardized acid analyte into the reaction vessel.",
        "Select and add the appropriate chemical indicator for stoichiometric detection.",
        "Perform dropwise titration with continuous swirling to avoid volumetric overshoot.",
        "Distinguish between indicator color transitions and exact potentiometric pH readings.",
        "Dispose of neutralized and concentrated chemicals into designated chemical waste.",
    ],
    required_ppe=["goggles", "gloves", "coat"],
    apparatus={
        "burette": {
            "type": "burette",
            "rinsed": False,
            "filled": False,
            "volume_ml": 0.0,
            "max_volume_ml": 50.0,
            "titrant": "naoh_0.1M",
            "titrant_conc_m": 0.1,
        },
        "conical_flask": {
            "type": "flask",
            "analyte": None,
            "analyte_conc_m": 0.1,
            "volume_ml": 0.0,
            "indicator": None,
            "ph": 7.0,
            "color_hex": "#f8fafc",
            "titrant_added_ml": 0.0,
            "clean": True,
        },
        "pipette": {
            "type": "pipette",
            "capacity_ml": 25.0,
            "filled": False,
            "substance": None,
            "clean": True,
        },
        "indicator_bottles": {
            "type": "indicator_shelf",
            "available": ["phenolphthalein", "methyl_orange", "bromothymol_blue"],
        },
        "ph_meter": {
            "type": "ph_meter",
            "calibrated": True,
            "last_reading": None,
        },
        "acid_bottle_hcl": {
            "type": "reagent_bottle",
            "substance": "hcl_0.1M",
            "concentration_m": 0.1,
            "volume_ml": 250.0,
        },
        "acid_bottle_acetic": {
            "type": "reagent_bottle",
            "substance": "acetic_0.1M",
            "concentration_m": 0.1,
            "pka": 4.76,
            "volume_ml": 250.0,
        },
        "naoh_bottle": {
            "type": "reagent_bottle",
            "substance": "naoh_0.1M",
            "concentration_m": 0.1,
            "volume_ml": 500.0,
        },
        "wash_bottle": {
            "type": "utility",
            "volume_ml": 500.0,
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
        "hcl_0.1M": {
            "volume_ml": 250.0,
            "concentration_m": 0.1,
        },
        "acetic_0.1M": {
            "volume_ml": 250.0,
            "concentration_m": 0.1,
            "pka": 4.76,
        },
        "naoh_0.1M": {
            "volume_ml": 500.0,
            "concentration_m": 0.1,
        },
        "phenolphthalein": {
            "drops": 50,
        },
        "methyl_orange": {
            "drops": 50,
        },
        "bromothymol_blue": {
            "drops": 50,
        },
        "deionized_water": {
            "volume_ml": 1000.0,
        },
    },
    allowed_actions=[
        "wear_ppe",
        "remove_ppe",
        "rinse_burette",
        "fill_burette",
        "pipette_analyte",
        "add_indicator",
        "titrate",
        "swirl",
        "read_ph_meter",
        "record_endpoint",
        "pour",
        "dispose_waste",
        "wash_hands",
        "submit_report",
    ],
    protocol=[
        {
            "id": "wear_ppe",
            "title": "Wear Personal Protective Equipment (PPE)",
            "hint_text": "Put on all required safety gear: goggles, gloves, and lab coat.",
            "hint": "Put on all required safety gear: goggles, gloves, and lab coat.",
        },
        {
            "id": "rinse_burette",
            "title": "Rinse & Condition Burette",
            "hint_text": "Condition the burette by rinsing with a small portion (5 mL) of NaOH titrant.",
            "hint": "Condition the burette by rinsing with a small portion (5 mL) of NaOH titrant.",
        },
        {
            "id": "fill_burette",
            "title": "Fill Burette with Titrant",
            "hint_text": "Fill the burette with 0.1 M NaOH up to 50 mL.",
            "hint": "Fill the burette with 0.1 M NaOH up to 50 mL.",
        },
        {
            "id": "pipette_analyte",
            "title": "Pipette Acid Analyte into Flask",
            "hint_text": "Pipette 25 mL of acid analyte (HCl 0.1M or Acetic acid 0.1M) into the conical flask.",
            "hint": "Pipette 25 mL of acid analyte (HCl 0.1M or Acetic acid 0.1M) into the conical flask.",
        },
        {
            "id": "add_indicator",
            "title": "Add Chemical Indicator Drops",
            "hint_text": "Add 2-3 drops of chemical indicator (e.g. phenolphthalein) to the flask.",
            "hint": "Add 2-3 drops of chemical indicator (e.g. phenolphthalein) to the flask.",
        },
        {
            "id": "titrate",
            "title": "Titrate Towards Equivalence Point",
            "hint_text": "Carefully dispense NaOH titrant into the flask.",
            "hint": "Carefully dispense NaOH titrant into the flask.",
        },
        {
            "id": "swirl",
            "title": "Swirl Conical Flask",
            "hint_text": "Swirl the conical flask to ensure complete chemical mixing.",
            "hint": "Swirl the conical flask to ensure complete chemical mixing.",
        },
        {
            "id": "record_endpoint",
            "title": "Record Equivalence Endpoint",
            "hint_text": "Observe the persistent color change and record the final endpoint volume.",
            "hint": "Observe the persistent color change and record the final endpoint volume.",
        },
        {
            "id": "dispose_waste",
            "title": "Dispose Chemical Waste",
            "hint_text": "Dispose of chemical contents into the designated chemical waste bin.",
            "hint": "Dispose of chemical contents into the designated chemical waste bin.",
        },
        {
            "id": "wash_hands",
            "title": "Wash Hands at Sink",
            "hint_text": "Remove PPE and wash hands thoroughly at the sink.",
            "hint": "Remove PPE and wash hands thoroughly at the sink.",
        },
        {
            "id": "submit_report",
            "title": "Submit Titration Lab Report",
            "hint_text": "Submit the completed acid-base titration laboratory report.",
            "hint": "Submit the completed acid-base titration laboratory report.",
        },
    ],
    scoring_weights={
        "safety": 40,
        "accuracy": 30,
        "technique": 20,
        "protocol": 10,
    },
    rules=[
        {"rule_id": "R1", "title": "Eye Protection (Goggles)", "explanation": "Protective safety goggles must be equipped before handling active drugs or chemicals."},
        {"rule_id": "R2", "title": "Protective Gloves", "explanation": "Chemical-resistant gloves must be worn before manipulating hazardous reagents or specimens."},
        {"rule_id": "R3", "title": "Protective Lab Coat", "explanation": "Buttoned laboratory coat required before beginning experiments in active lab zones."},
        {"rule_id": "R4", "title": "Balance Tare Required", "explanation": "Analytical digital balance must be tared to zero with container in place prior to weighing samples."},
        {"rule_id": "R5", "title": "Specimen & Solution Labelling", "explanation": "All beakers, vials, and solutions must be explicitly labeled with contents and concentration."},
        {"rule_id": "R6", "title": "Safe Acid Dilution Sequence", "explanation": "Always add acid to water slowly; never pour water directly into concentrated reagents."},
        {"rule_id": "R7", "title": "Burette Conditioning & Capacity", "explanation": "Rinse burette with titrant and never exceed graduated volumetric capacity."},
        {"rule_id": "R8", "title": "Maximum Safe Single Dose", "explanation": "Administered medication dose must not exceed safe therapeutic threshold."},
        {"rule_id": "R9", "title": "Segregated Waste Disposal", "explanation": "Chemical, biological, and sharps waste must be disposed into designated segregated waste receptacles."},
        {"rule_id": "R10", "title": "Aseptic Handwash & Clean Finish", "explanation": "Decontaminate hands and remove PPE in proper aseptic sequence before exiting laboratory."},
    ],
)
