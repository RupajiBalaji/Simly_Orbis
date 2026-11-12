"""
Simly Orbis Orbital Mechanics and Rocket Engine (backend/app/space/orbit.py).

Pure-Python deterministic physics engine for launch vehicle ascent,
orbital velocity, Hohmann transfers, and 2D Keplerian orbit propagation.

Physical Constants & Reference Values:
- Earth standard gravitational parameter (mu): 3.986004418e14 m^3/s^2 (WGS-84 / NASA standard).
- Earth volumetric mean radius (R): 6371e3 m (6371.0 km, IUGG spherical approximation).
- Standard sea-level acceleration of gravity (g0): 9.80665 m/s^2 (ISO 80000-3).

Educational simulation platform. Not medical advice. Not clinical evidence.
Not intended for actual mission planning, trajectory simulation, or flight hardware control.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

# Physical Constants
EARTH_MU: float = 3.986004418e14  # m^3 / s^2
EARTH_RADIUS_M: float = 6371000.0  # 6,371 km volumetric mean radius
STANDARD_G0: float = 9.80665  # m / s^2

# Game-balanced default ascent losses (gravity, aerodynamic drag, steering)
# Labelled: game-balanced, not a trajectory simulation
DEFAULT_ASCENT_LOSSES_MS: float = 1500.0


@dataclass
class StageConfig:
    stage_num: int
    name: str
    dry_mass_kg: float
    propellant_mass_kg: float
    thrust_n: float
    isp_s: float

    def validate(self) -> None:
        if self.dry_mass_kg <= 0:
            raise ValueError(f"Stage {self.stage_num} dry mass must be positive, got {self.dry_mass_kg}")
        if self.propellant_mass_kg < 0:
            raise ValueError(f"Stage {self.stage_num} propellant mass cannot be negative, got {self.propellant_mass_kg}")
        if self.thrust_n <= 0:
            raise ValueError(f"Stage {self.stage_num} thrust must be positive, got {self.thrust_n}")
        if self.isp_s <= 0:
            raise ValueError(f"Stage {self.stage_num} Isp must be positive, got {self.isp_s}")


# --- A. Tsiolkovsky Rocket Equations ---

def tsiolkovsky_dv(isp_s: float, m0_kg: float, mf_kg: float) -> float:
    """
    Calculate Tsiolkovsky delta-v: dv = Isp * g0 * ln(m0 / mf).
    """
    if isp_s <= 0:
        raise ValueError(f"Specific impulse must be positive, got {isp_s}")
    if m0_kg <= 0:
        raise ValueError(f"Initial mass must be positive, got {m0_kg}")
    if mf_kg <= 0:
        raise ValueError(f"Final mass must be positive, got {mf_kg}")
    if mf_kg > m0_kg:
        raise ValueError(f"Final mass ({mf_kg} kg) cannot exceed initial mass ({m0_kg} kg)")
    if m0_kg == mf_kg:
        return 0.0
    return float(isp_s * STANDARD_G0 * math.log(m0_kg / mf_kg))


def calculate_stage_dv(
    stage_dry_mass_kg: float,
    stage_prop_mass_kg: float,
    upper_mass_kg: float,
    isp_s: float,
) -> float:
    """
    Calculate delta-v for an individual stage carrying an upper stage or payload mass.
    """
    m0 = stage_dry_mass_kg + stage_prop_mass_kg + upper_mass_kg
    mf = stage_dry_mass_kg + upper_mass_kg
    return tsiolkovsky_dv(isp_s, m0, mf)


def calculate_multistage_dv(
    stages: Sequence[StageConfig],
    payload_mass_kg: float,
) -> tuple[float, list[dict[str, Any]]]:
    """
    Calculate stacked multistage delta-v in sequential order (Stage 1 first, dropping dry mass).
    Returns (total_dv_ms, per_stage_details).
    """
    if payload_mass_kg < 0:
        raise ValueError(f"Payload mass cannot be negative, got {payload_mass_kg}")
    if not stages:
        return 0.0, []

    for st in stages:
        st.validate()

    # Pre-calculate upper stack masses
    # For stage i, upper_mass is payload + all stages > i (both dry and propellant)
    n = len(stages)
    stage_details: list[dict[str, Any]] = []
    total_dv = 0.0

    for i in range(n):
        current = stages[i]
        upper_mass = payload_mass_kg + sum(
            stages[k].dry_mass_kg + stages[k].propellant_mass_kg for k in range(i + 1, n)
        )
        m0 = current.dry_mass_kg + current.propellant_mass_kg + upper_mass
        mf = current.dry_mass_kg + upper_mass
        dv = tsiolkovsky_dv(current.isp_s, m0, mf)
        total_dv += dv

        # Burn time and mass flow
        m_dot = current.thrust_n / (current.isp_s * STANDARD_G0)
        burn_t = current.propellant_mass_kg / m_dot if m_dot > 0 else 0.0

        stage_details.append({
            "stage_num": current.stage_num,
            "name": current.name,
            "initial_mass_kg": round(m0, 2),
            "burnout_mass_kg": round(mf, 2),
            "propellant_burned_kg": round(current.propellant_mass_kg, 2),
            "isp_s": current.isp_s,
            "thrust_n": current.thrust_n,
            "burn_time_s": round(burn_t, 2),
            "delta_v_ms": round(dv, 2),
        })

    return total_dv, stage_details


# --- B. Orbital Mechanics (Vis-Viva, Period, Hohmann) ---

def circular_velocity(radius_m: float) -> float:
    """
    Calculate circular orbital velocity: v_circ = sqrt(mu / r).
    """
    if radius_m <= 0:
        raise ValueError(f"Orbit radius must be positive, got {radius_m}")
    return float(math.sqrt(EARTH_MU / radius_m))


def orbital_period(semi_major_axis_m: float) -> float:
    """
    Calculate Keplerian orbital period: T = 2 * pi * sqrt(a^3 / mu).
    """
    if semi_major_axis_m <= 0:
        raise ValueError(f"Semi-major axis must be positive, got {semi_major_axis_m}")
    return float(2.0 * math.pi * math.sqrt((semi_major_axis_m ** 3) / EARTH_MU))


def vis_viva_speed(radius_m: float, semi_major_axis_m: float) -> float:
    """
    Calculate orbital speed using the vis-viva equation: v = sqrt(mu * (2/r - 1/a)).
    """
    if radius_m <= 0:
        raise ValueError(f"Radius must be positive, got {radius_m}")
    if semi_major_axis_m <= 0:
        raise ValueError(f"Semi-major axis must be positive, got {semi_major_axis_m}")
    term = (2.0 / radius_m) - (1.0 / semi_major_axis_m)
    if term < 0:
        raise ValueError(f"Hyperbolic trajectory or invalid semi-major axis {semi_major_axis_m} at radius {radius_m}")
    return float(math.sqrt(EARTH_MU * term))


def hohmann_transfer(r1_m: float, r2_m: float) -> dict[str, Any]:
    """
    Calculate two-impulse coplanar Hohmann transfer between circular orbits r1 and r2.
    """
    if r1_m <= 0 or r2_m <= 0:
        raise ValueError(f"Radii must be positive, got r1={r1_m}, r2={r2_m}")

    a_tx = (r1_m + r2_m) / 2.0
    v_c1 = circular_velocity(r1_m)
    v_tx1 = math.sqrt(EARTH_MU * ((2.0 / r1_m) - (1.0 / a_tx)))
    dv1 = abs(v_tx1 - v_c1)

    v_c2 = circular_velocity(r2_m)
    v_tx2 = math.sqrt(EARTH_MU * ((2.0 / r2_m) - (1.0 / a_tx)))
    dv2 = abs(v_c2 - v_tx2)

    total_dv = dv1 + dv2
    t_transfer = math.pi * math.sqrt((a_tx ** 3) / EARTH_MU)

    return {
        "r1_m": r1_m,
        "r2_m": r2_m,
        "semi_major_axis_m": a_tx,
        "dv1_ms": round(dv1, 2),
        "dv2_ms": round(dv2, 2),
        "total_dv_ms": round(total_dv, 2),
        "transfer_time_s": round(t_transfer, 2),
        "transfer_time_min": round(t_transfer / 60.0, 2),
        "transfer_time_hr": round(t_transfer / 3600.0, 2),
    }


# --- C. Ascent Budget & Liftoff Dynamics ---

def ascent_delta_v(
    target_altitude_m: float,
    ascent_losses_ms: float = DEFAULT_ASCENT_LOSSES_MS,
) -> float:
    """
    Required delta-v to reach circular orbit from surface:
    dv_req = v_circ(R + h) + ascent_losses_ms.
    ascent_losses_ms is an explicit game-balanced parameter accounting for gravity and drag.
    """
    if target_altitude_m < 0:
        raise ValueError(f"Target altitude cannot be negative, got {target_altitude_m}")
    r = EARTH_RADIUS_M + target_altitude_m
    v_circ = circular_velocity(r)
    return float(v_circ + ascent_losses_ms)


def liftoff_twr(stage1_thrust_n: float, total_liftoff_mass_kg: float) -> float:
    """
    Calculate thrust-to-weight ratio at liftoff: TWR = Thrust / (Mass * g0).
    """
    if total_liftoff_mass_kg <= 0:
        raise ValueError(f"Total liftoff mass must be positive, got {total_liftoff_mass_kg}")
    if stage1_thrust_n <= 0:
        raise ValueError(f"Thrust must be positive, got {stage1_thrust_n}")
    weight = total_liftoff_mass_kg * STANDARD_G0
    return float(stage1_thrust_n / weight)


def burn_time(propellant_mass_kg: float, thrust_n: float, isp_s: float) -> float:
    """
    Burn time = propellant_mass / mass_flow_rate.
    """
    if propellant_mass_kg < 0:
        raise ValueError("Propellant mass cannot be negative")
    if thrust_n <= 0 or isp_s <= 0:
        raise ValueError("Thrust and Isp must be positive")
    m_dot = thrust_n / (isp_s * STANDARD_G0)
    return float(propellant_mass_kg / m_dot)


# --- D. Mission Evaluation ---

def evaluate_mission(
    stages: Sequence[StageConfig],
    payload_mass_kg: float,
    target_altitude_m: float = 200000.0,  # 200 km default LEO
    transfer_altitude_m: float | None = None,  # Optional transfer orbit altitude
    ascent_losses_ms: float = DEFAULT_ASCENT_LOSSES_MS,
) -> dict[str, Any]:
    """
    Deterministic launch vehicle mission evaluation.

    Returns outcome in:
    {no_liftoff, suborbital_fall, orbit_reached, orbit_eccentric, transfer_complete, transfer_failed}
    along with achieved orbit metrics, delta-v budget table, margin %, TWR, and an analytical insight sentence.
    """
    if not stages:
        return {
            "outcome": "no_liftoff",
            "reason": "Vehicle has no stages defined.",
            "insight": "Vehicle has no rocket stages defined.",
            "passed": False,
        }

    # Calculate total liftoff mass
    total_liftoff_mass = payload_mass_kg + sum(s.dry_mass_kg + s.propellant_mass_kg for s in stages)
    twr0 = liftoff_twr(stages[0].thrust_n, total_liftoff_mass)

    # 1. Check liftoff TWR constraint
    if twr0 <= 1.0:
        return {
            "outcome": "no_liftoff",
            "passed": False,
            "liftoff_twr": round(twr0, 3),
            "total_mass_kg": round(total_liftoff_mass, 2),
            "payload_mass_kg": payload_mass_kg,
            "available_dv_ms": 0.0,
            "required_dv_ms": round(ascent_delta_v(target_altitude_m, ascent_losses_ms), 2),
            "margin_pct": -100.0,
            "achieved_orbit": {"perigee_km": 0.0, "apogee_km": 0.0, "period_min": 0.0},
            "insight": f"Liftoff failed: Stage 1 thrust of {stages[0].thrust_n/1e3:.1f} kN is insufficient to lift the {total_liftoff_mass:,.0f} kg vehicle (TWR = {twr0:.2f}; minimum required is > 1.0).",
            "dv_budget": [],
        }

    total_avail_dv, stage_details = calculate_multistage_dv(stages, payload_mass_kg)
    req_ascent_dv = ascent_delta_v(target_altitude_m, ascent_losses_ms)

    # Budget table items
    dv_budget: list[dict[str, Any]] = [
        {
            "phase": "Ascent & Circularization (Target LEO)",
            "required_dv_ms": round(req_ascent_dv, 2),
            "available_dv_ms": round(min(total_avail_dv, req_ascent_dv), 2),
            "status": "MET" if total_avail_dv >= req_ascent_dv else "DEFICIT",
        }
    ]

    # Evaluate optional transfer
    hohmann_info = None
    req_transfer_dv = 0.0
    if transfer_altitude_m is not None and transfer_altitude_m > target_altitude_m:
        r1 = EARTH_RADIUS_M + target_altitude_m
        r2 = EARTH_RADIUS_M + transfer_altitude_m
        hohmann_info = hohmann_transfer(r1, r2)
        req_transfer_dv = hohmann_info["total_dv_ms"]
        dv_budget.append({
            "phase": f"Hohmann Transfer to {transfer_altitude_m/1e3:.1f} km",
            "required_dv_ms": round(req_transfer_dv, 2),
            "available_dv_ms": round(max(0.0, total_avail_dv - req_ascent_dv), 2),
            "status": "MET" if total_avail_dv >= (req_ascent_dv + req_transfer_dv) else "DEFICIT",
        })

    total_required_dv = req_ascent_dv + req_transfer_dv
    margin_pct = ((total_avail_dv - total_required_dv) / total_required_dv) * 100.0

    # Determine deterministic outcome
    if total_avail_dv < (0.85 * req_ascent_dv):
        outcome = "suborbital_fall"
        passed = False
        achieved_apogee_km = round((total_avail_dv / req_ascent_dv) * (target_altitude_m / 1000.0), 1)
        achieved_orbit = {
            "perigee_km": -EARTH_RADIUS_M / 1000.0,
            "apogee_km": achieved_apogee_km,
            "period_min": 0.0,
        }
        deficit = req_ascent_dv - total_avail_dv
        insight = f"Suborbital trajectory: Available delta-v ({total_avail_dv:,.0f} m/s) fell {deficit:,.0f} m/s short of orbital velocity and ascent losses, peaking at {achieved_apogee_km:.1f} km before ballistic ocean impact."
    elif total_avail_dv < req_ascent_dv:
        outcome = "orbit_eccentric"
        passed = False
        # Achieves target apogee, but perigee is inside upper atmosphere
        achieved_perigee_km = round(max(0.0, (total_avail_dv - 0.85 * req_ascent_dv) / (0.15 * req_ascent_dv) * (target_altitude_m / 1000.0)), 1)
        achieved_orbit = {
            "perigee_km": achieved_perigee_km,
            "apogee_km": round(target_altitude_m / 1000.0, 1),
            "period_min": round(orbital_period(EARTH_RADIUS_M + (achieved_perigee_km * 1000 + target_altitude_m) / 2.0) / 60.0, 1),
        }
        insight = f"Eccentric partial orbit: Available delta-v reached apogee at {target_altitude_m/1e3:.0f} km but lacked {req_ascent_dv - total_avail_dv:,.0f} m/s to circularize, leaving an unstable perigee at {achieved_perigee_km:.1f} km."
    else:
        # Reached parking orbit at target_altitude_m
        target_period_min = round(orbital_period(EARTH_RADIUS_M + target_altitude_m) / 60.0, 2)
        if transfer_altitude_m is None:
            outcome = "orbit_reached"
            passed = True
            achieved_orbit = {
                "perigee_km": round(target_altitude_m / 1000.0, 1),
                "apogee_km": round(target_altitude_m / 1000.0, 1),
                "period_min": target_period_min,
            }
            insight = f"Stable circular orbit achieved: Inserted cleanly at {target_altitude_m/1e3:.1f} km (period: {target_period_min} min) with {margin_pct:.1f}% delta-v propellant reserves."
        else:
            # Transfer was requested
            if total_avail_dv >= total_required_dv:
                outcome = "transfer_complete"
                passed = True
                final_period_min = round(orbital_period(EARTH_RADIUS_M + transfer_altitude_m) / 60.0, 2)
                achieved_orbit = {
                    "perigee_km": round(transfer_altitude_m / 1000.0, 1),
                    "apogee_km": round(transfer_altitude_m / 1000.0, 1),
                    "period_min": final_period_min,
                }
                insight = f"Target transfer completed: Hohmann transfer and circularization at {transfer_altitude_m/1e3:,.1f} km accomplished with {margin_pct:.1f}% remaining delta-v margin."
            else:
                outcome = "transfer_failed"
                passed = False
                achieved_orbit = {
                    "perigee_km": round(target_altitude_m / 1000.0, 1),
                    "apogee_km": round(target_altitude_m / 1000.0, 1),
                    "period_min": target_period_min,
                }
                transfer_deficit = total_required_dv - total_avail_dv
                insight = f"Transfer burn failed: Established initial parking orbit at {target_altitude_m/1e3:.1f} km, but upper stage was {transfer_deficit:,.0f} m/s short of completing transfer to {transfer_altitude_m/1e3:,.1f} km."

    return {
        "outcome": outcome,
        "passed": passed,
        "liftoff_twr": round(twr0, 3),
        "total_mass_kg": round(total_liftoff_mass, 2),
        "payload_mass_kg": payload_mass_kg,
        "available_dv_ms": round(total_avail_dv, 2),
        "required_dv_ms": round(total_required_dv, 2),
        "margin_pct": round(margin_pct, 2),
        "achieved_orbit": achieved_orbit,
        "target_altitude_km": target_altitude_m / 1000.0,
        "transfer_altitude_km": (transfer_altitude_m / 1000.0) if transfer_altitude_m else None,
        "ascent_losses_ms": ascent_losses_ms,
        "insight": insight,
        "stages": stage_details,
        "dv_budget": dv_budget,
        "hohmann_info": hohmann_info,
    }


# --- E. 2D Kepler Propagator & Energy/Momentum Conservation ---

def generate_orbit_path(
    semi_major_axis_m: float,
    eccentricity: float,
    num_points: int = 128,
) -> list[dict[str, float]]:
    """
    Generate 2D (x, y) Cartesian coordinates centered at Earth center.
    Earth is at focal point (0, 0).
    """
    if semi_major_axis_m <= 0:
        raise ValueError(f"Semi-major axis must be positive, got {semi_major_axis_m}")
    if eccentricity < 0 or eccentricity >= 1.0:
        raise ValueError(f"Eccentricity must be in [0, 1), got {eccentricity}")

    p = semi_major_axis_m * (1.0 - eccentricity ** 2)
    points: list[dict[str, float]] = []

    for i in range(num_points):
        theta = (2.0 * math.pi * i) / num_points
        r = p / (1.0 + eccentricity * math.cos(theta))
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        points.append({
            "theta_rad": round(theta, 4),
            "r_m": round(r, 2),
            "x_m": round(x, 2),
            "y_m": round(y, 2),
            "altitude_km": round((r - EARTH_RADIUS_M) / 1000.0, 2),
        })

    return points


def propagate_kepler_rk4(
    r0: tuple[float, float],
    v0: tuple[float, float],
    total_time_s: float,
    dt_s: float = 10.0,
) -> list[dict[str, float]]:
    """
    Propagate 2D two-body orbit using classical Runge-Kutta 4th Order.
    d^2 r / dt^2 = - (mu / |r|^3) * r.
    Returns list of states: [{time, x, y, vx, vy, r, v, energy, h}].
    """
    def accel(pos: tuple[float, float]) -> tuple[float, float]:
        r_mag = math.sqrt(pos[0] ** 2 + pos[1] ** 2)
        if r_mag == 0:
            return 0.0, 0.0
        factor = -EARTH_MU / (r_mag ** 3)
        return factor * pos[0], factor * pos[1]

    t = 0.0
    x, y = r0
    vx, vy = v0

    states: list[dict[str, float]] = []

    while t <= total_time_s:
        r_mag = math.sqrt(x ** 2 + y ** 2)
        v_mag = math.sqrt(vx ** 2 + vy ** 2)
        # Specific mechanical energy: E = v^2/2 - mu/r
        energy = (v_mag ** 2) / 2.0 - (EARTH_MU / r_mag)
        # Specific angular momentum: h = r x v = x * vy - y * vx
        h_ang = x * vy - y * vx

        states.append({
            "t_s": round(t, 2),
            "x_m": x,
            "y_m": y,
            "vx_ms": vx,
            "vy_ms": vy,
            "r_m": r_mag,
            "v_ms": v_mag,
            "energy_jkg": energy,
            "h_m2s": h_ang,
        })

        # RK4 step
        ax1, ay1 = accel((x, y))

        x_k2 = x + 0.5 * dt_s * vx
        y_k2 = y + 0.5 * dt_s * vy
        vx_k2 = vx + 0.5 * dt_s * ax1
        vy_k2 = vy + 0.5 * dt_s * ay1
        ax2, ay2 = accel((x_k2, y_k2))

        x_k3 = x + 0.5 * dt_s * vx_k2
        y_k3 = y + 0.5 * dt_s * vy_k2
        vx_k3 = vx + 0.5 * dt_s * ax2
        vy_k3 = vy + 0.5 * dt_s * ay2
        ax3, ay3 = accel((x_k3, y_k3))

        x_k4 = x + dt_s * vx_k3
        y_k4 = y + dt_s * vy_k3
        vx_k4 = vx + dt_s * ax3
        vy_k4 = vy + dt_s * ay3
        ax4, ay4 = accel((x_k4, y_k4))

        x += (dt_s / 6.0) * (vx + 2.0 * vx_k2 + 2.0 * vx_k3 + vx_k4)
        y += (dt_s / 6.0) * (vy + 2.0 * vy_k2 + 2.0 * vy_k3 + vy_k4)
        vx += (dt_s / 6.0) * (ax1 + 2.0 * ax2 + 2.0 * ax3 + ax4)
        vy += (dt_s / 6.0) * (ay1 + 2.0 * ay2 + 2.0 * ay3 + ay4)

        t += dt_s

    return states


def check_conservation(
    states: list[dict[str, float]],
    tolerance: float = 1e-3,
) -> tuple[bool, dict[str, float]]:
    """
    Check conservation of specific orbital energy (E) and specific angular momentum (h).
    Returns (conserved, metrics_dict).
    """
    if not states:
        return False, {}

    energies = [s["energy_jkg"] for s in states]
    ang_moms = [s["h_m2s"] for s in states]

    e0 = energies[0]
    h0 = ang_moms[0]

    max_delta_e = max(abs(e - e0) for e in energies)
    max_delta_h = max(abs(h - h0) for h in ang_moms)

    rel_error_e = max_delta_e / abs(e0) if abs(e0) > 0 else max_delta_e
    rel_error_h = max_delta_h / abs(h0) if abs(h0) > 0 else max_delta_h

    conserved = (rel_error_e <= tolerance) and (rel_error_h <= tolerance)

    return conserved, {
        "initial_energy_jkg": e0,
        "max_delta_energy": max_delta_e,
        "rel_energy_error": rel_error_e,
        "initial_h_m2s": h0,
        "max_delta_h": max_delta_h,
        "rel_h_error": rel_error_h,
        "tolerance": tolerance,
        "conserved": conserved,
    }


# --- F. Presets Helper ---

def load_rocket_presets() -> list[dict[str, Any]]:
    """Load default rocket vehicle presets from rockets.json."""
    path = Path(__file__).resolve().parent / "rockets.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_rocket_preset(preset_id: str) -> dict[str, Any] | None:
    """Retrieve a specific rocket preset by ID."""
    for p in load_rocket_presets():
        if p.get("id") == preset_id:
            return p
    return None
