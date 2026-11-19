"""
Tests for Drug Library Validator & Freeze (P4-T3 / Spec Section 9.1).

ACCEPT Criteria:
- 10 to 15 drugs in library.
- Every parameter has a provenance declaration under G5.
- Every drug has a 'what this drug teaches' line.
- Route list, game target window, and game maximum dose present.
- Validator strictly rejects missing provenance.
- Zero clinical dosing advice text anywhere in the library.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import pytest

from app.pharma.pkpd.validator import (
    DrugValidationError,
    validate_drug,
    validate_drug_library,
)

DRUGS_V2_PATH = Path(__file__).resolve().parent.parent / "app" / "pharma" / "pkpd" / "drugs_v2.json"


@pytest.fixture
def library_data() -> dict:
    with open(DRUGS_V2_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_frozen_drug_library_passes_validation(library_data):
    """ACCEPT: The frozen drug library passes all validation rules cleanly."""
    errors = validate_drug_library(library_data, raise_on_error=False)
    assert errors == [], f"Frozen drug library has validation errors: {errors}"
    assert 10 <= len(library_data) <= 15
    assert len(library_data) == 12


def test_validator_rejects_missing_top_level_provenance(library_data):
    """ACCEPT: Validator rejects a drug without top-level provenance."""
    corrupted = copy.deepcopy(library_data)
    del corrupted["paracetamol"]["provenance"]

    errors = validate_drug_library(corrupted)
    assert any("missing top-level 'provenance'" in e for e in errors)


def test_validator_rejects_missing_parameter_provenance(library_data):
    """ACCEPT: Validator rejects a drug with missing parameter provenance."""
    corrupted = copy.deepcopy(library_data)
    del corrupted["ibuprofen"]["parameter_provenance"]["cl"]

    errors = validate_drug_library(corrupted)
    assert any("missing provenance for parameter 'cl'" in e for e in errors)

    # Empty string provenance is also rejected
    corrupted2 = copy.deepcopy(library_data)
    corrupted2["caffeine"]["parameter_provenance"]["ka"] = "   "
    errors2 = validate_drug_library(corrupted2)
    assert any("missing provenance for parameter 'ka'" in e for e in errors2)


def test_validator_rejects_missing_what_this_teaches(library_data):
    """ACCEPT: Validator rejects a drug missing educational statement."""
    corrupted = copy.deepcopy(library_data)
    corrupted["metformin"]["what_this_drug_teaches"] = ""

    errors = validate_drug_library(corrupted)
    assert any("missing required 'what_this_drug_teaches'" in e for e in errors)


def test_validator_rejects_invalid_routes(library_data):
    """ACCEPT: Validator rejects missing or invalid routes."""
    corrupted = copy.deepcopy(library_data)
    corrupted["amoxicillin"]["routes_allowed"] = ["inhalation_unsupported"]

    errors = validate_drug_library(corrupted)
    assert any("unknown route 'inhalation_unsupported'" in e for e in errors)


def test_validator_rejects_inverted_target_window(library_data):
    """ACCEPT: Validator rejects inverted target window (high <= low)."""
    corrupted = copy.deepcopy(library_data)
    corrupted["gentamicin"]["target_window_low"] = 15.0
    corrupted["gentamicin"]["target_window_high"] = 5.0

    errors = validate_drug_library(corrupted)
    assert any("target_window_high (5.0) must be > target_window_low (15.0)" in e for e in errors)


def test_validator_rejects_dosing_advice_text(library_data):
    """ACCEPT: Validator strictly rejects any clinical dosing advice text (Rule R6)."""
    corrupted = copy.deepcopy(library_data)
    corrupted["paracetamol"]["what_this_drug_teaches"] = "Patient should take 1000 mg for relief of symptoms."

    errors = validate_drug_library(corrupted)
    assert any("Prohibited dosing advice detected" in e for e in errors)


def test_zero_dosing_advice_in_entire_library(library_data):
    """ACCEPT: Confirm 0 occurrences of personal or clinical dosing advice across entire catalog."""
    # Serialize entire library to text and scan for common clinical advice keywords
    dumped = json.dumps(library_data).lower()

    prohibited_phrases = [
        "take 500 mg",
        "take 1000 mg",
        "patient should take",
        "prescribe",
        "recommended patient dose",
        "dosage recommendation",
        "for treating your",
        "take with food",
    ]

    for phrase in prohibited_phrases:
        assert phrase not in dumped, f"Found prohibited dosing phrase '{phrase}' in library!"
