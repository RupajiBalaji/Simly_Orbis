"""
backend/app/chem/kinetics.py
Chemical Reaction Kinetics Engine.

Implements Section 9.2 & Section 18 (P3-T1) of Simly Orbis MVP Build Specification:
- Integrated rate laws for orders 0, 1, 2
- Half-life formulas
- Arrhenius temperature dependence k(T) and two-temperature form
- Consecutive first-order reactions A -> B -> C with non-equal and degenerate equal rate constants
- Classical 4th-order Runge-Kutta (RK4) numerical cross-check
- Linearised transformations (c, ln c, 1/c vs time) and seeded measurement noise generation

Governance:
- Pure simulation logic; engine decides, client renders.
- Educational simulation; no medical advice.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

# Universal gas constant in J / (mol * K)
R_GAS_CONSTANT: float = 8.314462618


@dataclass(frozen=True)
class ConsecutiveKineticsPoint:
    time: float
    a: float
    b: float
    c: float
    mass_balance_error: float


@dataclass(frozen=True)
class KineticsObservation:
    time: float
    a_true: float
    a_measured: float
    ln_a_measured: Optional[float]
    inv_a_measured: Optional[float]


@dataclass(frozen=True)
class LinearFitResult:
    slope: float
    intercept: float
    r_squared: float
    order_candidate: int


# ---------------------------------------------------------------------------
# Integrated Rate Laws & Half-Life
# ---------------------------------------------------------------------------

def concentration_order_0(a0: float, k: float, t: float) -> float:
    """
    0th order rate law: d[A]/dt = -k
    Integrated law: [A](t) = [A]_0 - k * t (clipped at 0.0)
    """
    if a0 < 0.0 or k < 0.0 or t < 0.0:
        raise ValueError("Concentration, rate constant, and time must be non-negative.")
    val = a0 - k * t
    return max(0.0, val)


def half_life_order_0(a0: float, k: float) -> float:
    """Half-life for 0th order: t_1/2 = [A]_0 / (2k)"""
    if a0 <= 0.0 or k <= 0.0:
        raise ValueError("Initial concentration and rate constant must be strictly positive.")
    return a0 / (2.0 * k)


def concentration_order_1(a0: float, k: float, t: float) -> float:
    """
    1st order rate law: d[A]/dt = -k * [A]
    Integrated law: [A](t) = [A]_0 * exp(-k * t)
    """
    if a0 < 0.0 or k < 0.0 or t < 0.0:
        raise ValueError("Concentration, rate constant, and time must be non-negative.")
    if a0 == 0.0:
        return 0.0
    return a0 * math.exp(-k * t)


def half_life_order_1(k: float) -> float:
    """Half-life for 1st order: t_1/2 = ln(2) / k"""
    if k <= 0.0:
        raise ValueError("Rate constant must be strictly positive.")
    return math.log(2.0) / k


def concentration_order_2(a0: float, k: float, t: float) -> float:
    """
    2nd order rate law (single reactant A -> products, rate = k * [A]^2):
    Integrated law: 1/[A](t) = 1/[A]_0 + k * t
    => [A](t) = [A]_0 / (1 + k * [A]_0 * t)
    """
    if a0 < 0.0 or k < 0.0 or t < 0.0:
        raise ValueError("Concentration, rate constant, and time must be non-negative.")
    if a0 == 0.0:
        return 0.0
    return a0 / (1.0 + k * a0 * t)


def half_life_order_2(a0: float, k: float) -> float:
    """Half-life for 2nd order: t_1/2 = 1 / (k * [A]_0)"""
    if a0 <= 0.0 or k <= 0.0:
        raise ValueError("Initial concentration and rate constant must be strictly positive.")
    return 1.0 / (k * a0)


# ---------------------------------------------------------------------------
# Arrhenius Temperature Dependence
# ---------------------------------------------------------------------------

def arrhenius_k(a_pre_exponential: float, ea_joules: float, t_kelvin: float) -> float:
    """
    Arrhenius equation: k(T) = A * exp(-Ea / (R * T))
    Args:
        a_pre_exponential: frequency factor A (same units as k)
        ea_joules: activation energy in J/mol
        t_kelvin: temperature in Kelvin (> 0)
    """
    if a_pre_exponential <= 0.0:
        raise ValueError("Pre-exponential factor must be strictly positive.")
    if ea_joules < 0.0:
        raise ValueError("Activation energy must be non-negative.")
    if t_kelvin <= 0.0:
        raise ValueError("Temperature in Kelvin must be strictly positive.")
    exponent = -ea_joules / (R_GAS_CONSTANT * t_kelvin)
    return a_pre_exponential * math.exp(exponent)


def arrhenius_two_temperature(
    k1: float, t1_kelvin: float, t2_kelvin: float, ea_joules: float
) -> float:
    """
    Two-temperature form of Arrhenius equation:
    ln(k2 / k1) = (Ea / R) * (1/T1 - 1/T2)
    k2 = k1 * exp((Ea / R) * (1/T1 - 1/T2))
    """
    if k1 <= 0.0:
        raise ValueError("Reference rate constant k1 must be strictly positive.")
    if t1_kelvin <= 0.0 or t2_kelvin <= 0.0:
        raise ValueError("Temperatures in Kelvin must be strictly positive.")
    if ea_joules < 0.0:
        raise ValueError("Activation energy must be non-negative.")
    factor = (ea_joules / R_GAS_CONSTANT) * (1.0 / t1_kelvin - 1.0 / t2_kelvin)
    return k1 * math.exp(factor)


def celsius_to_kelvin(t_celsius: float) -> float:
    """Convert Celsius to Kelvin."""
    k = t_celsius + 273.15
    if k <= 0.0:
        raise ValueError(f"Temperature {t_celsius}°C is below absolute zero.")
    return k


# ---------------------------------------------------------------------------
# Consecutive First-Order Reactions: A -> B -> C
# ---------------------------------------------------------------------------

def consecutive_kinetics(
    a0: float, k1: float, k2: float, t: float
) -> ConsecutiveKineticsPoint:
    """
    Exact analytic solution for consecutive first-order reactions:
      A --k1--> B --k2--> C
    with initial conditions [A](0) = a0, [B](0) = 0, [C](0) = 0.
    
    Equations:
      [A](t) = [A]_0 * exp(-k1 * t)
      If k1 != k2:
        [B](t) = [A]_0 * [k1 / (k2 - k1)] * (exp(-k1 * t) - exp(-k2 * t))
        [C](t) = [A]_0 * [ 1 + (k1 * exp(-k2 * t) - k2 * exp(-k1 * t)) / (k2 - k1) ]
      If k1 == k2 = k:
        [B](t) = [A]_0 * k * t * exp(-k * t)
        [C](t) = [A]_0 * [ 1 - exp(-k * t) * (1 + k * t) ]
    """
    if a0 < 0.0 or k1 < 0.0 or k2 < 0.0 or t < 0.0:
        raise ValueError("Parameters must be non-negative.")
    if a0 == 0.0:
        return ConsecutiveKineticsPoint(time=t, a=0.0, b=0.0, c=0.0, mass_balance_error=0.0)

    # [A](t)
    a = a0 * math.exp(-k1 * t)

    diff = k2 - k1
    eps = 1e-12

    if abs(diff) > eps:
        b = a0 * (k1 / diff) * (math.exp(-k1 * t) - math.exp(-k2 * t))
        c = a0 * (1.0 + (k1 * math.exp(-k2 * t) - k2 * math.exp(-k1 * t)) / diff)
    else:
        # Equal rate constants: k1 == k2
        k = k1
        b = a0 * k * t * math.exp(-k * t)
        c = a0 * (1.0 - math.exp(-k * t) * (1.0 + k * t))

    # Protect against tiny negative floats due to floating point rounding
    a = max(0.0, a)
    b = max(0.0, b)
    c = max(0.0, c)
    mass_err = abs((a + b + c) - a0)

    return ConsecutiveKineticsPoint(time=t, a=a, b=b, c=c, mass_balance_error=mass_err)


def consecutive_peak_b(a0: float, k1: float, k2: float) -> Tuple[float, float]:
    """
    Analytic peak time t_max and peak concentration [B]_max for intermediate B.
    t_max = ln(k1 / k2) / (k1 - k2) if k1 != k2
    t_max = 1 / k if k1 == k2 = k
    """
    if a0 <= 0.0 or k1 <= 0.0 or k2 <= 0.0:
        raise ValueError("Parameters must be strictly positive for intermediate peak.")

    diff = k1 - k2
    eps = 1e-12
    if abs(diff) > eps:
        t_max = math.log(k1 / k2) / diff
        b_max = a0 * ((k1 / k2) ** (k2 / (k2 - k1)))
    else:
        k = k1
        t_max = 1.0 / k
        b_max = a0 / math.e
    return t_max, b_max


# ---------------------------------------------------------------------------
# Classical 4th-Order Runge-Kutta (RK4) Numerical Cross-Check
# ---------------------------------------------------------------------------

def rk4_step(
    derivs_fn: Callable[[float, List[float]], List[float]],
    t: float,
    y: List[float],
    dt: float,
) -> List[float]:
    """Single step of classical 4th order Runge-Kutta."""
    n = len(y)

    k1 = derivs_fn(t, y)

    y_k2 = [y[i] + 0.5 * dt * k1[i] for i in range(n)]
    k2 = derivs_fn(t + 0.5 * dt, y_k2)

    y_k3 = [y[i] + 0.5 * dt * k2[i] for i in range(n)]
    k3 = derivs_fn(t + 0.5 * dt, y_k3)

    y_k4 = [y[i] + dt * k3[i] for i in range(n)]
    k4 = derivs_fn(t + dt, y_k4)

    return [
        y[i] + (dt / 6.0) * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i])
        for i in range(n)
    ]


def rk4_integrate(
    derivs_fn: Callable[[float, List[float]], List[float]],
    y0: List[float],
    t_eval: List[float],
    dt_max: float = 0.01,
) -> List[List[float]]:
    """
    Integrate system of ODEs from t_eval[0] to t_eval[-1] using adaptive/sub-stepped RK4.
    """
    if not t_eval:
        return []
    if len(t_eval) == 1:
        return [list(y0)]

    results: List[List[float]] = [list(y0)]
    curr_y = list(y0)
    curr_t = t_eval[0]

    for next_t in t_eval[1:]:
        interval = next_t - curr_t
        if interval < 0.0:
            raise ValueError("t_eval must be monotonically non-decreasing.")
        if interval == 0.0:
            results.append(list(curr_y))
            continue

        n_substeps = max(1, math.ceil(interval / dt_max))
        dt = interval / n_substeps

        for _ in range(n_substeps):
            curr_y = rk4_step(derivs_fn, curr_t, curr_y, dt)
            curr_t += dt

        # Snap to exact target time
        curr_t = next_t
        results.append(list(curr_y))

    return results


# ---------------------------------------------------------------------------
# Synthetic Measurement Data & Linearisation
# ---------------------------------------------------------------------------

def generate_kinetics_observations(
    order: int,
    k: float,
    a0: float,
    time_points: List[float],
    noise_sd: float = 0.0,
    seed: Optional[int] = None,
) -> List[KineticsObservation]:
    """
    Generate synthetic concentration measurements with optional seeded Gaussian noise.
    Computes linearised values:
      order 0 candidate: [A]
      order 1 candidate: ln([A])
      order 2 candidate: 1 / [A]
    """
    rng = random.Random(seed) if seed is not None else random.Random()
    obs: List[KineticsObservation] = []

    for t in time_points:
        if order == 0:
            a_true = concentration_order_0(a0, k, t)
        elif order == 1:
            a_true = concentration_order_1(a0, k, t)
        elif order == 2:
            a_true = concentration_order_2(a0, k, t)
        else:
            raise ValueError(f"Unsupported reaction order: {order}. Must be 0, 1, or 2.")

        if noise_sd > 0.0:
            noise = rng.gauss(0.0, noise_sd)
            a_meas = max(1e-6, a_true + noise)
        else:
            a_meas = a_true

        ln_a = math.log(a_meas) if a_meas > 0.0 else None
        inv_a = (1.0 / a_meas) if a_meas > 0.0 else None

        obs.append(
            KineticsObservation(
                time=t,
                a_true=a_true,
                a_measured=a_meas,
                ln_a_measured=ln_a,
                inv_a_measured=inv_a,
            )
        )

    return obs


def linear_regression(x: List[float], y: List[float]) -> Tuple[float, float, float]:
    """
    Ordinary least squares simple linear regression: y = slope * x + intercept.
    Returns (slope, intercept, r_squared).
    """
    n = len(x)
    if n < 2 or len(y) != n:
        raise ValueError("Need at least 2 points for linear regression.")

    sum_x = sum(x)
    sum_y = sum(y)
    sum_xx = sum(xi * xi for xi in x)
    sum_yy = sum(yi * yi for yi in y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))

    denominator = n * sum_xx - sum_x * sum_x
    if abs(denominator) < 1e-15:
        return 0.0, sum_y / n, 0.0

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n

    # Compute R^2
    y_mean = sum_y / n
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))

    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-15 else 1.0
    r_squared = max(0.0, min(1.0, r_squared))

    return slope, intercept, r_squared


def fit_best_order(observations: List[KineticsObservation]) -> LinearFitResult:
    """
    Fit candidate rate models (0th: [A] vs t, 1st: ln[A] vs t, 2nd: 1/[A] vs t)
    and select the model with the highest coefficient of determination R^2.
    """
    valid_obs = [o for o in observations if o.a_measured > 0.0]
    if len(valid_obs) < 2:
        raise ValueError("At least 2 positive concentration observations required for fitting.")

    t_vals = [o.time for o in valid_obs]
    c_vals = [o.a_measured for o in valid_obs]
    ln_c_vals = [o.ln_a_measured for o in valid_obs if o.ln_a_measured is not None]
    inv_c_vals = [o.inv_a_measured for o in valid_obs if o.inv_a_measured is not None]

    # Order 0: [A] vs t -> slope = -k, intercept = [A]_0
    slope_0, intercept_0, r2_0 = linear_regression(t_vals, c_vals)

    # Order 1: ln[A] vs t -> slope = -k, intercept = ln[A]_0
    slope_1, intercept_1, r2_1 = linear_regression(t_vals, ln_c_vals)

    # Order 2: 1/[A] vs t -> slope = +k, intercept = 1/[A]_0
    slope_2, intercept_2, r2_2 = linear_regression(t_vals, inv_c_vals)

    fits = [
        (r2_0, LinearFitResult(slope=slope_0, intercept=intercept_0, r_squared=r2_0, order_candidate=0)),
        (r2_1, LinearFitResult(slope=slope_1, intercept=intercept_1, r_squared=r2_1, order_candidate=1)),
        (r2_2, LinearFitResult(slope=slope_2, intercept=intercept_2, r_squared=r2_2, order_candidate=2)),
    ]
    fits.sort(key=lambda item: item[0], reverse=True)
    return fits[0][1]
