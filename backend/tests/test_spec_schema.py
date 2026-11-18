"""
Tests for Experiment Specification Schema, Loader, Validator, and CLI.
Validates all Section 10 rejection rules:
1. Unknown fields
2. Duplicate rule IDs
3. Actions with no handler
4. Directives not in schema
5. Parameter bounds outside engine limits
6. Constants without provenance
7. Hard-coded strings / missing i18n keys
8. Pharma specs outside adult ranges
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
import pytest

from app.specs.loader import load_and_validate_spec, load_raw_spec
from app.specs.validator import validate_spec_data

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

VALID_MINIMAL_SPEC = {
    "id": "titration_sample",
    "version": "1.0.0",
    "district": "chemistry",
    "title": "Acid-Base Titration",
    "learning_goals": ["Identify equivalence point"],
    "difficulty": "beginner",
    "est_minutes": 15,
    "engine": {
        "id": "chem.titration",
        "minimum_version": "0.1.0",
        "parameter_bounds": {
            "analyte_vol_ml": {"min": 10.0, "max": 50.0, "unit": "mL", "default": 25.0},
            "titrant_vol_ml": {"min": 0.0, "max": 50.0, "unit": "mL", "default": 25.0},
            "analyte_molarity": {"min": 0.05, "max": 0.2, "unit": "M", "default": 0.1},
            "titrant_molarity": {"min": 0.05, "max": 0.2, "unit": "M", "default": 0.1},
            "temperature_c": {"min": 20.0, "max": 25.0, "unit": "C", "default": 25.0},
        },
    },
    "equipment": ["burette", "flask", "pipette", "indicator_bottle"],
    "steps": [
        {
            "id": "step_1",
            "title": "Rinse burette",
            "allowed_actions": ["wear_ppe", "rinse_burette"],
            "preconditions": [],
            "effects": ["burette_rinsed"],
        },
        {
            "id": "step_2",
            "title": "Titrate to endpoint",
            "allowed_actions": ["titrate", "record_endpoint"],
            "preconditions": ["burette_rinsed"],
            "effects": ["titration_complete"],
        },
    ],
    "rules": [
        {
            "id": "S1",
            "text": "Wear eye protection before handling chemical solutions",
            "severity": "penalty",
            "condition": "ppe_worn",
        },
        {
            "id": "S2",
            "text": "Rinse burette with titrant before filling",
            "severity": "penalty",
            "condition": "burette_rinsed",
        },
    ],
    "scoring": {
        "weights": {"accuracy": 40, "safety": 30, "technique": 20, "protocol": 10},
        "grade_thresholds": {"A": 90, "B": 80, "C": 70, "D": 60},
    },
    "visual_directive_mapping": {
        "endpoint": {"type": "liquid", "hex": "#FFC0CB", "target": "flask"},
        "splash": {"type": "effect", "name": "splash", "target": "sink"},
    },
    "mentor": {
        "hints_per_step": {"step_1": ["Check PPE first", "Rinse with titrant, not water"]},
        "common_mistakes": [
            {"id": "m1", "trigger": "titrate_without_indicator", "remedy": "Add 2-3 drops of indicator first"}
        ],
    },
    "ask_orbis": {
        "allowed_actions": ["wear_ppe", "rinse_burette", "titrate", "record_endpoint"],
        "synonyms": {"titrate": ["add titrant", "dispense base", "turn stopcock"]},
    },
    "model_card": "docs/model_cards/chem.titration.md",
    "provenance": {
        "author": "Antigravity Chemistry Team",
        "model_card": "docs/model_cards/chem.titration.md",
        "constants": {
            "water_pkw": {
                "value": 14.0,
                "unit": "dimensionless",
                "source": "CRC Handbook of Chemistry and Physics, 97th ed.",
                "citation": "Table 5-11, Ionization Constant of Normal Water",
                "verified_by": "unverified",
                "retrieved_on": "",
            }
        },
    },
    "i18n_keys": {
        "title": "experiments.titration.title",
        "steps.step_1.title": "experiments.titration.steps.1.title",
        "steps.step_2.title": "experiments.titration.steps.2.title",
    },
}


def test_valid_spec_passes():
    """Verify that a compliant experiment spec passes validation without errors."""
    report = validate_spec_data(VALID_MINIMAL_SPEC)
    assert report.valid is True
    assert len(report.errors) == 0
    assert report.spec is not None
    assert report.spec.id == "titration_sample"


def test_rejection_rule_1_unknown_fields():
    """Rule 1: Validator must reject unknown fields and name the exact field path."""
    bad_spec = copy.deepcopy(VALID_MINIMAL_SPEC)
    bad_spec["unauthorized_top_level_field"] = "malicious_payload"

    report = validate_spec_data(bad_spec)
    assert report.valid is False
    assert any("unauthorized_top_level_field" in err.path for err in report.errors)


def test_rejection_rule_2_duplicate_rule_ids():
    """Rule 2: Validator must reject duplicate rule IDs and name the exact field path."""
    bad_spec = copy.deepcopy(VALID_MINIMAL_SPEC)
    bad_spec["rules"].append(
        {
            "id": "S1",  # duplicate of first rule
            "text": "Duplicate rule statement",
            "severity": "penalty",
        }
    )

    report = validate_spec_data(bad_spec)
    assert report.valid is False
    dup_errors = [e for e in report.errors if "rules[2].id" in e.path]
    assert len(dup_errors) > 0
    assert "Duplicate rule id 'S1'" in dup_errors[0].message


def test_rejection_rule_3_actions_with_no_handler():
    """Rule 3: Validator must reject actions with no handler in ActionType."""
    bad_spec = copy.deepcopy(VALID_MINIMAL_SPEC)
    bad_spec["steps"][0]["allowed_actions"].append("nonexistent_experimental_action")

    report = validate_spec_data(bad_spec)
    assert report.valid is False
    act_errors = [e for e in report.errors if "steps[0].allowed_actions[2]" in e.path]
    assert len(act_errors) > 0
    assert "no registered engine handler" in act_errors[0].message


def test_rejection_rule_4_directives_not_in_schema():
    """Rule 4: Validator must reject directives not in the VisualDirective schema."""
    bad_spec = copy.deepcopy(VALID_MINIMAL_SPEC)
    bad_spec["visual_directive_mapping"]["bad_directive"] = {
        "type": "invalid_directive_type",
        "target": "beaker",
    }

    report = validate_spec_data(bad_spec)
    assert report.valid is False
    dir_errors = [e for e in report.errors if "visual_directive_mapping.bad_directive.type" in e.path]
    assert len(dir_errors) > 0
    assert "Directive type 'invalid_directive_type' not in schema" in dir_errors[0].message


def test_rejection_rule_5_parameter_bounds_outside_engine_limits():
    """Rule 5: Validator must reject parameter bounds exceeding engine limits or min > max."""
    bad_spec = copy.deepcopy(VALID_MINIMAL_SPEC)
    # analyte_vol_ml engine max is 1000.0 mL, set to 5000.0 mL
    bad_spec["engine"]["parameter_bounds"]["analyte_vol_ml"]["max"] = 5000.0

    report = validate_spec_data(bad_spec)
    assert report.valid is False
    bound_errors = [e for e in report.errors if "engine.parameter_bounds.analyte_vol_ml.max" in e.path]
    assert len(bound_errors) > 0
    assert "exceeds engine limit" in bound_errors[0].message

    # Test min > max
    bad_spec2 = copy.deepcopy(VALID_MINIMAL_SPEC)
    bad_spec2["engine"]["parameter_bounds"]["analyte_vol_ml"]["min"] = 100.0
    bad_spec2["engine"]["parameter_bounds"]["analyte_vol_ml"]["max"] = 50.0
    report2 = validate_spec_data(bad_spec2)
    assert report2.valid is False
    assert any("cannot exceed max" in e.message for e in report2.errors)


def test_rejection_rule_6_constants_without_provenance():
    """Rule 6: Validator must reject constants without provenance source/citation."""
    bad_spec = copy.deepcopy(VALID_MINIMAL_SPEC)
    bad_spec["provenance"]["constants"]["unverified_constant"] = {
        "value": 42.0,
        "unit": "g/mol",
        "source": "",  # Empty provenance
        "citation": None,
    }

    report = validate_spec_data(bad_spec)
    assert report.valid is False
    const_errors = [e for e in report.errors if "provenance.constants.unverified_constant.source" in e.path]
    assert len(const_errors) > 0
    assert "has no provenance source or citation" in const_errors[0].message


def test_rejection_rule_7_hard_coded_strings_missing_i18n():
    """Rule 7: Validator must reject hard-coded strings not mapped in i18n_keys."""
    bad_spec = copy.deepcopy(VALID_MINIMAL_SPEC)
    # Remove title mapping from i18n_keys
    del bad_spec["i18n_keys"]["title"]

    report = validate_spec_data(bad_spec)
    assert report.valid is False
    i18n_errors = [e for e in report.errors if "i18n_keys.title" in e.path]
    assert len(i18n_errors) > 0
    assert "missing i18n key for 'title'" in i18n_errors[0].message


def test_rejection_rule_8_pharma_specs_outside_adult_ranges():
    """Rule 8: Validator must reject pharma specs with paediatric or out-of-range adult covariates."""
    pharma_spec = copy.deepcopy(VALID_MINIMAL_SPEC)
    pharma_spec["id"] = "pk_sample"
    pharma_spec["district"] = "pharma"
    pharma_spec["engine"] = {
        "id": "pharma.pkpd",
        "minimum_version": "0.1.0",
        "parameter_bounds": {
            "age": {"min": 8.0, "max": 14.0, "unit": "years"},  # Paediatric!
            "weight_kg": {"min": 25.0, "max": 45.0, "unit": "kg"},  # Under 40 kg!
            "crcl_ml_min": {"min": 80.0, "max": 120.0, "unit": "mL/min"},
            "dose_mg": {"min": 100.0, "max": 500.0, "unit": "mg"},
        },
    }
    pharma_spec["provenance"]["model_card"] = "docs/model_cards/pharma.pkpd.md"
    pharma_spec["model_card"] = "docs/model_cards/pharma.pkpd.md"

    report = validate_spec_data(pharma_spec)
    assert report.valid is False
    age_errors = [e for e in report.errors if "engine.parameter_bounds.age" in e.path]
    assert len(age_errors) > 0
    assert any("paediatric not supported per R6" in e.message for e in age_errors)

    wt_errors = [e for e in report.errors if "engine.parameter_bounds.weight_kg" in e.path]
    assert len(wt_errors) > 0
    assert any("outside adult range" in e.message for e in wt_errors)


def test_cli_execution_valid_and_invalid(tmp_path: Path):
    """Test validate_specs.py CLI execution on valid and invalid files."""
    valid_file = tmp_path / "valid_spec.json"
    valid_file.write_text(json.dumps(VALID_MINIMAL_SPEC, indent=2), encoding="utf-8")

    bad_spec = copy.deepcopy(VALID_MINIMAL_SPEC)
    bad_spec["unknown_field"] = 123
    invalid_file = tmp_path / "invalid_spec.json"
    invalid_file.write_text(json.dumps(bad_spec, indent=2), encoding="utf-8")

    cli_script = REPO_ROOT / "scripts" / "validate_specs.py"

    # 1. Run on valid file -> expect exit code 0
    res_valid = subprocess.run(
        [sys.executable, str(cli_script), str(valid_file)],
        capture_output=True,
        text=True,
    )
    assert res_valid.returncode == 0
    assert "[PASS]" in res_valid.stdout

    # 2. Run on invalid file -> expect exit code 1
    res_invalid = subprocess.run(
        [sys.executable, str(cli_script), str(invalid_file)],
        capture_output=True,
        text=True,
    )
    assert res_invalid.returncode == 1
    assert "[FAIL]" in res_invalid.stdout
    assert "unknown_field" in res_invalid.stdout


def test_worked_example_fixture_validates_and_runs():
    """Verify that the worked example from docs/experiment_spec.md validates and can run."""
    from app.specs.loader import load_and_validate_spec
    from app.specs.adapter import spec_to_experiment_definition
    from app.lab.engine import create_session, apply_action
    from app.lab.models import ActionRequest, ActionType
    import app.lab.experiments as lab_exp

    fixture_path = REPO_ROOT / "specs" / "fixtures" / "worked_example_neutralization.json"
    assert fixture_path.is_file(), f"Fixture {fixture_path} missing"

    spec, report = load_and_validate_spec(fixture_path)
    assert report.valid is True, f"Worked example failed validation: {report.errors}"
    assert spec is not None
    assert spec.id == "worked_example_neutralization"

    # Convert to ExperimentDefinition
    from app.lab.experiments.titration import TITRATION_BENCH_EXPERIMENT
    exp_def = spec_to_experiment_definition(
        spec,
        base_apparatus=TITRATION_BENCH_EXPERIMENT.apparatus,
        base_inventory=TITRATION_BENCH_EXPERIMENT.inventory,
        required_ppe=TITRATION_BENCH_EXPERIMENT.required_ppe,
    )
    assert exp_def.id == "worked_example_neutralization"
    assert len(exp_def.protocol) == 11
    assert len(exp_def.rules) == 10

    # Register temporarily and execute actions on a session
    lab_exp._EXPERIMENTS[exp_def.id] = exp_def
    try:
        session = create_session(exp_def.id, "TeacherAlex")
        assert session.experiment_id == exp_def.id

        # Execute wear_ppe
        res_ppe = apply_action(session, ActionRequest(action=ActionType.wear_ppe, target="avatar", params={"item": "all"}))
        assert res_ppe.accepted is True
        assert "goggles" in session.ppe

        # Execute rinse_burette
        res_rinse = apply_action(session, ActionRequest(action=ActionType.rinse_burette, target="burette", params={"solvent": "naoh"}))
        assert res_rinse.accepted is True
    finally:
        lab_exp._EXPERIMENTS.pop(exp_def.id, None)

