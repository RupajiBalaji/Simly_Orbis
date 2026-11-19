"""
backend/tests/test_chem_tolerances_guard.py
Validation tolerances guard and benchmark verification for chemistry engines (P3-T6).
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
import yaml

from app.chem.buffer import compute_buffer_state, max_buffer_capacity
from app.chem.kinetics import arrhenius_two_temperature, celsius_to_kelvin, half_life_order_1

FROZEN_CHEM_TOLERANCES_SHA256 = "2288d01d83e2a5fc986f1a5817f83c2c32eb7afb56605241ea8552da07d3782a"


def test_chem_tolerances_configuration_frozen():
    """Fails if validation/chem_tolerances.yaml changes."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    tol_file = base_dir / "validation" / "chem_tolerances.yaml"
    sha_file = base_dir / "validation" / "chem_tolerances.sha256"

    assert tol_file.exists(), "validation/chem_tolerances.yaml missing"
    assert sha_file.exists(), "validation/chem_tolerances.sha256 missing"

    content = tol_file.read_bytes()
    computed_sha = hashlib.sha256(content).hexdigest()
    recorded_sha = sha_file.read_text().strip()

    assert computed_sha == FROZEN_CHEM_TOLERANCES_SHA256, (
        f"validation/chem_tolerances.yaml modified! Expected {FROZEN_CHEM_TOLERANCES_SHA256}, got {computed_sha}"
    )
    assert recorded_sha == FROZEN_CHEM_TOLERANCES_SHA256, (
        f"validation/chem_tolerances.sha256 mismatch! Expected {FROZEN_CHEM_TOLERANCES_SHA256}, got {recorded_sha}"
    )


def test_chem_tolerances_governance_rules():
    """Verify strict governance on all chemistry tolerance rows:
    - verified_by strictly 'unverified'
    - retrieved_on strictly ''
    - notes require human verification
    - citations non-empty
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    tol_file = base_dir / "validation" / "chem_tolerances.yaml"

    with open(tol_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    quantities = data.get("quantities", {})
    assert len(quantities) == 6, f"Expected 6 chemistry quantities, found {len(quantities)}"

    for qid, qdata in quantities.items():
        assert qdata.get("verified_by") == "unverified", (
            f"Governance violation in {qid}: verified_by must be 'unverified'"
        )
        assert qdata.get("retrieved_on") == "", (
            f"Governance violation in {qid}: retrieved_on must be strictly empty ''"
        )
        citation = qdata.get("source_citation", "")
        assert len(citation) > 0, f"Missing source citation in {qid}"
        notes = qdata.get("notes", "")
        assert "human verification needed" in notes.lower(), (
            f"Notes in {qid} must mention human verification needed"
        )


def test_chem_tolerances_numerical_benchmarks():
    """Verify that chem.kinetics and chem.buffer engines agree with declared validation benchmarks."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    tol_file = base_dir / "validation" / "chem_tolerances.yaml"

    with open(tol_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    quantities = data["quantities"]

    # 1. Rate constant at 25 °C (evaluated at T1 = T2 = 298.15 K)
    k_ref = arrhenius_two_temperature(k1=0.05, t1_kelvin=298.15, t2_kelvin=298.15, ea_joules=45000.0)
    ref_k = quantities["kinetics_rate_constant_at_25c"]["reference_value"]
    pct_tol_k = quantities["kinetics_rate_constant_at_25c"]["percent_tolerance"]
    assert abs(k_ref - ref_k) / ref_k * 100.0 <= pct_tol_k

    # 2. Half-life formula (t1/2 = ln(2) / k)
    t_half = half_life_order_1(k=0.05)
    ref_thalf = quantities["kinetics_half_life_formula"]["reference_value"]
    pct_tol_thalf = quantities["kinetics_half_life_formula"]["percent_tolerance"]
    assert abs(t_half - ref_thalf) / ref_thalf * 100.0 <= pct_tol_thalf

    # 3. Buffer Van Slyke beta max
    beta_max = max_buffer_capacity(c_total=0.2)
    ref_beta = quantities["buffer_van_slyke_beta_max"]["reference_value"]
    pct_tol_beta = quantities["buffer_van_slyke_beta_max"]["percent_tolerance"]
    assert abs(beta_max - ref_beta) / ref_beta * 100.0 <= pct_tol_beta

    # 4. Equimolar buffer pH
    state = compute_buffer_state(total_acid_conc=0.1, total_salt_conc=0.1, ka=10.0**(-4.76))
    ref_ph = quantities["buffer_equimolar_ph"]["reference_value"]
    pct_tol_ph = quantities["buffer_equimolar_ph"]["percent_tolerance"]
    assert abs(state.ph - ref_ph) / ref_ph * 100.0 <= pct_tol_ph
