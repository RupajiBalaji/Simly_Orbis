"""
backend/tests/test_chem_kinetics.py
Unit tests for Chemical Reaction Kinetics Engine (chem.kinetics).

Standard: Section 18 (P3-T1) of Simly Orbis MVP Build Specification.
Criteria:
- At least 40 analytic tests with hand-computed values documented in comments.
- Mass-balance verification.
- Limiting-case tests (t->0, t->inf, k->0, k1==k2).
- RK4 numerical cross-checks.
"""

import math
import pytest

from app.chem.kinetics import (
    R_GAS_CONSTANT,
    arrhenius_k,
    arrhenius_two_temperature,
    celsius_to_kelvin,
    concentration_order_0,
    concentration_order_1,
    concentration_order_2,
    consecutive_kinetics,
    consecutive_peak_b,
    fit_best_order,
    generate_kinetics_observations,
    half_life_order_0,
    half_life_order_1,
    half_life_order_2,
    linear_regression,
    rk4_integrate,
)


# ===========================================================================
# 1. Zero-Order Kinetics Tests (Analytic & Hand-Computed)
# ===========================================================================

def test_order_0_hand_computed_step_1():
    # [A]_0 = 1.0 M, k = 0.05 M/s, t = 10.0 s
    # Hand calculation: [A] = 1.0 - (0.05 * 10.0) = 1.0 - 0.5 = 0.50 M
    val = concentration_order_0(a0=1.0, k=0.05, t=10.0)
    assert abs(val - 0.50) < 1e-9


def test_order_0_hand_computed_step_2():
    # [A]_0 = 2.5 M, k = 0.2 M/s, t = 4.0 s
    # Hand calculation: [A] = 2.5 - (0.2 * 4.0) = 2.5 - 0.8 = 1.70 M
    val = concentration_order_0(a0=2.5, k=0.2, t=4.0)
    assert abs(val - 1.70) < 1e-9


def test_order_0_zero_clipping():
    # [A]_0 = 1.0 M, k = 0.2 M/s, t = 10.0 s
    # Hand calculation: 1.0 - 2.0 = -1.0 => clipped to 0.0 M
    val = concentration_order_0(a0=1.0, k=0.2, t=10.0)
    assert val == 0.0


def test_order_0_exact_exhaustion_time():
    # [A]_0 = 0.8 M, k = 0.08 M/s, t = 10.0 s
    # Hand calculation: 0.8 - (0.08 * 10.0) = 0.0 M
    val = concentration_order_0(a0=0.8, k=0.08, t=10.0)
    assert abs(val - 0.0) < 1e-9


def test_order_0_half_life_hand_computed_1():
    # [A]_0 = 1.0 M, k = 0.05 M/s
    # Hand calculation: t_1/2 = [A]_0 / (2 * k) = 1.0 / (2 * 0.05) = 10.0 s
    t_half = half_life_order_0(a0=1.0, k=0.05)
    assert abs(t_half - 10.0) < 1e-9


def test_order_0_half_life_hand_computed_2():
    # [A]_0 = 3.6 M, k = 0.12 M/s
    # Hand calculation: t_1/2 = 3.6 / (2 * 0.12) = 3.6 / 0.24 = 15.0 s
    t_half = half_life_order_0(a0=3.6, k=0.12)
    assert abs(t_half - 15.0) < 1e-9


def test_order_0_limiting_case_t_zero():
    # At t = 0, [A] must equal [A]_0
    assert concentration_order_0(a0=2.718, k=0.5, t=0.0) == 2.718


def test_order_0_limiting_case_k_zero():
    # When k = 0, reaction does not proceed: [A](t) = [A]_0
    assert concentration_order_0(a0=1.5, k=0.0, t=100.0) == 1.5


# ===========================================================================
# 2. First-Order Kinetics Tests (Analytic & Hand-Computed)
# ===========================================================================

def test_order_1_hand_computed_step_1():
    # [A]_0 = 1.0 M, k = 0.1 s^-1, t = 10.0 s
    # Hand calculation: [A] = 1.0 * exp(-0.1 * 10) = 1.0 * exp(-1.0) = 0.36787944117 M
    val = concentration_order_1(a0=1.0, k=0.1, t=10.0)
    expected = math.exp(-1.0)
    assert abs(val - expected) < 1e-9


def test_order_1_hand_computed_step_2():
    # [A]_0 = 5.0 M, k = 0.69314718056 s^-1 (ln 2), t = 2.0 s (2 half-lives)
    # Hand calculation: [A] = 5.0 / (2^2) = 1.25 M
    k = math.log(2.0)
    val = concentration_order_1(a0=5.0, k=k, t=2.0)
    assert abs(val - 1.25) < 1e-9


def test_order_1_half_life_hand_computed_1():
    # k = 0.05 s^-1
    # Hand calculation: t_1/2 = ln(2) / 0.05 = 0.69314718 / 0.05 = 13.86294361 s
    expected = math.log(2.0) / 0.05
    assert abs(half_life_order_1(k=0.05) - expected) < 1e-9


def test_order_1_half_life_hand_computed_2():
    # k = 0.1 s^-1
    # Hand calculation: t_1/2 = 6.9314718056 s
    expected = math.log(2.0) / 0.1
    assert abs(half_life_order_1(k=0.1) - expected) < 1e-9


def test_order_1_at_half_life_concentration():
    # At t = t_1/2, [A] must equal exactly [A]_0 / 2
    a0 = 4.2
    k = 0.035
    t_half = half_life_order_1(k)
    val = concentration_order_1(a0=a0, k=k, t=t_half)
    assert abs(val - (a0 / 2.0)) < 1e-9


def test_order_1_limiting_case_t_zero():
    # At t = 0, [A](0) = [A]_0
    assert concentration_order_1(a0=3.1415, k=0.8, t=0.0) == 3.1415


def test_order_1_limiting_case_t_inf():
    # At large t, [A] -> 0
    val = concentration_order_1(a0=10.0, k=0.5, t=100.0)
    assert val < 1e-15


def test_order_1_limiting_case_k_zero():
    # When k = 0, no reaction: [A](t) = [A]_0
    assert concentration_order_1(a0=2.0, k=0.0, t=50.0) == 2.0


# ===========================================================================
# 3. Second-Order Kinetics Tests (Analytic & Hand-Computed)
# ===========================================================================

def test_order_2_hand_computed_step_1():
    # [A]_0 = 1.0 M, k = 0.5 M^-1 s^-1, t = 2.0 s
    # Hand calculation: 1/[A] = 1/1.0 + (0.5 * 2.0) = 1.0 + 1.0 = 2.0
    # => [A] = 1/2.0 = 0.50 M
    val = concentration_order_2(a0=1.0, k=0.5, t=2.0)
    assert abs(val - 0.50) < 1e-9


def test_order_2_hand_computed_step_2():
    # [A]_0 = 2.0 M, k = 0.25 M^-1 s^-1, t = 6.0 s
    # Hand calculation: 1/[A] = 1/2.0 + (0.25 * 6.0) = 0.5 + 1.5 = 2.0
    # => [A] = 0.50 M
    val = concentration_order_2(a0=2.0, k=0.25, t=6.0)
    assert abs(val - 0.50) < 1e-9


def test_order_2_half_life_hand_computed_1():
    # [A]_0 = 1.0 M, k = 0.5 M^-1 s^-1
    # Hand calculation: t_1/2 = 1 / (k * [A]_0) = 1 / (0.5 * 1.0) = 2.0 s
    assert abs(half_life_order_2(a0=1.0, k=0.5) - 2.0) < 1e-9


def test_order_2_half_life_hand_computed_2():
    # [A]_0 = 0.4 M, k = 0.1 M^-1 s^-1
    # Hand calculation: t_1/2 = 1 / (0.1 * 0.4) = 1 / 0.04 = 25.0 s
    assert abs(half_life_order_2(a0=0.4, k=0.1) - 25.0) < 1e-9


def test_order_2_at_half_life_concentration():
    # At t = t_1/2, [A] = [A]_0 / 2
    a0 = 1.8
    k = 0.3
    t_half = half_life_order_2(a0=a0, k=k)
    val = concentration_order_2(a0=a0, k=k, t=t_half)
    assert abs(val - (a0 / 2.0)) < 1e-9


def test_order_2_limiting_case_t_zero():
    # At t = 0, [A](0) = [A]_0
    assert concentration_order_2(a0=4.5, k=0.7, t=0.0) == 4.5


def test_order_2_limiting_case_k_zero():
    # When k = 0, [A](t) = [A]_0
    assert concentration_order_2(a0=3.2, k=0.0, t=40.0) == 3.2


# ===========================================================================
# 4. Arrhenius Equation Tests (Analytic & Hand-Computed)
# ===========================================================================

def test_arrhenius_hand_computed_step_1():
    # A = 1.0e11 s^-1, Ea = 60,000 J/mol (60 kJ/mol), T = 300.0 K
    # Exponent: -60000 / (8.314462618 * 300) = -60000 / 2494.3387854 = -24.05447137
    # exp(-24.05447137) = 3.5750275e-11
    # k = 1.0e11 * 3.5750275e-11 = 3.5750275 s^-1
    k = arrhenius_k(a_pre_exponential=1.0e11, ea_joules=60000.0, t_kelvin=300.0)
    expected = 1.0e11 * math.exp(-60000.0 / (R_GAS_CONSTANT * 300.0))
    assert abs(k - expected) < 1e-6
    assert abs(k - 3.5750275) < 1e-4


def test_arrhenius_zero_activation_energy():
    # When Ea = 0, k(T) = A for all temperatures
    k = arrhenius_k(a_pre_exponential=42.0, ea_joules=0.0, t_kelvin=350.0)
    assert abs(k - 42.0) < 1e-9


def test_arrhenius_temperature_increase_increases_k():
    # Rate constant must monotonically increase with temperature
    k_low = arrhenius_k(a_pre_exponential=1e10, ea_joules=50000.0, t_kelvin=298.15)
    k_high = arrhenius_k(a_pre_exponential=1e10, ea_joules=50000.0, t_kelvin=323.15)
    assert k_high > k_low


def test_arrhenius_two_temperature_hand_computed():
    # k1 = 0.01 s^-1 at T1 = 300 K. Ea = 50,000 J/mol. T2 = 350 K.
    # Factor: (50000 / 8.314462618) * (1/300 - 1/350)
    # (1/300 - 1/350) = 0.003333333 - 0.002857143 = 0.0004761905
    # Factor = 6013.6186 * 0.0004761905 = 2.8636279
    # k2 = 0.01 * exp(2.8636279) = 0.01 * 17.52504 = 0.1752504 s^-1
    k2 = arrhenius_two_temperature(k1=0.01, t1_kelvin=300.0, t2_kelvin=350.0, ea_joules=50000.0)
    expected = 0.01 * math.exp((50000.0 / R_GAS_CONSTANT) * (1.0 / 300.0 - 1.0 / 350.0))
    assert abs(k2 - expected) < 1e-9
    assert abs(k2 - 0.1752504) < 1e-4


def test_celsius_to_kelvin_conversion():
    # 25.0 °C = 298.15 K; 0.0 °C = 273.15 K
    assert abs(celsius_to_kelvin(25.0) - 298.15) < 1e-9
    assert abs(celsius_to_kelvin(0.0) - 273.15) < 1e-9


# ===========================================================================
# 5. Consecutive First-Order Reactions: A -> B -> C
# ===========================================================================

def test_consecutive_mass_balance_non_equal_k():
    # Mass balance: [A] + [B] + [C] must equal [A]_0 at all times
    a0 = 2.0
    k1 = 0.2
    k2 = 0.05
    for t in [0.0, 1.0, 5.0, 10.0, 25.0, 50.0, 100.0]:
        pt = consecutive_kinetics(a0=a0, k1=k1, k2=k2, t=t)
        assert pt.mass_balance_error < 1e-12
        assert abs((pt.a + pt.b + pt.c) - a0) < 1e-12


def test_consecutive_mass_balance_equal_k():
    # Degenerate case k1 == k2: mass balance must still hold exactly
    a0 = 1.5
    k = 0.15
    for t in [0.0, 0.5, 2.0, 10.0, 30.0, 100.0]:
        pt = consecutive_kinetics(a0=a0, k1=k, k2=k, t=t)
        assert pt.mass_balance_error < 1e-12
        assert abs((pt.a + pt.b + pt.c) - a0) < 1e-12


def test_consecutive_hand_computed_non_equal():
    # a0 = 1.0 M, k1 = 0.4 s^-1, k2 = 0.1 s^-1, t = 2.0 s
    # [A] = 1.0 * exp(-0.4 * 2) = exp(-0.8) = 0.44932896
    # [B] = 1.0 * (0.4 / (0.1 - 0.4)) * (exp(-0.8) - exp(-0.2))
    #     = (-0.4 / 0.3) * (0.44932896 - 0.81873075) = (-1.333333) * (-0.36940179) = 0.4925357
    # [C] = 1.0 - (0.44932896 + 0.4925357) = 0.0581353
    pt = consecutive_kinetics(a0=1.0, k1=0.4, k2=0.1, t=2.0)
    assert abs(pt.a - 0.44932896) < 1e-5
    assert abs(pt.b - 0.4925357) < 1e-5
    assert abs(pt.c - 0.0581353) < 1e-5


def test_consecutive_peak_intermediate_b_non_equal():
    # a0 = 1.0 M, k1 = 0.4 s^-1, k2 = 0.1 s^-1
    # Hand calculation: t_max = ln(0.4 / 0.1) / (0.4 - 0.1) = ln(4) / 0.3 = 1.38629436 / 0.3 = 4.6209812 s
    # B_max = 1.0 * (0.4 / 0.1)^(0.1 / (0.1 - 0.4)) = 4^(-0.1 / 0.3) = 4^(-1/3) = 0.6299605 M
    t_max, b_max = consecutive_peak_b(a0=1.0, k1=0.4, k2=0.1)
    assert abs(t_max - 4.6209812) < 1e-5
    assert abs(b_max - 0.6299605) < 1e-5

    # Verify that evaluating consecutive_kinetics at t_max gives b_max
    pt_max = consecutive_kinetics(a0=1.0, k1=0.4, k2=0.1, t=t_max)
    assert abs(pt_max.b - b_max) < 1e-6


def test_consecutive_peak_intermediate_b_equal_k():
    # a0 = 2.0 M, k1 = k2 = 0.2 s^-1
    # Hand calculation: t_max = 1 / k = 1 / 0.2 = 5.0 s
    # B_max = a0 / e = 2.0 / 2.7182818 = 0.73575888 M
    t_max, b_max = consecutive_peak_b(a0=2.0, k1=0.2, k2=0.2)
    assert abs(t_max - 5.0) < 1e-9
    assert abs(b_max - (2.0 / math.e)) < 1e-6

    pt_max = consecutive_kinetics(a0=2.0, k1=0.2, k2=0.2, t=t_max)
    assert abs(pt_max.b - b_max) < 1e-6


def test_consecutive_limiting_case_t_zero():
    # At t = 0: [A] = a0, [B] = 0, [C] = 0
    pt = consecutive_kinetics(a0=3.0, k1=0.5, k2=0.2, t=0.0)
    assert pt.a == 3.0
    assert pt.b == 0.0
    assert pt.c == 0.0


def test_consecutive_limiting_case_t_inf():
    # At t -> inf: [A] -> 0, [B] -> 0, [C] -> a0
    pt = consecutive_kinetics(a0=3.0, k1=0.5, k2=0.2, t=200.0)
    assert pt.a < 1e-12
    assert pt.b < 1e-12
    assert abs(pt.c - 3.0) < 1e-12


# ===========================================================================
# 6. RK4 Numerical Cross-Check Tests
# ===========================================================================

def test_rk4_cross_check_order_0():
    # ODE: d[A]/dt = -k
    a0 = 1.0
    k = 0.04
    t_eval = [0.0, 5.0, 10.0, 15.0, 20.0]

    def derivs_order_0(t: float, y: list[float]) -> list[float]:
        return [-k if y[0] > 0.0 else 0.0]

    rk4_res = rk4_integrate(derivs_order_0, [a0], t_eval, dt_max=0.05)

    for i, t in enumerate(t_eval):
        analytic = concentration_order_0(a0, k, t)
        numerical = rk4_res[i][0]
        assert abs(numerical - analytic) < 1e-5


def test_rk4_cross_check_order_1():
    # ODE: d[A]/dt = -k * [A]
    a0 = 2.0
    k = 0.1
    t_eval = [0.0, 2.0, 5.0, 10.0, 20.0]

    def derivs_order_1(t: float, y: list[float]) -> list[float]:
        return [-k * y[0]]

    rk4_res = rk4_integrate(derivs_order_1, [a0], t_eval, dt_max=0.02)

    for i, t in enumerate(t_eval):
        analytic = concentration_order_1(a0, k, t)
        numerical = rk4_res[i][0]
        # RK4 agreement within 1e-5 relative error
        rel_err = abs(numerical - analytic) / max(analytic, 1e-6)
        assert rel_err < 1e-4


def test_rk4_cross_check_order_2():
    # ODE: d[A]/dt = -k * [A]^2
    a0 = 1.5
    k = 0.2
    t_eval = [0.0, 1.0, 3.0, 8.0, 15.0]

    def derivs_order_2(t: float, y: list[float]) -> list[float]:
        return [-k * (y[0] ** 2)]

    rk4_res = rk4_integrate(derivs_order_2, [a0], t_eval, dt_max=0.02)

    for i, t in enumerate(t_eval):
        analytic = concentration_order_2(a0, k, t)
        numerical = rk4_res[i][0]
        rel_err = abs(numerical - analytic) / max(analytic, 1e-6)
        assert rel_err < 1e-4


def test_rk4_cross_check_consecutive():
    # ODEs for A -> B -> C:
    # d[A]/dt = -k1 * [A]
    # d[B]/dt = k1 * [A] - k2 * [B]
    # d[C]/dt = k2 * [B]
    a0 = 1.0
    k1 = 0.3
    k2 = 0.08
    t_eval = [0.0, 1.0, 3.0, 7.0, 15.0, 30.0]

    def derivs_consecutive(t: float, y: list[float]) -> list[float]:
        da = -k1 * y[0]
        db = k1 * y[0] - k2 * y[1]
        dc = k2 * y[1]
        return [da, db, dc]

    rk4_res = rk4_integrate(derivs_consecutive, [a0, 0.0, 0.0], t_eval, dt_max=0.02)

    for i, t in enumerate(t_eval):
        pt = consecutive_kinetics(a0, k1, k2, t)
        num_a, num_b, num_c = rk4_res[i]
        assert abs(num_a - pt.a) < 1e-4
        assert abs(num_b - pt.b) < 1e-4
        assert abs(num_c - pt.c) < 1e-4


# ===========================================================================
# 7. Linear Regression & Order Identification Tests
# ===========================================================================

def test_linear_regression_perfect_line():
    # y = 2x + 3
    x = [0.0, 1.0, 2.0, 3.0, 4.0]
    y = [3.0, 5.0, 7.0, 9.0, 11.0]
    slope, intercept, r2 = linear_regression(x, y)
    assert abs(slope - 2.0) < 1e-9
    assert abs(intercept - 3.0) < 1e-9
    assert abs(r2 - 1.0) < 1e-9


def test_fit_best_order_identifies_order_0():
    # True order 0: [A] = 1.0 - 0.05 * t
    times = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0]
    obs = generate_kinetics_observations(order=0, k=0.05, a0=1.0, time_points=times, noise_sd=0.0)
    best_fit = fit_best_order(obs)
    assert best_fit.order_candidate == 0
    assert abs(best_fit.r_squared - 1.0) < 1e-6
    assert abs(best_fit.slope - (-0.05)) < 1e-6


def test_fit_best_order_identifies_order_1():
    # True order 1: [A] = 1.0 * exp(-0.08 * t)
    times = [0.0, 2.0, 5.0, 10.0, 15.0, 20.0]
    obs = generate_kinetics_observations(order=1, k=0.08, a0=1.0, time_points=times, noise_sd=0.0)
    best_fit = fit_best_order(obs)
    assert best_fit.order_candidate == 1
    assert abs(best_fit.r_squared - 1.0) < 1e-6
    assert abs(best_fit.slope - (-0.08)) < 1e-6


def test_fit_best_order_identifies_order_2():
    # True order 2: 1/[A] = 1/1.0 + 0.1 * t
    times = [0.0, 2.0, 5.0, 10.0, 15.0, 20.0]
    obs = generate_kinetics_observations(order=2, k=0.1, a0=1.0, time_points=times, noise_sd=0.0)
    best_fit = fit_best_order(obs)
    assert best_fit.order_candidate == 2
    assert abs(best_fit.r_squared - 1.0) < 1e-6
    assert abs(best_fit.slope - 0.1) < 1e-6


def test_noisy_observations_seed_reproducibility():
    times = [0.0, 5.0, 10.0, 20.0]
    obs1 = generate_kinetics_observations(order=1, k=0.05, a0=1.0, time_points=times, noise_sd=0.02, seed=42)
    obs2 = generate_kinetics_observations(order=1, k=0.05, a0=1.0, time_points=times, noise_sd=0.02, seed=42)
    for o1, o2 in zip(obs1, obs2):
        assert o1.a_measured == o2.a_measured


# ===========================================================================
# 8. Boundary Conditions & Error Handling Tests
# ===========================================================================

def test_negative_parameters_raise_value_errors():
    with pytest.raises(ValueError):
        concentration_order_0(a0=-1.0, k=0.1, t=1.0)
    with pytest.raises(ValueError):
        concentration_order_1(a0=1.0, k=-0.1, t=1.0)
    with pytest.raises(ValueError):
        concentration_order_2(a0=1.0, k=0.1, t=-1.0)
    with pytest.raises(ValueError):
        half_life_order_0(a0=0.0, k=0.1)
    with pytest.raises(ValueError):
        half_life_order_1(k=-0.05)
    with pytest.raises(ValueError):
        half_life_order_2(a0=1.0, k=0.0)
    with pytest.raises(ValueError):
        arrhenius_k(a_pre_exponential=0.0, ea_joules=1000.0, t_kelvin=300.0)
    with pytest.raises(ValueError):
        arrhenius_k(a_pre_exponential=1.0, ea_joules=-50.0, t_kelvin=300.0)
    with pytest.raises(ValueError):
        arrhenius_k(a_pre_exponential=1.0, ea_joules=1000.0, t_kelvin=-10.0)
    with pytest.raises(ValueError):
        celsius_to_kelvin(-300.0)
