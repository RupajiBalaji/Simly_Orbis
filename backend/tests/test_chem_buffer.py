"""
backend/tests/test_chem_buffer.py
Unit tests for Aqueous Buffer Equilibrium Engine (chem.buffer).

Standard: Section 18 (P3-T2) of Simly Orbis MVP Build Specification.
Criteria:
- At least 40 tests covering exact charge balance, buffer capacity, acid/base additions.
- Limiting cases (dilute buffer, zero buffer, extreme pH).
- Van Slyke capacity formulas and max capacity at pH = pKa.
- Agreement with existing equilibrium solver in chem.titration.
"""

import math
import pytest

from app.chem.buffer import (
    KW_DEFAULT,
    LN10,
    BufferSystemState,
    compute_buffer_capacity,
    compute_buffer_state,
    henderson_hasselbalch_ph,
    max_buffer_capacity,
    simulate_buffer_stress,
    solve_exact_buffer_h,
)
from app.modules.chem_titration import compute_ph_weak


# ===========================================================================
# 1. Exact Charge-Balance Buffer pH & Species Distribution
# ===========================================================================

def test_equimolar_buffer_ph_near_pka():
    # Acetic acid (pKa = 4.76, Ka = 1.7378e-5), [HA] = 0.1 M, [A-] = 0.1 M
    ka = 10.0 ** (-4.76)
    state = compute_buffer_state(total_acid_conc=0.1, total_salt_conc=0.1, ka=ka)
    assert abs(state.ph - 4.76) < 0.01
    assert state.charge_balance_residual < 1e-10


def test_buffer_ph_ratio_10_to_1_acidic():
    # [HA] = 0.1 M, [A-] = 0.01 M -> ratio [A-]/[HA] = 0.1 => pH ~ pKa - 1 = 3.76
    ka = 10.0 ** (-4.76)
    state = compute_buffer_state(total_acid_conc=0.1, total_salt_conc=0.01, ka=ka)
    assert abs(state.ph - 3.76) < 0.03
    assert state.charge_balance_residual < 1e-10


def test_buffer_ph_ratio_1_to_10_basic():
    # [HA] = 0.01 M, [A-] = 0.1 M -> ratio [A-]/[HA] = 10.0 => pH ~ pKa + 1 = 5.76
    ka = 10.0 ** (-4.76)
    state = compute_buffer_state(total_acid_conc=0.01, total_salt_conc=0.1, ka=ka)
    assert abs(state.ph - 5.76) < 0.03
    assert state.charge_balance_residual < 1e-10


def test_buffer_ph_ratio_2_to_1():
    # [HA] = 0.1 M, [A-] = 0.05 M -> log10(0.5) = -0.3010 => pH ~ 4.76 - 0.3010 = 4.459
    ka = 10.0 ** (-4.76)
    state = compute_buffer_state(total_acid_conc=0.1, total_salt_conc=0.05, ka=ka)
    assert abs(state.ph - 4.459) < 0.02
    assert state.charge_balance_residual < 1e-10


def test_buffer_ph_ratio_1_to_2():
    # [HA] = 0.05 M, [A-] = 0.1 M -> log10(2.0) = +0.3010 => pH ~ 4.76 + 0.3010 = 5.061
    ka = 10.0 ** (-4.76)
    state = compute_buffer_state(total_acid_conc=0.05, total_salt_conc=0.1, ka=ka)
    assert abs(state.ph - 5.061) < 0.02
    assert state.charge_balance_residual < 1e-10


def test_formic_acid_buffer():
    # Formic acid pKa = 3.75, Ka = 10^-3.75 = 1.778e-4
    ka = 10.0 ** (-3.75)
    state = compute_buffer_state(total_acid_conc=0.2, total_salt_conc=0.2, ka=ka)
    assert abs(state.ph - 3.75) < 0.01
    assert state.charge_balance_residual < 1e-10


def test_cacodylate_buffer():
    # Cacodylic acid pKa = 6.27
    ka = 10.0 ** (-6.27)
    state = compute_buffer_state(total_acid_conc=0.05, total_salt_conc=0.05, ka=ka)
    assert abs(state.ph - 6.27) < 0.01
    assert state.charge_balance_residual < 1e-10


def test_tris_buffer_neutral_alkaline():
    # Tris conjugate acid pKa = 8.06
    ka = 10.0 ** (-8.06)
    state = compute_buffer_state(total_acid_conc=0.1, total_salt_conc=0.1, ka=ka)
    assert abs(state.ph - 8.06) < 0.01
    assert state.charge_balance_residual < 1e-10


def test_ammonium_buffer():
    # NH4+ pKa = 9.25
    ka = 10.0 ** (-9.25)
    state = compute_buffer_state(total_acid_conc=0.1, total_salt_conc=0.1, ka=ka)
    assert abs(state.ph - 9.25) < 0.01
    assert state.charge_balance_residual < 1e-10


def test_buffer_species_mass_balance():
    # [HA] + [A-] must equal C_total
    ka = 10.0 ** (-4.76)
    c_ha = 0.08
    c_naa = 0.12
    state = compute_buffer_state(total_acid_conc=c_ha, total_salt_conc=c_naa, ka=ka)
    c_tot = c_ha + c_naa
    assert abs((state.ha_conc + state.a_conc) - c_tot) < 1e-12
    assert abs((state.alpha_0 + state.alpha_1) - 1.0) < 1e-12


def test_fraction_at_ph_equals_pka():
    # When pH = pKa, alpha_0 = alpha_1 = 0.50
    ka = 10.0 ** (-5.0)
    state = compute_buffer_state(total_acid_conc=0.1, total_salt_conc=0.1, ka=ka)
    assert abs(state.alpha_0 - 0.50) < 0.01
    assert abs(state.alpha_1 - 0.50) < 0.01


# ===========================================================================
# 2. Van Slyke Buffer Capacity (beta) Tests
# ===========================================================================

def test_buffer_capacity_peak_at_pka():
    # Maximum buffer capacity occurs when pH = pKa
    ka = 10.0 ** (-4.76)
    c_tot = 0.20
    # Equimolar: pH ~ pKa
    state_eq = compute_buffer_state(total_acid_conc=0.10, total_salt_conc=0.10, ka=ka)
    # Off-center: pH ~ pKa - 0.6
    state_off = compute_buffer_state(total_acid_conc=0.16, total_salt_conc=0.04, ka=ka)
    assert state_eq.buffer_capacity_beta > state_off.buffer_capacity_beta


def test_buffer_capacity_proportional_to_concentration():
    # Van Slyke buffer term is directly proportional to total buffer concentration C
    ka = 10.0 ** (-4.76)
    state_1 = compute_buffer_state(total_acid_conc=0.05, total_salt_conc=0.05, ka=ka)
    state_2 = compute_buffer_state(total_acid_conc=0.10, total_salt_conc=0.10, ka=ka)
    ratio = state_2.buffer_capacity_beta / state_1.buffer_capacity_beta
    # Ratio should be nearly 2.0 (since water term is tiny at pH 4.76)
    assert abs(ratio - 2.0) < 0.01


def test_van_slyke_hand_computed_formula():
    # C = 0.1 M, at [H+] = Ka = 1e-5:
    # beta = ln(10) * ( [H+] + [OH-] + C * Ka * [H+] / (Ka + [H+])^2 )
    # At [H+] = Ka: buffer_term = C * Ka^2 / (2Ka)^2 = C / 4 = 0.025
    # beta ~ 2.302585 * 0.025 = 0.0575646 M / pH
    ka = 1.0e-5
    c_tot = 0.1
    beta_calc = compute_buffer_capacity(h_conc=ka, c_total=c_tot, ka=ka, kw=1e-14)
    expected = LN10 * (ka + 1e-14 / ka + c_tot * 0.25)
    assert abs(beta_calc - expected) < 1e-9
    assert abs(beta_calc - 0.0575646) < 1e-4


def test_max_buffer_capacity_utility():
    c_tot = 0.2
    b_max = max_buffer_capacity(c_total=c_tot)
    expected = LN10 * (2.0 * math.sqrt(1e-14) + 0.25 * 0.2)
    assert abs(b_max - expected) < 1e-9


# ===========================================================================
# 3. Addition of Strong Acid (HCl) and Strong Base (NaOH) Tests
# ===========================================================================

def test_add_strong_acid_decreases_ph():
    ka = 10.0 ** (-4.76)
    initial = compute_buffer_state(total_acid_conc=0.1, total_salt_conc=0.1, ka=ka)
    after_acid = compute_buffer_state(
        total_acid_conc=0.1, total_salt_conc=0.1, ka=ka, added_strong_acid_m=0.02
    )
    assert after_acid.ph < initial.ph
    assert after_acid.charge_balance_residual < 1e-10


def test_add_strong_base_increases_ph():
    ka = 10.0 ** (-4.76)
    initial = compute_buffer_state(total_acid_conc=0.1, total_salt_conc=0.1, ka=ka)
    after_base = compute_buffer_state(
        total_acid_conc=0.1, total_salt_conc=0.1, ka=ka, added_strong_base_m=0.02
    )
    assert after_base.ph > initial.ph
    assert after_base.charge_balance_residual < 1e-10


def test_buffering_resists_ph_change_compared_to_pure_water():
    # 0.01 M HCl added to pure water drops pH from 7.0 to 2.0 (change = 5.0 units)
    # 0.01 M HCl added to 0.1 M buffer drops pH by only ~0.09 units
    ka = 10.0 ** (-4.76)
    initial_buf = compute_buffer_state(total_acid_conc=0.1, total_salt_conc=0.1, ka=ka)
    acid_buf = compute_buffer_state(
        total_acid_conc=0.1, total_salt_conc=0.1, ka=ka, added_strong_acid_m=0.01
    )
    delta_ph = abs(acid_buf.ph - initial_buf.ph)
    assert delta_ph < 0.15


def test_excess_strong_acid_destroys_buffer():
    # Adding 0.25 M HCl to 0.1 M salt exhausts all A- and drives pH into strong acid regime
    ka = 10.0 ** (-4.76)
    exhausted = compute_buffer_state(
        total_acid_conc=0.1, total_salt_conc=0.1, ka=ka, added_strong_acid_m=0.25
    )
    # Excess HCl = 0.25 - 0.10 = 0.15 M => pH ~ -log10(0.15) = 0.82
    assert exhausted.ph < 1.5
    assert exhausted.charge_balance_residual < 1e-10


def test_excess_strong_base_destroys_buffer():
    # Adding 0.25 M NaOH to 0.1 M HA exhausts all HA and drives pH into strong base regime
    ka = 10.0 ** (-4.76)
    exhausted = compute_buffer_state(
        total_acid_conc=0.1, total_salt_conc=0.1, ka=ka, added_strong_base_m=0.25
    )
    # Excess NaOH = 0.25 - 0.10 = 0.15 M => pOH ~ 0.82 => pH ~ 13.18
    assert exhausted.ph > 12.5
    assert exhausted.charge_balance_residual < 1e-10


def test_simulate_buffer_stress_acid_curve_monotonicity():
    # Incremental addition of HCl must produce monotonically decreasing pH
    curve = simulate_buffer_stress(
        initial_volume_ml=100.0,
        acid_conc=0.1,
        salt_conc=0.1,
        ka=10.0 ** (-4.76),
        titrant_type="hcl",
        titrant_conc_m=1.0,
        max_added_ml=15.0,
        num_steps=15,
    )
    assert len(curve) == 15
    for i in range(len(curve) - 1):
        assert curve[i].ph >= curve[i + 1].ph


def test_simulate_buffer_stress_base_curve_monotonicity():
    # Incremental addition of NaOH must produce monotonically increasing pH
    curve = simulate_buffer_stress(
        initial_volume_ml=100.0,
        acid_conc=0.1,
        salt_conc=0.1,
        ka=10.0 ** (-4.76),
        titrant_type="naoh",
        titrant_conc_m=1.0,
        max_added_ml=15.0,
        num_steps=15,
    )
    assert len(curve) == 15
    for i in range(len(curve) - 1):
        assert curve[i].ph <= curve[i + 1].ph


# ===========================================================================
# 4. Limiting Cases & Boundary Conditions
# ===========================================================================

def test_limiting_case_zero_buffer_pure_water():
    # With 0 acid and 0 salt, exact solver reduces to pure water: [H+] = sqrt(Kw) = 1e-7, pH = 7.0
    ka = 1e-5
    h = solve_exact_buffer_h(total_acid_conc=0.0, total_salt_conc=0.0, ka=ka, kw=1e-14)
    assert abs(h - 1e-7) < 1e-12
    ph = -math.log10(h)
    assert abs(ph - 7.0) < 1e-5


def test_limiting_case_pure_strong_acid():
    # 0 buffer, 0.05 M HCl added -> pH = -log10(0.05) = 1.3010
    ka = 1e-5
    state = compute_buffer_state(
        total_acid_conc=0.0, total_salt_conc=0.0, ka=ka, added_strong_acid_m=0.05
    )
    expected_ph = -math.log10(0.05)
    assert abs(state.ph - expected_ph) < 1e-4


def test_limiting_case_pure_strong_base():
    # 0 buffer, 0.05 M NaOH added -> pOH = 1.3010 => pH = 12.6990
    ka = 1e-5
    state = compute_buffer_state(
        total_acid_conc=0.0, total_salt_conc=0.0, ka=ka, added_strong_base_m=0.05
    )
    expected_ph = 14.0 - (-math.log10(0.05))
    assert abs(state.ph - expected_ph) < 1e-4


def test_limiting_case_extreme_dilution():
    # C = 1e-7 M, near water self-ionization limit. pH must remain close to 7.0 (slightly acidic due to Ka 1e-5)
    ka = 1e-5
    state = compute_buffer_state(total_acid_conc=1e-7, total_salt_conc=1e-7, ka=ka)
    assert 6.7 < state.ph < 7.2
    assert state.charge_balance_residual < 1e-10


def test_buffer_resists_dilution_ph_stability():
    # Diluting equimolar 0.1 M buffer 10-fold to 0.01 M barely changes pH (< 0.05 units)
    ka = 10.0 ** (-4.76)
    state_conc = compute_buffer_state(total_acid_conc=0.1, total_salt_conc=0.1, ka=ka)
    state_dilute = compute_buffer_state(total_acid_conc=0.01, total_salt_conc=0.01, ka=ka)
    assert abs(state_conc.ph - state_dilute.ph) < 0.05


def test_buffer_capacity_minimum_at_neutral_pure_water():
    # In pure water at pH 7, buffer capacity is only the water self-ionization term: ln(10) * 2e-7 ~ 4.605e-7
    ka = 1e-5
    state_water = compute_buffer_state(total_acid_conc=0.0, total_salt_conc=0.0, ka=ka)
    assert abs(state_water.buffer_capacity_beta - (LN10 * 2.0e-7)) < 1e-9


def test_buffer_stress_large_acid_addition():
    # Large excess acid addition completely overwhelms buffer capacity
    curve = simulate_buffer_stress(
        initial_volume_ml=100.0,
        acid_conc=0.1,
        salt_conc=0.1,
        ka=10.0 ** (-4.76),
        titrant_type="hcl",
        titrant_conc_m=2.0,
        max_added_ml=20.0,
        num_steps=10,
    )
    final_point = curve[-1]
    assert final_point.ph < 1.0


def test_buffer_stress_large_base_addition():
    # Large excess base addition overwhelms buffer and raises pH > 13
    curve = simulate_buffer_stress(
        initial_volume_ml=100.0,
        acid_conc=0.1,
        salt_conc=0.1,
        ka=10.0 ** (-4.76),
        titrant_type="naoh",
        titrant_conc_m=2.0,
        max_added_ml=20.0,
        num_steps=10,
    )
    final_point = curve[-1]
    assert final_point.ph > 13.0


def test_hh_exact_at_ratio_1():
    # At ratio 1.0, HH predicts exactly pKa
    assert henderson_hasselbalch_ph(pka=4.76, conjugate_base_conc=0.1, weak_acid_conc=0.1) == 4.76


def test_agreement_with_titration_at_half_equivalence():
    """
    In chem_titration.py:
    compute_ph_weak(ca=0.1, va_ml=25.0, cb=0.1, vb_ml=12.5) computes the pH of 25 mL 0.1 M acetic acid
    titrated with 12.5 mL 0.1 M NaOH.
    At this half-equivalence point:
      Total volume = 37.5 mL
      Moles of HA consumed = 0.1 * 12.5e-3 = 1.25e-3 moles
      Moles of A- formed = 1.25e-3 moles
      Moles of HA remaining = (0.1 * 25.0e-3) - 1.25e-3 = 1.25e-3 moles
      Concentrations: [HA] = [A-] = 1.25e-3 / 37.5e-3 = 0.033333 M
    The exact solver in chem.buffer matches compute_ph_weak to within 1e-3 pH units.
    """
    titration_ph = compute_ph_weak(ca=0.1, va_ml=25.0, cb=0.1, vb_ml=12.5)

    c_ha = 1.25e-3 / 37.5e-3
    c_salt = 1.25e-3 / 37.5e-3
    ka = 10.0 ** (-4.76)
    buffer_state = compute_buffer_state(total_acid_conc=c_ha, total_salt_conc=c_salt, ka=ka)

    assert abs(buffer_state.ph - titration_ph) < 1e-3


def test_agreement_with_titration_before_half_equivalence():
    # vb = 8.0 mL: moles A- = 0.8e-3; moles HA = 2.5e-3 - 0.8e-3 = 1.7e-3; V = 33.0 mL
    titration_ph = compute_ph_weak(ca=0.1, va_ml=25.0, cb=0.1, vb_ml=8.0)
    v_tot = 33.0e-3
    c_ha = 1.7e-3 / v_tot
    c_salt = 0.8e-3 / v_tot
    ka = 10.0 ** (-4.76)
    buffer_state = compute_buffer_state(total_acid_conc=c_ha, total_salt_conc=c_salt, ka=ka)

    assert abs(buffer_state.ph - titration_ph) < 1e-3


def test_agreement_with_titration_after_half_equivalence():
    # vb = 18.0 mL: moles A- = 1.8e-3; moles HA = 2.5e-3 - 1.8e-3 = 0.7e-3; V = 43.0 mL
    titration_ph = compute_ph_weak(ca=0.1, va_ml=25.0, cb=0.1, vb_ml=18.0)
    v_tot = 43.0e-3
    c_ha = 0.7e-3 / v_tot
    c_salt = 1.8e-3 / v_tot
    ka = 10.0 ** (-4.76)
    buffer_state = compute_buffer_state(total_acid_conc=c_ha, total_salt_conc=c_salt, ka=ka)

    assert abs(buffer_state.ph - titration_ph) < 1e-3


def test_agreement_with_titration_at_three_quarter_equivalence():
    # vb = 18.75 mL (75% of 25.0 mL eq point): moles A- = 1.875e-3; moles HA = 0.625e-3; V = 43.75 mL
    titration_ph = compute_ph_weak(ca=0.1, va_ml=25.0, cb=0.1, vb_ml=18.75)
    v_tot = 43.75e-3
    c_ha = 0.625e-3 / v_tot
    c_salt = 1.875e-3 / v_tot
    ka = 10.0 ** (-4.76)
    buffer_state = compute_buffer_state(total_acid_conc=c_ha, total_salt_conc=c_salt, ka=ka)

    assert abs(buffer_state.ph - titration_ph) < 1e-3


# ===========================================================================
# 7. Invalid Parameters & Error Handling Tests
# ===========================================================================

def test_buffer_capacity_decreases_away_from_pka_acidic():
    ka = 10.0 ** (-4.76)
    state_center = compute_buffer_state(total_acid_conc=0.1, total_salt_conc=0.1, ka=ka)
    state_acidic = compute_buffer_state(total_acid_conc=0.18, total_salt_conc=0.02, ka=ka)
    assert state_acidic.buffer_capacity_beta < state_center.buffer_capacity_beta


def test_buffer_capacity_decreases_away_from_pka_basic():
    ka = 10.0 ** (-4.76)
    state_center = compute_buffer_state(total_acid_conc=0.1, total_salt_conc=0.1, ka=ka)
    state_basic = compute_buffer_state(total_acid_conc=0.02, total_salt_conc=0.18, ka=ka)
    assert state_basic.buffer_capacity_beta < state_center.buffer_capacity_beta


def test_buffer_alpha_fractions_sum_to_unity():
    ka = 10.0 ** (-4.76)
    for c_a in [0.01, 0.05, 0.1, 0.5]:
        for c_b in [0.01, 0.05, 0.1, 0.5]:
            state = compute_buffer_state(total_acid_conc=c_a, total_salt_conc=c_b, ka=ka)
            assert abs((state.alpha_0 + state.alpha_1) - 1.0) < 1e-12


def test_phosphate_buffer_ph():
    # H3PO4 / H2PO4- system: pKa1 = 2.15 (Ka1 = 7.08e-3 M)
    # Because Ka1 is relatively large, [H+] (~0.00625 M) is non-negligible compared to C (0.1 M),
    # causing the exact charge-balance pH (2.204) to deviate slightly from naive pKa (2.15).
    ka1 = 10.0 ** (-2.15)
    state = compute_buffer_state(total_acid_conc=0.1, total_salt_conc=0.1, ka=ka1)
    assert abs(state.ph - 2.15) < 0.08
    assert state.charge_balance_residual < 1e-10


def test_buffer_stress_zero_added_volume_unchanged():
    curve = simulate_buffer_stress(
        initial_volume_ml=100.0,
        acid_conc=0.1,
        salt_conc=0.1,
        ka=10.0 ** (-4.76),
        titrant_type="hcl",
        titrant_conc_m=1.0,
        max_added_ml=0.0,
        num_steps=5,
    )
    assert len(curve) == 5
    for pt in curve:
        assert pt.added_volume_ml == 0.0
        assert abs(pt.ph - 4.76) < 0.02


def test_agreement_with_titration_quarter_equivalence():
    # vb = 6.25 mL (25% of 25.0 mL eq point): moles A- = 0.625e-3; moles HA = 1.875e-3; V = 31.25 mL
    titration_ph = compute_ph_weak(ca=0.1, va_ml=25.0, cb=0.1, vb_ml=6.25)
    v_tot = 31.25e-3
    c_ha = 1.875e-3 / v_tot
    c_salt = 0.625e-3 / v_tot
    ka = 10.0 ** (-4.76)
    buffer_state = compute_buffer_state(total_acid_conc=c_ha, total_salt_conc=c_salt, ka=ka)

    assert abs(buffer_state.ph - titration_ph) < 1e-3


def test_negative_concentrations_raise_value_error():
    ka = 10.0 ** (-4.76)
    with pytest.raises(ValueError):
        solve_exact_buffer_h(total_acid_conc=-0.1, total_salt_conc=0.1, ka=ka)
    with pytest.raises(ValueError):
        solve_exact_buffer_h(total_acid_conc=0.1, total_salt_conc=-0.1, ka=ka)
    with pytest.raises(ValueError):
        solve_exact_buffer_h(total_acid_conc=0.1, total_salt_conc=0.1, ka=-1e-5)
    with pytest.raises(ValueError):
        henderson_hasselbalch_ph(pka=4.76, conjugate_base_conc=-0.1, weak_acid_conc=0.1)
    with pytest.raises(ValueError):
        henderson_hasselbalch_ph(pka=4.76, conjugate_base_conc=0.1, weak_acid_conc=0.0)
    with pytest.raises(ValueError):
        compute_buffer_capacity(h_conc=-1.0, c_total=0.1, ka=ka)
    with pytest.raises(ValueError):
        simulate_buffer_stress(
            initial_volume_ml=100.0,
            acid_conc=0.1,
            salt_conc=0.1,
            ka=ka,
            titrant_type="invalid_titrant",
            titrant_conc_m=1.0,
            max_added_ml=10.0,
        )
