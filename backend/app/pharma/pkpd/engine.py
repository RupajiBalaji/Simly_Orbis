"""
backend/app/pharma/pkpd/engine.py
Deterministic One- and Two-Compartment PK/PD Simulation Engine.

Supports:
- Routes: iv_bolus, iv_infusion (constant rate R0 over duration t_inf), oral (first-order ka, lag time t_lag, F).
- Closed-form analytical solutions (biexponential with alpha, beta, A, B).
- Numerical cross-check via 4th-order Runge-Kutta (RK4).
- Pharmacodynamics: Direct Emax / Sigmoid Emax (E0, Emax, EC50, Hill n) with optional effect-compartment (ke0).
- Adult covariate scaling: Allometric weight scaling (CL ~ (WT/70)^0.75, V ~ (WT/70)^1.0), renal fraction scaling, age multiplier.
- Adult-only covariate ranges: Age 18-90 yr, Weight 40-150 kg, CrCl 15-150 mL/min.

Educational simulation platform. Not medical advice. Not clinical evidence.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np


class ModelType(str, enum.Enum):
    one_compartment = "one_compartment"
    two_compartment = "two_compartment"


class RouteType(str, enum.Enum):
    iv_bolus = "iv_bolus"
    iv_infusion = "iv_infusion"
    oral = "oral"


@dataclass
class AdultCovariates:
    """Adult patient covariates strictly bounded (R6: no pediatric support)."""
    weight_kg: float = 70.0
    age_yr: float = 35.0
    crcl_ml_min: float = 100.0  # Creatinine Clearance in mL/min

    def validate(self) -> None:
        if not (40.0 <= self.weight_kg <= 150.0):
            raise ValueError(f"Weight {self.weight_kg} kg is outside adult range [40.0, 150.0] kg.")
        if not (18.0 <= self.age_yr <= 90.0):
            raise ValueError(f"Age {self.age_yr} yr is outside adult range [18.0, 90.0] yr.")
        if not (15.0 <= self.crcl_ml_min <= 150.0):
            raise ValueError(f"Creatinine clearance {self.crcl_ml_min} mL/min is outside adult range [15.0, 150.0] mL/min.")


@dataclass
class PKPDParams:
    """Core parameters for one- or two-compartment PK/PD model."""
    model_type: ModelType = ModelType.one_compartment
    route: RouteType = RouteType.oral
    dose_mg: float = 500.0
    n_doses: int = 1
    interval_h: float = 6.0

    # PK parameters (reference adult 70 kg)
    cl: float = 15.0         # Central clearance L/h (k10 = cl / v1)
    v1: float = 50.0         # Central volume of distribution L
    q: float = 0.0           # Inter-compartmental clearance L/h (two-compartment)
    v2: float = 0.0          # Peripheral volume of distribution L (two-compartment)

    # Route specifics
    ka: float = 1.5          # Absorption rate constant (1/h)
    f_bioav: float = 1.0     # Bioavailability F in (0.0, 1.0]
    t_lag: float = 0.0       # Absorption lag time (h)
    infusion_duration_h: float = 1.0  # Duration for iv_infusion (h)

    # Renal fraction for clearance
    fe: float = 0.0          # Fraction cleared renally in [0.0, 1.0]

    # Pharmacodynamics (Emax model)
    pd_enabled: bool = False
    e0: float = 0.0          # Baseline effect
    emax: float = 100.0      # Maximum effect attributable to drug
    ec50: float = 10.0       # Concentration producing 50% of Emax (mg/L)
    hill_n: float = 1.0      # Sigmoid cooperativity parameter (>= 0.1)
    ke0: float = 0.0         # Effect compartment equilibration rate constant (1/h, 0 = direct)

    # Target window (game-balanced, not clinical)
    target_window_low: float = 5.0
    target_window_high: float = 20.0

    def validate(self) -> None:
        if self.dose_mg <= 0:
            raise ValueError(f"Dose must be > 0, got {self.dose_mg}")
        if self.n_doses < 1:
            raise ValueError(f"n_doses must be >= 1, got {self.n_doses}")
        if self.n_doses > 1 and self.interval_h <= 0:
            raise ValueError(f"interval_h must be > 0 when n_doses > 1, got {self.interval_h}")
        if self.cl <= 0:
            raise ValueError(f"Clearance (cl) must be > 0, got {self.cl}")
        if self.v1 <= 0:
            raise ValueError(f"Central volume (v1) must be > 0, got {self.v1}")
        if not (0.0 < self.f_bioav <= 1.0):
            raise ValueError(f"Bioavailability (f_bioav) must be in (0, 1], got {self.f_bioav}")
        if self.t_lag < 0:
            raise ValueError(f"Lag time (t_lag) must be >= 0, got {self.t_lag}")
        if not (0.0 <= self.fe <= 1.0):
            raise ValueError(f"Renal fraction (fe) must be in [0, 1], got {self.fe}")

        if self.route == RouteType.oral:
            if self.ka <= 0:
                raise ValueError(f"Absorption rate constant (ka) must be > 0, got {self.ka}")
        elif self.route == RouteType.iv_infusion:
            if self.infusion_duration_h <= 0:
                raise ValueError(f"Infusion duration must be > 0, got {self.infusion_duration_h}")

        if self.model_type == ModelType.two_compartment:
            if self.v2 <= 0:
                raise ValueError(f"Peripheral volume (v2) must be > 0 for two-compartment, got {self.v2}")
            if self.q <= 0:
                raise ValueError(f"Inter-compartmental clearance (q) must be > 0 for two-compartment, got {self.q}")

        if self.pd_enabled:
            if self.ec50 <= 0:
                raise ValueError(f"EC50 must be > 0, got {self.ec50}")
            if self.hill_n <= 0:
                raise ValueError(f"Hill coefficient n must be > 0, got {self.hill_n}")
            if self.ke0 < 0:
                raise ValueError(f"ke0 must be >= 0, got {self.ke0}")


def apply_covariates(base_params: PKPDParams, cov: AdultCovariates) -> PKPDParams:
    """
    Apply standard allometric and physiological adult covariate scaling.
    - Allometric weight scaling: CL * (WT/70)^0.75, V * (WT/70)^1.0, Q * (WT/70)^0.75, V2 * (WT/70)^1.0
    - Renal function scaling: CL = CL_nonrenal + CL_renal * (CrCl / 120.0)
    - Age scaling: Mild physiological decline above 65: CL * (1.0 - 0.005 * max(0.0, Age - 65))
    """
    cov.validate()
    scaled = PKPDParams(**base_params.__dict__)

    wt_ratio = cov.weight_kg / 70.0
    cl_allometric = base_params.cl * (wt_ratio ** 0.75)
    v1_allometric = base_params.v1 * (wt_ratio ** 1.0)

    # Renal fraction separation
    cl_nonrenal = cl_allometric * (1.0 - base_params.fe)
    cl_renal = cl_allometric * base_params.fe * (cov.crcl_ml_min / 120.0)
    cl_total = cl_nonrenal + cl_renal

    # Age effect on systemic clearance (0.5% per year above age 65)
    if cov.age_yr > 65.0:
        age_factor = max(0.60, 1.0 - 0.005 * (cov.age_yr - 65.0))
        cl_total *= age_factor

    scaled.cl = max(0.01, cl_total)
    scaled.v1 = max(0.1, v1_allometric)

    if base_params.model_type == ModelType.two_compartment:
        scaled.q = max(0.01, base_params.q * (wt_ratio ** 0.75))
        scaled.v2 = max(0.1, base_params.v2 * (wt_ratio ** 1.0))

    return scaled


@dataclass
class BiexponentialCoefficients:
    """Micro-rate and biexponential macroscopic coefficients for two-compartment model."""
    k10: float
    k12: float
    k21: float
    alpha: float
    beta: float
    a_iv: float
    b_iv: float


def compute_biexponential_coefficients(params: PKPDParams) -> BiexponentialCoefficients:
    """
    Compute micro-constants and roots alpha, beta for 2-compartment model.
    k10 = CL / V1
    k12 = Q / V1
    k21 = Q / V2
    Characteristic equation: s^2 + (k10 + k12 + k21)s + k10*k21 = 0
    alpha + beta = k10 + k12 + k21
    alpha * beta = k10 * k21
    """
    k10 = params.cl / params.v1
    k12 = params.q / params.v1
    k21 = params.q / params.v2

    sum_k = k10 + k12 + k21
    prod_k = k10 * k21
    disc = max(0.0, sum_k * sum_k - 4.0 * prod_k)
    sqrt_disc = math.sqrt(disc)

    alpha = 0.5 * (sum_k + sqrt_disc)
    beta = 0.5 * (sum_k - sqrt_disc)

    # Unit IV bolus macro-coefficients:
    # C(t) = D * (A_iv * exp(-alpha*t) + B_iv * exp(-beta*t))
    # where A_iv = (alpha - k21) / (V1 * (alpha - beta)), B_iv = (k21 - beta) / (V1 * (alpha - beta))
    if abs(alpha - beta) > 1e-12:
        a_iv = (alpha - k21) / (params.v1 * (alpha - beta))
        b_iv = (k21 - beta) / (params.v1 * (alpha - beta))
    else:
        a_iv = 0.5 / params.v1
        b_iv = 0.5 / params.v1

    return BiexponentialCoefficients(
        k10=k10, k12=k12, k21=k21,
        alpha=alpha, beta=beta,
        a_iv=a_iv, b_iv=b_iv,
    )


@dataclass
class PKPDResult:
    """Full simulation timecourse and derived pharmacokinetic/pharmacodynamic metrics."""
    times: list[float]
    concentrations: list[float]
    effect: list[float]
    ce: list[float]  # effect compartment concentrations
    cmax: float
    tmax: float
    auc_analytic: float
    auc_trapezoid: float
    terminal_half_life_h: float
    clearance_l_h: float
    steady_state_volume_l: float
    accumulation_ratio: float
    time_to_steady_state_h: float
    time_in_target_h: float
    time_above_target_h: float
    time_below_target_h: float
    time_in_effect_h: float
    total_duration_h: float
    params: PKPDParams = field(default_factory=PKPDParams)


def _eval_one_comp_single(t: float, params: PKPDParams, dose: float) -> float:
    """Closed-form concentration at time t after a single dose for 1-compartment."""
    if t < 0.0:
        return 0.0
    k10 = params.cl / params.v1

    if params.route == RouteType.iv_bolus:
        return (dose / params.v1) * math.exp(-k10 * t)

    elif params.route == RouteType.iv_infusion:
        t_inf = params.infusion_duration_h
        r0 = dose / t_inf
        if t <= t_inf:
            return (r0 / params.cl) * (1.0 - math.exp(-k10 * t))
        else:
            c_end = (r0 / params.cl) * (1.0 - math.exp(-k10 * t_inf))
            return c_end * math.exp(-k10 * (t - t_inf))

    else:  # oral
        t_eff = t - params.t_lag
        if t_eff < 0.0:
            return 0.0
        ka = params.ka
        f = params.f_bioav
        if abs(ka - k10) < 1e-9:
            return (f * dose * ka / params.v1) * t_eff * math.exp(-k10 * t_eff)
        return (
            (f * dose * ka) / (params.v1 * (ka - k10))
            * (math.exp(-k10 * t_eff) - math.exp(-ka * t_eff))
        )


def _eval_two_comp_single(t: float, params: PKPDParams, dose: float, biexp: BiexponentialCoefficients) -> float:
    """Closed-form concentration at time t after a single dose for 2-compartment."""
    if t < 0.0:
        return 0.0
    alpha = biexp.alpha
    beta = biexp.beta
    a_iv = biexp.a_iv
    b_iv = biexp.b_iv

    if params.route == RouteType.iv_bolus:
        return dose * (a_iv * math.exp(-alpha * t) + b_iv * math.exp(-beta * t))

    elif params.route == RouteType.iv_infusion:
        t_inf = params.infusion_duration_h
        r0 = dose / t_inf
        if t <= t_inf:
            term_a = (a_iv / alpha) * (1.0 - math.exp(-alpha * t))
            term_b = (b_iv / beta) * (1.0 - math.exp(-beta * t))
            return r0 * (term_a + term_b)
        else:
            term_a = (a_iv / alpha) * (1.0 - math.exp(-alpha * t_inf)) * math.exp(-alpha * (t - t_inf))
            term_b = (b_iv / beta) * (1.0 - math.exp(-beta * t_inf)) * math.exp(-beta * (t - t_inf))
            return r0 * (term_a + term_b)

    else:  # oral
        t_eff = t - params.t_lag
        if t_eff < 0.0:
            return 0.0
        ka = params.ka
        f = params.f_bioav

        # Closed-form tri-exponential oral solution
        # C(t) = F*D*ka * [ A_iv/(ka - alpha)*(exp(-alpha*t) - exp(-ka*t)) + B_iv/(ka - beta)*(exp(-beta*t) - exp(-ka*t)) ]
        term_a = (a_iv / (ka - alpha)) * (math.exp(-alpha * t_eff) - math.exp(-ka * t_eff)) if abs(ka - alpha) > 1e-9 else a_iv * t_eff * math.exp(-alpha * t_eff)
        term_b = (b_iv / (ka - beta)) * (math.exp(-beta * t_eff) - math.exp(-ka * t_eff)) if abs(ka - beta) > 1e-9 else b_iv * t_eff * math.exp(-beta * t_eff)
        return f * dose * ka * (term_a + term_b)


def simulate_pkpd(params: PKPDParams, t_end_h: float | None = None, dt_h: float = 0.05) -> PKPDResult:
    """
    Execute full closed-form simulation of PK/PD across multi-dose regimen.
    """
    params.validate()

    # Determine total time span
    if t_end_h is None:
        last_dose_time = (params.n_doses - 1) * params.interval_h
        # Add at least 5 terminal half-lives or 24h
        if params.model_type == ModelType.two_compartment:
            biexp_temp = compute_biexponential_coefficients(params)
            t_half_term = math.log(2.0) / biexp_temp.beta
        else:
            t_half_term = math.log(2.0) / (params.cl / params.v1)
        t_end_h = max(24.0, last_dose_time + max(24.0, 5.0 * t_half_term))

    t_end_h = round(t_end_h, 3)
    n_points = int(math.ceil(t_end_h / dt_h)) + 1
    times = [round(i * dt_h, 6) for i in range(n_points)]

    dose_times = [i * params.interval_h for i in range(params.n_doses)]

    biexp = compute_biexponential_coefficients(params) if params.model_type == ModelType.two_compartment else None

    # Compute plasma concentrations via linear superposition
    c_list: list[float] = []
    for t in times:
        c_t = 0.0
        for td in dose_times:
            if t >= td:
                if params.model_type == ModelType.two_compartment and biexp is not None:
                    c_t += _eval_two_comp_single(t - td, params, params.dose_mg, biexp)
                else:
                    c_t += _eval_one_comp_single(t - td, params, params.dose_mg)
        c_list.append(max(0.0, c_t))

    # Effect compartment & PD calculation
    ce_list: list[float] = []
    e_list: list[float] = []

    if params.pd_enabled:
        if params.ke0 <= 0.0:
            # Direct link: Ce(t) = C(t)
            ce_list = list(c_list)
        else:
            # Convolution / RK4 integration of dCe/dt = ke0 * (C(t) - Ce(t))
            ce_val = 0.0
            ce_list.append(ce_val)
            for i in range(1, len(times)):
                dt = times[i] - times[i - 1]
                # Midpoint RK2 for Ce
                c_prev = c_list[i - 1]
                c_curr = c_list[i]
                c_mid = 0.5 * (c_prev + c_curr)
                k1 = params.ke0 * (c_prev - ce_val)
                ce_mid = ce_val + 0.5 * dt * k1
                k2 = params.ke0 * (c_mid - ce_mid)
                ce_val = max(0.0, ce_val + dt * k2)
                ce_list.append(ce_val)

        # Sigmoid Emax: E = E0 + (Emax * Ce^n) / (EC50^n + Ce^n)
        for ce in ce_list:
            if ce <= 0.0:
                e_list.append(params.e0)
            else:
                ce_pow = ce ** params.hill_n
                ec50_pow = params.ec50 ** params.hill_n
                eff = params.e0 + (params.emax * ce_pow) / (ec50_pow + ce_pow)
                e_list.append(float(eff))
    else:
        ce_list = [0.0] * len(times)
        e_list = [0.0] * len(times)

    # Derived Metrics
    cmax = float(max(c_list))
    idx_max = int(np.argmax(c_list))
    tmax = float(times[idx_max])

    # Trapezoid AUC over simulated window
    auc_trap = float(np.trapezoid(c_list, times) if hasattr(np, "trapezoid") else np.trapz(c_list, times))

    # Analytic AUC for total dose administered (single dose or n doses)
    f_total = params.f_bioav if params.route == RouteType.oral else 1.0
    total_dose = params.dose_mg * params.n_doses
    auc_analytic = float((total_dose * f_total) / params.cl)

    # Add terminal tail to trapezoidal AUC: Clast / lambda_z
    if params.model_type == ModelType.two_compartment and biexp is not None:
        lambda_z = biexp.beta
        v_ss = params.v1 + params.v2
    else:
        lambda_z = params.cl / params.v1
        v_ss = params.v1

    terminal_half_life = float(math.log(2.0) / lambda_z)
    auc_trap_inf = auc_trap + (c_list[-1] / lambda_z if c_list[-1] > 0 else 0.0)

    # Accumulation ratio R = 1 / (1 - exp(-lambda_z * tau))
    tau = params.interval_h
    accum_ratio = float(1.0 / (1.0 - math.exp(-lambda_z * tau))) if (params.n_doses > 1 and tau > 0) else 1.0
    time_to_ss = float(4.32 * terminal_half_life)  # ~95% of steady state

    # Time in / above / below target window
    t_in = 0.0
    t_above = 0.0
    t_below = 0.0
    t_effect = 0.0
    eff_threshold = params.e0 + 0.5 * params.emax

    for i in range(len(times) - 1):
        dt = times[i + 1] - times[i]
        c_mid = 0.5 * (c_list[i] + c_list[i + 1])
        if c_mid < params.target_window_low:
            t_below += dt
        elif c_mid > params.target_window_high:
            t_above += dt
        else:
            t_in += dt

        if params.pd_enabled:
            e_mid = 0.5 * (e_list[i] + e_list[i + 1])
            if e_mid >= eff_threshold:
                t_effect += dt

    return PKPDResult(
        times=times,
        concentrations=c_list,
        effect=e_list,
        ce=ce_list,
        cmax=cmax,
        tmax=tmax,
        auc_analytic=round(auc_analytic, 4),
        auc_trapezoid=round(auc_trap_inf, 4),
        terminal_half_life_h=round(terminal_half_life, 4),
        clearance_l_h=round(params.cl, 4),
        steady_state_volume_l=round(v_ss, 4),
        accumulation_ratio=round(accum_ratio, 4),
        time_to_steady_state_h=round(time_to_ss, 2),
        time_in_target_h=round(t_in, 2),
        time_above_target_h=round(t_above, 2),
        time_below_target_h=round(t_below, 2),
        time_in_effect_h=round(t_effect, 2),
        total_duration_h=t_end_h,
        params=params,
    )


def rk4_pkpd_cross_check(params: PKPDParams, t_end_h: float, dt_h: float = 0.01) -> tuple[list[float], list[float]]:
    """
    Numerical cross-check implementation using 4th-order Runge-Kutta.
    State vector:
    1-comp oral: [A_gut, A_central]
    2-comp oral: [A_gut, A_central, A_periph]
    IV bolus: starts with A_central = Dose
    IV infusion: input rate R0 for t <= t_inf
    Returns (times, concentrations).
    """
    params.validate()
    k10 = params.cl / params.v1
    k12 = params.q / params.v1 if params.model_type == ModelType.two_compartment else 0.0
    k21 = params.q / params.v2 if params.model_type == ModelType.two_compartment else 0.0
    ka = params.ka if params.route == RouteType.oral else 0.0
    f = params.f_bioav if params.route == RouteType.oral else 1.0

    # Initialize state at t=0
    # y = [A_gut, A_central, A_periph]
    y = [0.0, 0.0, 0.0]
    if params.route == RouteType.iv_bolus:
        y[1] = params.dose_mg
    elif params.route == RouteType.oral:
        if params.t_lag <= 0.0:
            y[0] = params.dose_mg * f

    def derivatives(t: float, state: list[float]) -> list[float]:
        ag, ac, ap = state
        # Infusion rate input
        r_in = 0.0
        if params.route == RouteType.iv_infusion:
            if 0.0 <= t <= params.infusion_duration_h:
                r_in = params.dose_mg / params.infusion_duration_h

        # Oral absorption input
        d_ag = 0.0
        r_abs = 0.0
        if params.route == RouteType.oral:
            if t >= params.t_lag:
                r_abs = ka * ag
                d_ag = -r_abs

        d_ac = r_in + r_abs - k10 * ac - k12 * ac + k21 * ap
        d_ap = k12 * ac - k21 * ap
        return [d_ag, d_ac, d_ap]

    n_steps = int(math.ceil(t_end_h / dt_h))
    times = [0.0]
    concs = [y[1] / params.v1]

    curr_t = 0.0
    for _ in range(n_steps):
        # Handle lag-time oral dose insertion
        if params.route == RouteType.oral and params.t_lag > 0.0:
            if curr_t < params.t_lag and (curr_t + dt_h) >= params.t_lag:
                y[0] += params.dose_mg * f

        # RK4 step
        k1 = derivatives(curr_t, y)
        y_k1 = [y[j] + 0.5 * dt_h * k1[j] for j in range(3)]

        k2 = derivatives(curr_t + 0.5 * dt_h, y_k1)
        y_k2 = [y[j] + 0.5 * dt_h * k2[j] for j in range(3)]

        k3 = derivatives(curr_t + 0.5 * dt_h, y_k2)
        y_k3 = [y[j] + dt_h * k3[j] for j in range(3)]

        k4 = derivatives(curr_t + dt_h, y_k3)

        for j in range(3):
            y[j] += (dt_h / 6.0) * (k1[j] + 2.0 * k2[j] + 2.0 * k3[j] + k4[j])

        curr_t += dt_h
        times.append(round(curr_t, 5))
        concs.append(max(0.0, y[1] / params.v1))

    return times, concs
