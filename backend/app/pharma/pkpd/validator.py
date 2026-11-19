"""
backend/app/pharma/pkpd/validator.py
Drug Library Validator (P4-T3 / Spec Section 9.1).

Validates that:
1. Drug library contains 10 to 15 drugs (frozen library specification).
2. Every drug has:
   - Non-empty 'name'
   - Valid 'model_type' ('one_compartment' or 'two_compartment')
   - Non-empty 'routes_allowed' with valid routes ('oral', 'iv_bolus', 'iv_infusion')
   - Valid positive numeric parameters (cl, v1, fe, f_bioav, etc.)
   - Non-empty 'what_this_drug_teaches' pedagogical summary
   - Valid 'target_window_low' and 'target_window_high' (0 < low < high)
   - Valid positive 'max_game_dose_mg'
   - Provenance on every parameter under Rule R5 / G5
3. The validator strictly REJECTS any drug with missing or blank provenance.
4. The validator strictly REJECTS any text containing real-patient dosing advice or clinical prescribing instructions (Rule R6).
"""

from __future__ import annotations

import re
from typing import Any

REQUIRED_PARAMETERS = [
    "cl",
    "v1",
    "q",
    "v2",
    "ka",
    "f_bioav",
    "t_lag",
    "fe",
    "target_window_low",
    "target_window_high",
    "max_game_dose_mg",
]

ALLOWED_ROUTES = {"oral", "iv_bolus", "iv_infusion"}
ALLOWED_MODEL_TYPES = {"one_compartment", "two_compartment"}

# Adversarial regex detecting clinical dosing advice or patient prescribing instructions
DOSING_ADVICE_PATTERNS = [
    re.compile(r"\btake\s+\d+\s*(?:mg|g|tablets?|capsules?)\b", re.IGNORECASE),
    re.compile(r"\bprescribe\b", re.IGNORECASE),
    re.compile(r"\bpatient\s+should\s+take\b", re.IGNORECASE),
    re.compile(r"\brecommended\s+(?:patient\s+)?dose\b", re.IGNORECASE),
    re.compile(r"\bdosage\s+recommendation\b", re.IGNORECASE),
    re.compile(r"\bclinical\s+dosing\s+guideline\b", re.IGNORECASE),
    re.compile(r"\bfor\s+treating\s+your\b", re.IGNORECASE),
    re.compile(r"\btake\s+with\s+food\s+for\s+pain\b", re.IGNORECASE),
]


class DrugValidationError(ValueError):
    """Raised when drug library or individual drug fails validation rules."""
    pass


def scan_for_dosing_advice(text: str, context: str) -> list[str]:
    """Scan string for prohibited clinical dosing recommendations."""
    errors = []
    for pat in DOSING_ADVICE_PATTERNS:
        match = pat.search(text)
        if match:
            errors.append(
                f"Prohibited dosing advice detected in {context}: '{match.group(0)}'. "
                f"Educational simulation must not provide clinical dosing instructions (Rule R6)."
            )
    return errors


def validate_drug(drug_id: str, drug_data: dict[str, Any]) -> list[str]:
    """
    Validate a single drug entry against governance specifications.
    Returns list of error messages (empty if valid).
    """
    errors: list[str] = []

    # 1. Identity & Name
    name = drug_data.get("name")
    if not name or not isinstance(name, str) or not name.strip():
        errors.append(f"Drug '{drug_id}' is missing a valid non-empty 'name'.")
    else:
        errors.extend(scan_for_dosing_advice(name, f"drug '{drug_id}' name"))

    # 2. Model Type
    model_type = drug_data.get("model_type")
    if model_type not in ALLOWED_MODEL_TYPES:
        errors.append(f"Drug '{drug_id}' has invalid model_type '{model_type}'; must be one of {ALLOWED_MODEL_TYPES}.")

    # 3. Routes Allowed
    routes = drug_data.get("routes_allowed")
    if not isinstance(routes, list) or len(routes) == 0:
        errors.append(f"Drug '{drug_id}' must provide a non-empty 'routes_allowed' list.")
    else:
        for r in routes:
            if r not in ALLOWED_ROUTES:
                errors.append(f"Drug '{drug_id}' contains unknown route '{r}'. Allowed: {ALLOWED_ROUTES}.")

    # 4. Pedagogical description ('what this drug teaches')
    teaches = drug_data.get("what_this_drug_teaches")
    if not teaches or not isinstance(teaches, str) or not teaches.strip():
        errors.append(f"Drug '{drug_id}' is missing required 'what_this_drug_teaches' educational line.")
    else:
        errors.extend(scan_for_dosing_advice(teaches, f"drug '{drug_id}' what_this_drug_teaches"))

    # 5. Numerical Parameters
    for param in REQUIRED_PARAMETERS:
        val = drug_data.get(param)
        if val is None or not isinstance(val, (int, float)):
            errors.append(f"Drug '{drug_id}' is missing required numeric parameter '{param}'.")
        elif val < 0:
            errors.append(f"Drug '{drug_id}' parameter '{param}' must be non-negative, got {val}.")

    # Parameter relations
    target_low = drug_data.get("target_window_low", 0.0)
    target_high = drug_data.get("target_window_high", 0.0)
    if isinstance(target_low, (int, float)) and isinstance(target_high, (int, float)):
        if target_low <= 0:
            errors.append(f"Drug '{drug_id}' target_window_low must be > 0, got {target_low}.")
        if target_high <= target_low:
            errors.append(f"Drug '{drug_id}' target_window_high ({target_high}) must be > target_window_low ({target_low}).")

    max_dose = drug_data.get("max_game_dose_mg", 0.0)
    if isinstance(max_dose, (int, float)) and max_dose <= 0:
        errors.append(f"Drug '{drug_id}' max_game_dose_mg must be > 0, got {max_dose}.")

    # 6. Overall Provenance Field
    provenance = drug_data.get("provenance")
    if not provenance or not isinstance(provenance, str) or not provenance.strip():
        errors.append(f"Drug '{drug_id}' is missing top-level 'provenance' declaration under Rule R5/G5.")
    else:
        errors.extend(scan_for_dosing_advice(provenance, f"drug '{drug_id}' provenance"))

    # 7. Parameter-Level Provenance Fields
    param_prov = drug_data.get("parameter_provenance")
    if not isinstance(param_prov, dict):
        errors.append(f"Drug '{drug_id}' is missing required 'parameter_provenance' dictionary.")
    else:
        for param in REQUIRED_PARAMETERS:
            p_prov = param_prov.get(param)
            if not p_prov or not isinstance(p_prov, str) or not p_prov.strip():
                errors.append(f"Drug '{drug_id}' is missing provenance for parameter '{param}'.")
            else:
                errors.extend(scan_for_dosing_advice(p_prov, f"drug '{drug_id}' parameter_provenance['{param}']"))

    return errors


def validate_drug_library(library_data: dict[str, Any], raise_on_error: bool = False) -> list[str]:
    """
    Validate complete drug library catalog.
    Enforces:
    - 10 to 15 drugs in library
    - All individual drug validation constraints
    - No clinical dosing advice anywhere in the library
    """
    all_errors: list[str] = []

    count = len(library_data)
    if not (10 <= count <= 15):
        all_errors.append(f"Drug library must contain 10 to 15 drugs (spec P4-T3), got {count}.")

    for drug_id, drug_cfg in library_data.items():
        if not isinstance(drug_cfg, dict):
            all_errors.append(f"Drug entry '{drug_id}' must be a dictionary, got {type(drug_cfg)}.")
            continue
        all_errors.extend(validate_drug(drug_id, drug_cfg))

    if raise_on_error and all_errors:
        raise DrugValidationError(f"Drug library validation failed with {len(all_errors)} errors:\n- " + "\n- ".join(all_errors))

    return all_errors
