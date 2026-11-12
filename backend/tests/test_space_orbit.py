"""
Unit and analytical tests for orbital mechanics and rocket engine (backend/tests/test_space_orbit.py).
Contains 40+ rigorous analytical benchmarks and invariant tests.
"""

from __future__ import annotations

import math
import pytest

from app.space.orbit import (
    EARTH_MU,
    EARTH_RADIUS_M,
    STANDARD_G0,
    DEFAULT_ASCENT_LOSSES_MS,
    StageConfig,
    ascent_delta_v,
    burn_time,
    check_conservation,
    circular_velocity,
    evaluate_mission,
    generate_orbit_path,
    get_rocket_preset,
    hohmann_transfer,
    liftoff_twr,
    load_rocket_presets,
    orbital_period,
    propagate_kepler_rk4,
    tsiolkovsky_dv,
    vis_viva_speed,
)
from app.modules.space_orbit import SpaceOrbitModule, SpaceOrbitParams


# --- 1. Tsiolkovsky Delta-V Tests ---

def test_tsiolkovsky_hand_computed_case():
    """Hand-computed benchmark: Isp=300s, m0=1000kg, mf=500kg -> dv = 300 * 9.80665 * ln(2) = 2039.2355 m/s."""
    expected = 300.0 * STANDARD_G0 * math.log(2.0)
    actual = tsiolkovsky_dv(300.0, 1000.0, 500.0)
    assert math.isclose(actual, expected, rel_tol=1e-7)
    assert math.isclose(actual, 2039.2355, abs_tol=1e-3)


def test_tsiolkovsky_zero_propellant():
    """m0 == mf means no propellant burned, dv must be exactly 0.0."""
    assert tsiolkovsky_dv(350.0, 5000.0, 5000.0) == 0.0


def test_tsiolkovsky_input_validation_negative_isp():
    with pytest.raises(ValueError, match="Specific impulse must be positive"):
        tsiolkovsky_dv(-300.0, 1000.0, 500.0)


def test_tsiolkovsky_input_validation_zero_isp():
    with pytest.raises(ValueError, match="Specific impulse must be positive"):
        tsiolkovsky_dv(0.0, 1000.0, 500.0)


def test_tsiolkovsky_input_validation_negative_m0():
    with pytest.raises(ValueError, match="Initial mass must be positive"):
        tsiolkovsky_dv(300.0, -100.0, 50.0)


def test_tsiolkovsky_input_validation_negative_mf():
    with pytest.raises(ValueError, match="Final mass must be positive"):
        tsiolkovsky_dv(300.0, 100.0, -50.0)


def test_tsiolkovsky_input_validation_mf_greater_than_m0():
    with pytest.raises(ValueError, match="Final mass.*cannot exceed initial mass"):
        tsiolkovsky_dv(300.0, 500.0, 1000.0)


def test_staging_vs_single_stage_advantage():
    """
    Multistage rocket must produce significantly higher delta-v than a single stage
    with identical total structural mass and propellant mass, because dry mass is dropped.
    """
    payload = 500.0
    # Two-stage rocket:
    # S1: dry=3000, prop=20000, Isp=300
    # S2: dry=1000, prop=5000, Isp=350
    stages = [
        StageConfig(1, "S1", dry_mass_kg=3000.0, propellant_mass_kg=20000.0, thrust_n=500000.0, isp_s=300.0),
        StageConfig(2, "S2", dry_mass_kg=1000.0, propellant_mass_kg=5000.0, thrust_n=100000.0, isp_s=350.0),
    ]
    from app.space.orbit import calculate_multistage_dv
    two_stage_dv, _ = calculate_multistage_dv(stages, payload)

    # Single-stage equivalent: total dry=4000, prop=25000, weighted average Isp=310
    single_stage_m0 = 4000.0 + 25000.0 + payload
    single_stage_mf = 4000.0 + payload
    single_stage_dv = tsiolkovsky_dv(310.0, single_stage_m0, single_stage_mf)

    assert two_stage_dv > single_stage_dv
    assert (two_stage_dv - single_stage_dv) > 800.0  # Multi-staging gain > 800 m/s


def test_stage_config_validation():
    with pytest.raises(ValueError, match="dry mass must be positive"):
        StageConfig(1, "Bad", dry_mass_kg=-10.0, propellant_mass_kg=100.0, thrust_n=1000.0, isp_s=300.0).validate()
    with pytest.raises(ValueError, match="propellant mass cannot be negative"):
        StageConfig(1, "Bad", dry_mass_kg=10.0, propellant_mass_kg=-5.0, thrust_n=1000.0, isp_s=300.0).validate()


# --- 2. Circular Velocity & Period Analytical Tests ---

def test_circular_velocity_at_200km():
    """At 200 km altitude (r = 6571 km), circular speed is sqrt(mu/r) ~ 7784.3 m/s (~7.78 km/s)."""
    r = EARTH_RADIUS_M + 200000.0
    v = circular_velocity(r)
    expected = math.sqrt(EARTH_MU / r)
    assert math.isclose(v, expected, rel_tol=1e-9)
    assert 7780.0 <= v <= 7790.0  # Stated textbook range around 7.78 km/s


def test_circular_velocity_at_iss_altitude_400km():
    """At 400 km altitude (ISS orbit), v_circ ~ 7668.6 m/s."""
    r = EARTH_RADIUS_M + 400000.0
    v = circular_velocity(r)
    assert 7660.0 <= v <= 7680.0


def test_circular_velocity_invalid_radius():
    with pytest.raises(ValueError, match="Orbit radius must be positive"):
        circular_velocity(0.0)
    with pytest.raises(ValueError, match="Orbit radius must be positive"):
        circular_velocity(-1000.0)


def test_orbital_period_at_200km():
    """Period at 200 km LEO is 2*pi*sqrt(r^3/mu) ~ 5308.5 s (~88.5 min)."""
    r = EARTH_RADIUS_M + 200000.0
    period = orbital_period(r)
    expected = 2.0 * math.pi * math.sqrt((r ** 3) / EARTH_MU)
    assert math.isclose(period, expected, rel_tol=1e-9)
    assert 5300.0 <= period <= 5320.0
    assert 88.0 <= (period / 60.0) <= 89.0


def test_orbital_period_at_geo():
    """Period at GEO radius 42,164 km must match Earth sidereal day (~86,164 s, ~23.93 hr)."""
    r_geo = 42164140.0
    period = orbital_period(r_geo)
    assert math.isclose(period, 86164.1, rel_tol=0.001)


def test_orbital_period_invalid_semi_major_axis():
    with pytest.raises(ValueError, match="Semi-major axis must be positive"):
        orbital_period(-500.0)


# --- 3. Vis-Viva Equation Tests ---

def test_vis_viva_circular_orbit_equivalence():
    """At r == a, vis-viva equation must return identical speed to circular_velocity."""
    r = 7000000.0
    v_vv = vis_viva_speed(r, r)
    v_circ = circular_velocity(r)
    assert math.isclose(v_vv, v_circ, rel_tol=1e-9)


def test_vis_viva_eccentric_orbit_periapsis_apoapsis():
    """In an eccentric orbit (rp=6600 km, ra=8000 km), v(periapsis) > v_circ > v(apoapsis)."""
    rp = 6600000.0
    ra = 8000000.0
    a = (rp + ra) / 2.0
    v_peri = vis_viva_speed(rp, a)
    v_apo = vis_viva_speed(ra, a)
    v_circ_peri = circular_velocity(rp)
    v_circ_apo = circular_velocity(ra)

    assert v_peri > v_circ_peri
    assert v_apo < v_circ_apo
    assert v_peri > v_apo


def test_vis_viva_invalid_inputs():
    with pytest.raises(ValueError):
        vis_viva_speed(-100.0, 7000000.0)
    with pytest.raises(ValueError):
        vis_viva_speed(7000000.0, -100.0)


# --- 4. Hohmann Transfer Analytical Tests ---

def test_hohmann_transfer_leo_to_geo_closed_form():
    """
    Standard textbook problem: 200 km LEO (r1=6571 km) to GEO (r2=42164 km).
    Textbook closed-form values:
    dv1 ~ 2436 m/s, dv2 ~ 1468 m/s, total dv ~ 3934 m/s (Curtis, Example 6.1).
    """
    r1 = EARTH_RADIUS_M + 200000.0
    r2 = 42164000.0
    tx = hohmann_transfer(r1, r2)

    # Analytical formula check
    a_tx = (r1 + r2) / 2.0
    expected_dv1 = abs(math.sqrt(EARTH_MU * (2.0 / r1 - 1.0 / a_tx)) - math.sqrt(EARTH_MU / r1))
    expected_dv2 = abs(math.sqrt(EARTH_MU / r2) - math.sqrt(EARTH_MU * (2.0 / r2 - 1.0 / a_tx)))
    expected_total = expected_dv1 + expected_dv2

    assert math.isclose(tx["dv1_ms"], expected_dv1, abs_tol=0.1)
    assert math.isclose(tx["dv2_ms"], expected_dv2, abs_tol=0.1)
    assert math.isclose(tx["total_dv_ms"], expected_total, abs_tol=0.1)

    # Documented textbook range assertion: [3900 m/s, 3960 m/s]
    assert 3900.0 <= tx["total_dv_ms"] <= 3960.0
    # Transfer duration: ~5.28 hours
    assert 5.0 <= tx["transfer_time_hr"] <= 5.5


def test_hohmann_transfer_symmetry():
    """Transfer dv and duration from r1 to r2 equals that from r2 to r1."""
    r1 = 6600000.0
    r2 = 12000000.0
    tx1 = hohmann_transfer(r1, r2)
    tx2 = hohmann_transfer(r2, r1)
    assert math.isclose(tx1["total_dv_ms"], tx2["total_dv_ms"], abs_tol=0.01)
    assert math.isclose(tx1["transfer_time_s"], tx2["transfer_time_s"], abs_tol=0.01)


def test_hohmann_transfer_invalid_radii():
    with pytest.raises(ValueError):
        hohmann_transfer(-1000.0, 7000000.0)
    with pytest.raises(ValueError):
        hohmann_transfer(7000000.0, 0.0)


# --- 5. Ascent Budget & Dynamics Tests ---

def test_ascent_delta_v_budget():
    """Required ascent dv = v_circ(R + h) + ascent_losses."""
    h = 200000.0
    v_circ = circular_velocity(EARTH_RADIUS_M + h)
    expected = v_circ + DEFAULT_ASCENT_LOSSES_MS
    actual = ascent_delta_v(h, DEFAULT_ASCENT_LOSSES_MS)
    assert math.isclose(actual, expected, rel_tol=1e-9)


def test_ascent_delta_v_custom_losses():
    h = 300000.0
    losses = 1250.0
    expected = circular_velocity(EARTH_RADIUS_M + h) + losses
    actual = ascent_delta_v(h, losses)
    assert math.isclose(actual, expected, rel_tol=1e-9)


def test_ascent_delta_v_invalid_altitude():
    with pytest.raises(ValueError, match="Target altitude cannot be negative"):
        ascent_delta_v(-50.0)


def test_liftoff_twr_computation():
    """TWR = Thrust / (Mass * g0)."""
    thrust = 1000000.0
    mass = 80000.0
    expected = thrust / (mass * STANDARD_G0)
    actual = liftoff_twr(thrust, mass)
    assert math.isclose(actual, expected, rel_tol=1e-9)


def test_liftoff_twr_invalid_inputs():
    with pytest.raises(ValueError):
        liftoff_twr(1000.0, -50.0)
    with pytest.raises(ValueError):
        liftoff_twr(-1000.0, 50.0)


def test_burn_time_computation():
    """Burn time = prop_mass * Isp * g0 / thrust."""
    prop = 10000.0
    thrust = 200000.0
    isp = 300.0
    expected = prop * isp * STANDARD_G0 / thrust
    actual = burn_time(prop, thrust, isp)
    assert math.isclose(actual, expected, rel_tol=1e-9)


# --- 6. Mission Outcome Tests (All Outlines Reachable) ---

def test_mission_outcome_no_liftoff():
    """Design with Stage 1 thrust < liftoff weight yields outcome 'no_liftoff'."""
    # Under-powered booster: 50 kN thrust for 20 ton vehicle (TWR ~ 0.25)
    stages = [StageConfig(1, "WeakBooster", dry_mass_kg=4000.0, propellant_mass_kg=16000.0, thrust_n=50000.0, isp_s=280.0)]
    res = evaluate_mission(stages, payload_mass_kg=500.0)
    assert res["outcome"] == "no_liftoff"
    assert res["passed"] is False
    assert res["liftoff_twr"] < 1.0
    assert "Liftoff failed" in res["insight"]


def test_mission_outcome_suborbital_fall():
    """Sounding rocket with high TWR but very low delta-v (< 85% of LEO) yields 'suborbital_fall'."""
    stages = [StageConfig(1, "Sounding", dry_mass_kg=400.0, propellant_mass_kg=1500.0, thrust_n=60000.0, isp_s=240.0)]
    res = evaluate_mission(stages, payload_mass_kg=50.0, target_altitude_m=200000.0)
    assert res["outcome"] == "suborbital_fall"
    assert res["passed"] is False
    assert res["liftoff_twr"] > 1.0
    assert res["available_dv_ms"] < (0.85 * res["required_dv_ms"])
    assert "Suborbital trajectory" in res["insight"]


def test_mission_outcome_orbit_eccentric():
    """Rocket with ~92% of required delta-v reaches apogee but yields 'orbit_eccentric'."""
    stages = [
        StageConfig(1, "S1", dry_mass_kg=4000.0, propellant_mass_kg=35000.0, thrust_n=800000.0, isp_s=280.0),
        StageConfig(2, "S2", dry_mass_kg=1000.0, propellant_mass_kg=8000.0, thrust_n=100000.0, isp_s=320.0),
    ]
    res = evaluate_mission(stages, payload_mass_kg=800.0, target_altitude_m=200000.0)
    assert res["outcome"] == "orbit_eccentric"
    assert res["passed"] is False
    assert "Eccentric partial orbit" in res["insight"]


def test_mission_outcome_orbit_reached():
    """Standard Orbis-1 launch vehicle with nominal payload reaches circular LEO orbit."""
    stages = [
        StageConfig(1, "S1", dry_mass_kg=4200.0, propellant_mass_kg=50000.0, thrust_n=950000.0, isp_s=288.0),
        StageConfig(2, "S2", dry_mass_kg=1100.0, propellant_mass_kg=9000.0, thrust_n=120000.0, isp_s=365.0),
    ]
    res = evaluate_mission(stages, payload_mass_kg=800.0, target_altitude_m=200000.0)
    assert res["outcome"] == "orbit_reached"
    assert res["passed"] is True
    assert res["margin_pct"] > 0.0
    assert res["achieved_orbit"]["perigee_km"] == 200.0
    assert res["achieved_orbit"]["apogee_km"] == 200.0
    assert "Stable circular orbit achieved" in res["insight"]


def test_mission_outcome_transfer_complete():
    """Heavy launch vehicle with upper stage reaches LEO and successfully completes transfer to GEO."""
    stages = [
        StageConfig(1, "Booster", dry_mass_kg=16000.0, propellant_mass_kg=210000.0, thrust_n=3500000.0, isp_s=305.0),
        StageConfig(2, "TransferStage", dry_mass_kg=3200.0, propellant_mass_kg=42000.0, thrust_n=450000.0, isp_s=445.0),
    ]
    res = evaluate_mission(
        stages,
        payload_mass_kg=500.0,
        target_altitude_m=200000.0,
        transfer_altitude_m=35786000.0,
    )
    assert res["outcome"] == "transfer_complete"
    assert res["passed"] is True
    assert res["achieved_orbit"]["apogee_km"] == 35786.0
    assert "Target transfer completed" in res["insight"]


def test_mission_outcome_transfer_failed():
    """Standard Orbis-1 (LEO-only rocket) attempting a GEO transfer establishes LEO but fails transfer."""
    stages = [
        StageConfig(1, "S1", dry_mass_kg=4200.0, propellant_mass_kg=50000.0, thrust_n=950000.0, isp_s=288.0),
        StageConfig(2, "S2", dry_mass_kg=1100.0, propellant_mass_kg=9000.0, thrust_n=120000.0, isp_s=365.0),
    ]
    res = evaluate_mission(
        stages,
        payload_mass_kg=800.0,
        target_altitude_m=200000.0,
        transfer_altitude_m=35786000.0,
    )
    assert res["outcome"] == "transfer_failed"
    assert res["passed"] is False
    assert "Transfer burn failed" in res["insight"]


def test_mission_evaluation_determinism():
    """Running identical mission parameters 10 times produces strictly bit-identical results."""
    stages = [
        StageConfig(1, "S1", dry_mass_kg=4200.0, propellant_mass_kg=50000.0, thrust_n=950000.0, isp_s=288.0),
        StageConfig(2, "S2", dry_mass_kg=1100.0, propellant_mass_kg=9000.0, thrust_n=120000.0, isp_s=365.0),
    ]
    runs = [evaluate_mission(stages, payload_mass_kg=800.0, target_altitude_m=200000.0) for _ in range(10)]
    first = runs[0]
    for r in runs[1:]:
        assert r["outcome"] == first["outcome"]
        assert r["available_dv_ms"] == first["available_dv_ms"]
        assert r["required_dv_ms"] == first["required_dv_ms"]
        assert r["margin_pct"] == first["margin_pct"]
        assert r["insight"] == first["insight"]


# --- 7. Keplerian 2D Propagator & Invariant Conservation Tests ---

def test_kepler_orbit_path_generation():
    """Generates 2D path points on circular orbit."""
    r = 7000000.0
    pts = generate_orbit_path(r, 0.0, num_points=64)
    assert len(pts) == 64
    for p in pts:
        radius = math.sqrt(p["x_m"] ** 2 + p["y_m"] ** 2)
        assert math.isclose(radius, r, rel_tol=1e-5)


def test_kepler_orbit_path_invalid_params():
    with pytest.raises(ValueError):
        generate_orbit_path(-1000.0, 0.1)
    with pytest.raises(ValueError):
        generate_orbit_path(7000000.0, 1.2)  # Parabolic / hyperbolic out of scope


def test_kepler_rk4_energy_angular_momentum_conservation():
    """
    Simulate a 200 km LEO circular orbit over 2 complete revolutions.
    Assert specific mechanical energy (E) and angular momentum (h) are conserved within 0.1% (1e-3).
    """
    r0 = EARTH_RADIUS_M + 200000.0
    v0 = circular_velocity(r0)
    period = orbital_period(r0)

    # Propagate for 2 complete orbits with 10s steps
    states = propagate_kepler_rk4((r0, 0.0), (0.0, v0), total_time_s=2.0 * period, dt_s=10.0)
    assert len(states) >= 100

    conserved, metrics = check_conservation(states, tolerance=1e-3)
    assert conserved is True
    assert metrics["rel_energy_error"] < 1e-3
    assert metrics["rel_h_error"] < 1e-3


# --- 8. Presets & SimModule Reality Checks ---

def test_rocket_presets_loaded_and_valid():
    """Default presets in rockets.json contain valid stages and required provenance fields."""
    presets = load_rocket_presets()
    assert len(presets) >= 3
    ids = [p["id"] for p in presets]
    assert "sounding_suborbital" in ids
    assert "orbis_1" in ids
    assert "orbis_heavy" in ids

    for p in presets:
        assert "provenance" in p
        assert len(p["stages"]) >= 1
        for s in p["stages"]:
            assert s["dry_mass_kg"] > 0
            assert s["propellant_capacity_kg"] > 0


def test_space_orbit_sim_module_reality_checks():
    """All 5 built-in analytical reality checks of SpaceOrbitModule pass."""
    module = SpaceOrbitModule()
    checks = module.reality_checks()
    assert len(checks) == 5
    for c in checks:
        assert c.passed is True
        assert c.model_card is not None
        assert "Educational simulation only" in c.model_card.disclaimer
