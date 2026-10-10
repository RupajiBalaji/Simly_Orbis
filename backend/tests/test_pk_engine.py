"""
Pytest tests for the pharmacokinetics engine (app/sim/pk_engine.py).

Run with:
    pytest tests/test_pk_engine.py -v
"""

from __future__ import annotations

import math

import pytest

from app.sim.drugs import get_drug
from app.sim.models import Drug, Patient
from app.sim.pk_engine import _bateman_single, simulate

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

PARACETAMOL = get_drug("paracetamol")
CAFFEINE = get_drug("caffeine")

STANDARD_PATIENT = Patient(weight_kg=70.0, clearance_multiplier=1.0)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _ke(drug: Drug, patient: Patient) -> float:
    return math.log(2) / drug.half_life * patient.clearance_multiplier


# ---------------------------------------------------------------------------
# 1. Concentration is 0 at t = 0
# ---------------------------------------------------------------------------

def test_concentration_zero_at_t0():
    result = simulate(
        drug=PARACETAMOL,
        patient=STANDARD_PATIENT,
        dose_mg=500,
        n_doses=1,
        interval_h=6,
    )
    assert result.concentrations[0] == pytest.approx(0.0, abs=1e-12), (
        "Concentration must be 0 at t=0 (no drug absorbed yet)"
    )


# ---------------------------------------------------------------------------
# 2. Zero dose → zero curve
# ---------------------------------------------------------------------------

def test_zero_dose_gives_zero_curve():
    result = simulate(
        drug=PARACETAMOL,
        patient=STANDARD_PATIENT,
        dose_mg=0.0,
        n_doses=3,
        interval_h=6,
    )
    assert all(c == pytest.approx(0.0, abs=1e-12) for c in result.concentrations), (
        "Zero dose must produce a flat zero concentration curve"
    )


# ---------------------------------------------------------------------------
# 3. Concentration decays after the peak
# ---------------------------------------------------------------------------

def test_concentration_decays_after_peak():
    result = simulate(
        drug=CAFFEINE,
        patient=STANDARD_PATIENT,
        dose_mg=100,
        n_doses=1,
        interval_h=6,
    )
    peak_idx = result.concentrations.index(result.peak_concentration)

    # All points after peak+2 steps should be <= the peak
    for i in range(peak_idx + 2, len(result.concentrations)):
        assert result.concentrations[i] <= result.concentrations[peak_idx], (
            f"Concentration at step {i} ({result.concentrations[i]:.4f}) "
            f"exceeds peak ({result.peak_concentration:.4f})"
        )


# ---------------------------------------------------------------------------
# 4. Superposition: two-dose curve == sum of two single-dose curves
# ---------------------------------------------------------------------------

def test_superposition_two_doses():
    drug = PARACETAMOL
    patient = STANDARD_PATIENT
    interval = 6.0
    dose = 500.0

    two_dose = simulate(drug, patient, dose_mg=dose, n_doses=2, interval_h=interval)

    dose1 = simulate(drug, patient, dose_mg=dose, n_doses=1, interval_h=interval)
    dose2 = simulate(drug, patient, dose_mg=dose, n_doses=1, interval_h=interval)

    # Manually shift dose2 by 'interval' hours
    Vd = drug.vd_per_kg * patient.weight_kg
    ke = _ke(drug, patient)
    ka = drug.ka
    F = drug.bioavailability

    for i, t in enumerate(two_dose.times):
        single1 = _bateman_single(t_elapsed=t,            F=F, D=dose, ka=ka, ke=ke, Vd=Vd)
        single2 = _bateman_single(t_elapsed=t - interval, F=F, D=dose, ka=ka, ke=ke, Vd=Vd)
        expected = single1 + single2
        assert two_dose.concentrations[i] == pytest.approx(expected, rel=1e-9), (
            f"Superposition failed at t={t:.1f}h"
        )


# ---------------------------------------------------------------------------
# 5. ka == ke edge case does not crash and returns sensible values
# ---------------------------------------------------------------------------

def test_ka_equals_ke_no_crash():
    half_life = 2.5
    ke_val = math.log(2) / half_life  # ~0.277 h⁻¹

    drug = Drug(
        name="TestDrug",
        ka=ke_val,          # <-- exactly equal to ke
        half_life=half_life,
        vd_per_kg=0.5,
        bioavailability=1.0,
        green_low=1.0,
        green_high=5.0,
        red_threshold=10.0,
        standard_dose_mg=100.0,
    )
    patient = Patient(weight_kg=70.0)

    result = simulate(drug, patient, dose_mg=100, n_doses=1, interval_h=6)

    # Must not crash, t=0 must be 0, peak must be positive
    assert result.concentrations[0] == pytest.approx(0.0, abs=1e-12)
    assert result.peak_concentration > 0.0
    assert all(math.isfinite(c) for c in result.concentrations), (
        "All concentrations must be finite when ka == ke"
    )


# ---------------------------------------------------------------------------
# 6. Peak concentration matches manual Bateman calculation
# ---------------------------------------------------------------------------

def test_peak_value_matches_manual():
    """
    For a single dose, t_peak = ln(ka/ke) / (ka - ke).
    Check that simulate()'s reported peak is close to the analytical value.
    """
    drug = PARACETAMOL
    patient = STANDARD_PATIENT
    dose = 500.0

    ke = _ke(drug, patient)
    ka = drug.ka
    Vd = drug.vd_per_kg * patient.weight_kg
    F = drug.bioavailability

    t_peak_analytical = math.log(ka / ke) / (ka - ke)
    c_peak_analytical = _bateman_single(
        t_elapsed=t_peak_analytical, F=F, D=dose, ka=ka, ke=ke, Vd=Vd
    )

    result = simulate(drug, patient, dose_mg=dose, n_doses=1, interval_h=6)

    # Numerical peak will be within one time-step of the analytical peak.
    assert result.peak_concentration == pytest.approx(c_peak_analytical, rel=0.01), (
        "Simulated peak should be within 1% of the analytical Bateman peak"
    )


# ---------------------------------------------------------------------------
# 7. Percentage bands sum to 100
# ---------------------------------------------------------------------------

def test_percentage_bands_sum_to_100():
    result = simulate(
        drug=PARACETAMOL,
        patient=STANDARD_PATIENT,
        dose_mg=500,
        n_doses=4,
        interval_h=6,
    )
    total = result.pct_green + result.pct_below_green + result.pct_red
    assert total == pytest.approx(100.0, abs=1e-9), (
        f"pct_green + pct_below_green + pct_red = {total} (expected 100)"
    )


# ---------------------------------------------------------------------------
# 8. Drug catalogue loads correctly
# ---------------------------------------------------------------------------

def test_drug_catalogue_has_all_drugs():
    for name in ("paracetamol", "ibuprofen", "caffeine"):
        drug = get_drug(name)
        assert drug.ka > 0
        assert drug.half_life > 0
        assert drug.vd_per_kg > 0
        assert 0 < drug.bioavailability <= 1.0
        assert drug.green_low < drug.green_high < drug.red_threshold


def test_get_drug_unknown_raises():
    with pytest.raises(KeyError, match="Unknown drug"):
        get_drug("aspirin_xyz_unknown")
