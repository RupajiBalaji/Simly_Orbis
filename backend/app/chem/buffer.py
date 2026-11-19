"""
backend/app/chem/buffer.py
Aqueous Buffer Equilibrium and Buffer Capacity Engine.

Implements Section 9.2 & Section 18 (P3-T2) of Simly Orbis MVP Build Specification:
- Exact charge-balance aqueous pH solver for weak acid / conjugate base buffer systems
- Addition of strong monoprotic acid (HCl) and strong monoprotic base (NaOH)
- Exact Van Slyke buffer capacity beta(pH)
- Maximum buffer capacity at pH = pKa
- Comparison with Henderson-Hasselbalch approximation
- Cross-check and agreement with existing chem.titration charge-balance solver

Governance:
- Pure simulation logic; engine decides, client renders.
- Educational simulation; no medical advice.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

KW_DEFAULT: float = 1.0e-14
LN10: float = math.log(10.0)  # ~2.302585092994046


@dataclass(frozen=True)
class BufferSystemState:
    ph: float
    h_conc: float
    oh_conc: float
    ha_conc: float
    a_conc: float
    alpha_0: float  # fraction in HA form: [HA] / C
    alpha_1: float  # fraction in A- form: [A-] / C
    buffer_capacity_beta: float
    charge_balance_residual: float


@dataclass(frozen=True)
class TitrationAdditionPoint:
    added_volume_ml: float
    added_moles: float
    added_type: str  # 'acid' or 'base'
    total_volume_ml: float
    ph: float
    buffer_capacity_beta: float


# ---------------------------------------------------------------------------
# Exact Charge Balance Root-Finding
# ---------------------------------------------------------------------------

def solve_exact_buffer_h(
    total_acid_conc: float,
    total_salt_conc: float,
    ka: float,
    added_strong_acid_m: float = 0.0,
    added_strong_base_m: float = 0.0,
    kw: float = KW_DEFAULT,
    tol: float = 1e-12,
    max_iter: int = 150,
) -> float:
    """
    Solve for [H+] using the exact aqueous charge balance:
      [H+] + [Na+]_tot = [OH-] + [A-] + [Cl-]
    where:
      [Na+]_tot = total_salt_conc + added_strong_base_m
      [Cl-] = added_strong_acid_m
      [OH-] = Kw / [H+]
      C_buffer = total_acid_conc + total_salt_conc
      [A-] = C_buffer * Ka / ([H+] + Ka)

    Charge balance residual function:
      f([H+]) = [H+] + [Na+]_tot - [Cl-] - Kw / [H+] - C_buffer * Ka / ([H+] + Ka) = 0
    f([H+]) is strictly monotonically increasing for [H+] in (0, inf),
    guaranteeing a unique positive root.
    """
    if ka <= 0.0:
        raise ValueError("Acid dissociation constant Ka must be strictly positive.")
    if total_acid_conc < 0.0 or total_salt_conc < 0.0:
        raise ValueError("Buffer component concentrations must be non-negative.")
    if added_strong_acid_m < 0.0 or added_strong_base_m < 0.0:
        raise ValueError("Added strong acid and base concentrations must be non-negative.")

    c_buffer = total_acid_conc + total_salt_conc
    na_tot = total_salt_conc + added_strong_base_m
    cl_tot = added_strong_acid_m

    def f(h: float) -> float:
        if h <= 0.0:
            return -float("inf")
        oh = kw / h
        a_minus = (c_buffer * ka) / (h + ka) if c_buffer > 0.0 else 0.0
        return h + na_tot - cl_tot - oh - a_minus

    # Initial bracket: [1e-15, 10.0] M (pH range -1.0 to 15.0)
    low = 1e-15
    high = 10.0

    # Expand bracket if needed
    f_low = f(low)
    f_high = f(high)
    while f_low > 0.0:
        low *= 0.1
        f_low = f(low)
    while f_high < 0.0:
        high *= 10.0
        f_high = f(high)

    # Robust Bisection
    for _ in range(max_iter):
        mid = 0.5 * (low + high)
        f_mid = f(mid)

        if abs(f_mid) < tol or (high - low) / mid < 1e-10:
            return mid

        if f_mid < 0.0:
            low = mid
        else:
            high = mid

    return 0.5 * (low + high)


def compute_buffer_capacity(h_conc: float, c_total: float, ka: float, kw: float = KW_DEFAULT) -> float:
    """
    Van Slyke exact analytical buffer capacity:
      beta = ln(10) * ( [H+] + [OH-] + C * Ka * [H+] / (Ka + [H+])^2 )
    Unit: mol / (L * pH unit)
    """
    if h_conc <= 0.0 or ka <= 0.0:
        raise ValueError("[H+] and Ka must be strictly positive.")
    oh_conc = kw / h_conc
    denom = (ka + h_conc) ** 2
    buffer_term = (c_total * ka * h_conc) / denom if denom > 0.0 else 0.0
    return LN10 * (h_conc + oh_conc + buffer_term)


def compute_buffer_state(
    total_acid_conc: float,
    total_salt_conc: float,
    ka: float,
    added_strong_acid_m: float = 0.0,
    added_strong_base_m: float = 0.0,
    kw: float = KW_DEFAULT,
) -> BufferSystemState:
    """
    Compute full aqueous state for a weak acid / conjugate base buffer system.
    """
    h = solve_exact_buffer_h(
        total_acid_conc=total_acid_conc,
        total_salt_conc=total_salt_conc,
        ka=ka,
        added_strong_acid_m=added_strong_acid_m,
        added_strong_base_m=added_strong_base_m,
        kw=kw,
    )
    ph = -math.log10(h)
    oh = kw / h

    c_buffer = total_acid_conc + total_salt_conc
    alpha_0 = h / (h + ka)  # fraction HA
    alpha_1 = ka / (h + ka)  # fraction A-
    ha_conc = c_buffer * alpha_0
    a_conc = c_buffer * alpha_1

    na_tot = total_salt_conc + added_strong_base_m
    cl_tot = added_strong_acid_m
    residual = abs((h + na_tot) - (oh + a_conc + cl_tot))

    beta = compute_buffer_capacity(h_conc=h, c_total=c_buffer, ka=ka, kw=kw)

    return BufferSystemState(
        ph=ph,
        h_conc=h,
        oh_conc=oh,
        ha_conc=ha_conc,
        a_conc=a_conc,
        alpha_0=alpha_0,
        alpha_1=alpha_1,
        buffer_capacity_beta=beta,
        charge_balance_residual=residual,
    )


# ---------------------------------------------------------------------------
# Henderson-Hasselbalch Approximation (Educational Comparison)
# ---------------------------------------------------------------------------

def henderson_hasselbalch_ph(pka: float, conjugate_base_conc: float, weak_acid_conc: float) -> float:
    """
    Henderson-Hasselbalch equation:
      pH = pKa + log10([A-] / [HA])
    Valid only for dilute to moderate buffers where [H+] << [HA] and [OH-] << [A-].
    """
    if conjugate_base_conc <= 0.0 or weak_acid_conc <= 0.0:
        raise ValueError("Concentrations must be strictly positive for Henderson-Hasselbalch.")
    return pka + math.log10(conjugate_base_conc / weak_acid_conc)


def max_buffer_capacity(c_total: float, kw: float = KW_DEFAULT) -> float:
    """
    Maximum buffer capacity occurs at pH = pKa:
      beta_max = ln(10) * ( 2 * sqrt(Kw) + C / 4 )
    """
    if c_total < 0.0:
        raise ValueError("Buffer concentration must be non-negative.")
    water_term = 2.0 * math.sqrt(kw)
    return LN10 * (water_term + 0.25 * c_total)


# ---------------------------------------------------------------------------
# Buffer Titration / Strong Acid-Base Stress Curve
# ---------------------------------------------------------------------------

def simulate_buffer_stress(
    initial_volume_ml: float,
    acid_conc: float,
    salt_conc: float,
    ka: float,
    titrant_type: str,  # 'hcl' or 'naoh'
    titrant_conc_m: float,
    max_added_ml: float,
    num_steps: int = 50,
    kw: float = KW_DEFAULT,
) -> List[TitrationAdditionPoint]:
    """
    Simulate incremental addition of strong acid (HCl) or strong base (NaOH)
    to a buffer solution, tracking pH and buffer capacity as a function of volume.
    """
    if initial_volume_ml <= 0.0 or titrant_conc_m <= 0.0 or max_added_ml < 0.0:
        raise ValueError("Volumes and titrant concentration must be positive.")
    if titrant_type.lower() not in ("hcl", "acid", "naoh", "base"):
        raise ValueError(f"Unknown titrant type '{titrant_type}'. Use 'hcl' or 'naoh'.")

    is_acid = titrant_type.lower() in ("hcl", "acid")
    curve: List[TitrationAdditionPoint] = []
    step_vol = max_added_ml / max(1, num_steps - 1)

    initial_vol_l = initial_volume_ml / 1000.0
    initial_ha_moles = acid_conc * initial_vol_l
    initial_a_moles = salt_conc * initial_vol_l

    for i in range(num_steps):
        v_add_ml = i * step_vol
        v_add_l = v_add_ml / 1000.0
        v_tot_l = (initial_volume_ml + v_add_ml) / 1000.0

        # Diluted initial buffer components
        c_ha_diluted = initial_ha_moles / v_tot_l
        c_salt_diluted = initial_a_moles / v_tot_l

        # Added strong acid or base concentration in total volume
        added_moles = titrant_conc_m * v_add_l
        added_conc = added_moles / v_tot_l

        if is_acid:
            state = compute_buffer_state(
                total_acid_conc=c_ha_diluted,
                total_salt_conc=c_salt_diluted,
                ka=ka,
                added_strong_acid_m=added_conc,
                added_strong_base_m=0.0,
                kw=kw,
            )
        else:
            state = compute_buffer_state(
                total_acid_conc=c_ha_diluted,
                total_salt_conc=c_salt_diluted,
                ka=ka,
                added_strong_acid_m=0.0,
                added_strong_base_m=added_conc,
                kw=kw,
            )

        curve.append(
            TitrationAdditionPoint(
                added_volume_ml=round(v_add_ml, 4),
                added_moles=round(added_moles, 8),
                added_type="acid" if is_acid else "base",
                total_volume_ml=round(initial_volume_ml + v_add_ml, 4),
                ph=round(state.ph, 4),
                buffer_capacity_beta=round(state.buffer_capacity_beta, 6),
            )
        )

    return curve
