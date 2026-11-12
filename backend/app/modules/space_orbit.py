"""
Orbital Mechanics & Launch Bench Simulation Module (Module #4: space.orbit).

Computes:
- Tsiolkovsky multistage delta-v budgets.
- Circular orbital velocity, Keplerian periods, and vis-viva dynamics.
- Hohmann coplanar transfer orbits.
- Ascent-to-orbit energy budget with game-balanced atmospheric/gravity losses.
- Deterministic flight outcome evaluation.
"""

from __future__ import annotations

import math
import time
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.core.base import ModelCard, RealityCheck, RunResult, SimModule
from app.core.version import ENGINE_VERSION
from app.space.orbit import (
    EARTH_MU,
    EARTH_RADIUS_M,
    STANDARD_G0,
    DEFAULT_ASCENT_LOSSES_MS,
    StageConfig,
    ascent_delta_v,
    check_conservation,
    circular_velocity,
    evaluate_mission,
    generate_orbit_path,
    get_rocket_preset,
    hohmann_transfer,
    load_rocket_presets,
    orbital_period,
    propagate_kepler_rk4,
    tsiolkovsky_dv,
    vis_viva_speed,
)


class SpaceOrbitParams(BaseModel):
    """Input parameters for space.orbit simulation."""

    rocket_preset: str = Field(
        default="orbis_1",
        description="Preset rocket configuration identifier from rockets.json",
    )
    payload_mass_kg: float = Field(
        default=800.0,
        ge=0.0,
        le=20000.0,
        description="Payload mass placed on top of final rocket stage (kg)",
    )
    propellant_scale_pct: float = Field(
        default=100.0,
        ge=10.0,
        le=120.0,
        description="Scaling factor for default propellant load (percentage)",
    )
    target_altitude_km: float = Field(
        default=200.0,
        ge=100.0,
        le=2000.0,
        description="Target circular parking orbit altitude above Earth surface (km)",
    )
    transfer_altitude_km: float | None = Field(
        default=None,
        ge=200.0,
        le=50000.0,
        description="Optional transfer destination orbit altitude (km)",
    )
    ascent_losses_ms: float = Field(
        default=DEFAULT_ASCENT_LOSSES_MS,
        ge=500.0,
        le=3000.0,
        description="Ascent gravity, drag, and steering losses in m/s (game-balanced parameter)",
    )


class SpaceOrbitModule(SimModule):
    """
    Simulation module for orbital mechanics and launch vehicle dynamics.
    """

    id: str = "space.orbit"
    name: str = "Launch & Orbit Bench"
    district: Literal["space"] = "space"
    description: str = "Deterministic two-body orbital mechanics, Tsiolkovsky delta-v, and launch vehicle ascent."
    version: str = ENGINE_VERSION
    params_model: type[BaseModel] = SpaceOrbitParams

    def run(self, params: BaseModel | dict[str, Any]) -> RunResult:
        """Execute space launch and orbit evaluation."""
        start_time = time.perf_counter()

        if isinstance(params, dict):
            validated = SpaceOrbitParams(**params)
        else:
            validated = params  # type: ignore

        preset = get_rocket_preset(validated.rocket_preset)
        if not preset:
            # Fall back to default
            presets = load_rocket_presets()
            preset = presets[1] if len(presets) > 1 else presets[0]

        # Construct stages applying propellant scaling
        stages: list[StageConfig] = []
        for s in preset.get("stages", []):
            def_prop = s.get("default_propellant_kg", s.get("propellant_capacity_kg", 1000.0))
            actual_prop = def_prop * (validated.propellant_scale_pct / 100.0)
            stages.append(
                StageConfig(
                    stage_num=s["stage_num"],
                    name=s["name"],
                    dry_mass_kg=s["dry_mass_kg"],
                    propellant_mass_kg=actual_prop,
                    thrust_n=s.get("thrust_sea_n", 500000.0),
                    isp_s=s.get("isp_sea_s", 300.0),
                )
            )

        target_alt_m = validated.target_altitude_km * 1000.0
        tx_alt_m = (validated.transfer_altitude_km * 1000.0) if validated.transfer_altitude_km else None

        evaluation = evaluate_mission(
            stages=stages,
            payload_mass_kg=validated.payload_mass_kg,
            target_altitude_m=target_alt_m,
            transfer_altitude_m=tx_alt_m,
            ascent_losses_ms=validated.ascent_losses_ms,
        )

        # Generate orbit trajectory points for visualization
        achieved = evaluation["achieved_orbit"]
        semi_major_m = EARTH_RADIUS_M + target_alt_m
        orbit_points = generate_orbit_path(semi_major_m, 0.0, num_points=64)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        warnings: list[str] = []
        if evaluation["liftoff_twr"] <= 1.0:
            warnings.append("Vehicle cannot lift off: Thrust-to-weight ratio is <= 1.0.")
        if evaluation["margin_pct"] < 5.0 and evaluation["passed"]:
            warnings.append("Low propellant margin warning: Available delta-v margin is under 5.0%.")

        return RunResult(
            module_id=self.id,
            params=validated.model_dump(),
            summary={
                "outcome": evaluation["outcome"],
                "passed": evaluation["passed"],
                "liftoff_twr": evaluation["liftoff_twr"],
                "total_mass_kg": evaluation["total_mass_kg"],
                "available_dv_ms": evaluation["available_dv_ms"],
                "required_dv_ms": evaluation["required_dv_ms"],
                "margin_pct": evaluation["margin_pct"],
                "achieved_orbit": evaluation["achieved_orbit"],
                "insight": evaluation["insight"],
            },
            series={
                "orbit_x_km": [p["x_m"] / 1000.0 for p in orbit_points],
                "orbit_y_km": [p["y_m"] / 1000.0 for p in orbit_points],
            },
            warnings=warnings,
            duration_ms=round(duration_ms, 3),
            engine_version=self.version,
        )

    def reality_checks(self) -> list[RealityCheck]:
        """Execute analytical reality checks verifying physical and mathematical laws."""
        checks: list[RealityCheck] = []

        # 1. Circular velocity at 200 km LEO
        # v = sqrt(mu / (R + 200km)) = sqrt(3.986004418e14 / 6571000) ~ 7784.30 m/s
        r_leo = EARTH_RADIUS_M + 200000.0
        expected_v_leo = math.sqrt(EARTH_MU / r_leo)
        actual_v_leo = circular_velocity(r_leo)
        rel_diff_v = abs(actual_v_leo - expected_v_leo) / expected_v_leo
        checks.append(
            RealityCheck(
                name="LEO Circular Orbital Velocity (200 km)",
                description="Circular orbital speed at 200 km altitude equals sqrt(mu / (R + h)) within numerical precision.",
                expected=round(expected_v_leo, 2),
                actual=round(actual_v_leo, 2),
                tolerance=0.001,
                passed=rel_diff_v <= 0.001,
                source_note="Two-body circular orbit speed from vis-viva equation at r = 6,571 km with WGS-84 mu.",
            )
        )

        # 2. Orbital period at 200 km LEO
        # T = 2 * pi * sqrt(r^3 / mu) ~ 5308.47 s (~88.47 minutes)
        expected_t_leo = 2.0 * math.pi * math.sqrt((r_leo ** 3) / EARTH_MU)
        actual_t_leo = orbital_period(r_leo)
        rel_diff_t = abs(actual_t_leo - expected_t_leo) / expected_t_leo
        checks.append(
            RealityCheck(
                name="LEO Orbital Period (200 km)",
                description="Keplerian orbital period at 200 km altitude matches 2*pi*sqrt(a^3/mu) (~88.5 min).",
                expected=round(expected_t_leo, 2),
                actual=round(actual_t_leo, 2),
                tolerance=0.001,
                passed=rel_diff_t <= 0.001,
                source_note="Kepler's Third Law for circular orbit of radius 6,571 km around Earth.",
            )
        )

        # 3. Geostationary orbital radius
        # T = 86164.0905 s (sidereal day). r = (mu * (T / (2*pi))^2)^(1/3) ~ 42,164.14 km.
        t_sidereal = 86164.0905
        expected_r_geo = ((EARTH_MU * (t_sidereal / (2.0 * math.pi)) ** 2) ** (1.0 / 3.0))
        computed_t_at_geo = orbital_period(expected_r_geo)
        rel_diff_geo = abs(computed_t_at_geo - t_sidereal) / t_sidereal
        checks.append(
            RealityCheck(
                name="Geostationary Orbital Period (Sidereal Day)",
                description="Orbital period at geosynchronous radius (42,164.1 km) matches Earth's sidereal rotation period (86,164.1 s).",
                expected=round(t_sidereal, 1),
                actual=round(computed_t_at_geo, 1),
                tolerance=0.001,
                passed=rel_diff_geo <= 0.001,
                source_note="Vallado, Fundamentals of Astrodynamics and Applications; Earth sidereal rotation period.",
            )
        )

        # 4. Hohmann Transfer Delta-V (200 km LEO to GEO 35,786 km)
        # Textbook Hohmann LEO-to-GEO: dv1 ~ 2436 m/s, dv2 ~ 1468 m/s, total ~ 3934 m/s.
        r_geo = 42164000.0  # standard GEO radius
        hoh = hohmann_transfer(r_leo, r_geo)
        expected_hoh_dv = 3934.0  # standard textbook reference ~3934 m/s
        rel_diff_hoh = abs(hoh["total_dv_ms"] - expected_hoh_dv) / expected_hoh_dv
        checks.append(
            RealityCheck(
                name="Hohmann LEO to GEO Transfer Delta-V",
                description="Total two-impulse Hohmann transfer delta-v from 200 km LEO to GEO equals textbook ~3,934 m/s (± 1%).",
                expected=expected_hoh_dv,
                actual=hoh["total_dv_ms"],
                tolerance=0.01,
                passed=rel_diff_hoh <= 0.01,
                source_note="Curtis, Orbital Mechanics for Engineering Students, Example 6.1 (LEO to GEO transfer).",
            )
        )

        # 5. Energy and Angular Momentum Conservation in Kepler Propagation
        # Propagate circular orbit for 1 full period (~5300 s) in 10s steps
        v_circ = circular_velocity(r_leo)
        sim_states = propagate_kepler_rk4((r_leo, 0.0), (0.0, v_circ), total_time_s=expected_t_leo, dt_s=10.0)
        conserved, cons_metrics = check_conservation(sim_states, tolerance=1e-3)
        checks.append(
            RealityCheck(
                name="2D Kepler Energy & Angular Momentum Conservation",
                description="Numerical RK4 propagation conserves specific mechanical energy and angular momentum within 0.1% over an entire orbit.",
                expected=1.0,
                actual=1.0 if conserved else 0.0,
                tolerance=0.0,
                passed=conserved,
                source_note="Conservative central gravitational field theorem; constant orbital energy and angular momentum.",
            )
        )

        card = self.get_model_card()
        for c in checks:
            c.model_card = card

        return checks

    def get_model_card(self) -> ModelCard:
        """Return scientific documentation card for space orbit simulation."""
        return ModelCard(
            module_id=self.id,
            name=self.name,
            underlying_models=[
                "Tsiolkovsky rocket equation for multistage sequential delta-v and mass fraction accounting.",
                "Classical two-body Newtonian orbital mechanics (vis-viva equation, circular velocity, Kepler's Third Law).",
                "Two-impulse coplanar Hohmann transfer orbit dynamics.",
                "Classical 4th-order Runge-Kutta numerical orbit propagation.",
            ],
            key_assumptions=[
                "Spherical Earth gravitational field (pure point-mass/monopole potential, mu = 3.986004418e14 m^3/s^2).",
                "Ascent losses (aerodynamic drag, gravity drag, steering) modeled via explicit game-balanced parameter (default 1,500 m/s).",
                "Instantaneous impulsive velocity increments (delta-v) for orbital transfer calculations.",
                "Coplanar circular orbits without orbital inclination changes.",
            ],
            known_limitations=[
                "Does not simulate continuous-thrust ascent atmospheric trajectory integration (e.g., dynamic pressure max-q).",
                "Does not model Earth oblateness (J2 perturbation, nodal precession) or non-spherical gravitational harmonics.",
                "Does not model third-body gravitational perturbations (Lunar/Solar) or solar radiation pressure.",
                "Atmospheric reentry heating and aerodynamic drag deceleration during ballistic fall are simplified.",
            ],
            disclaimer="Educational simulation only. Game-balanced where parameters are simplified. Not intended for actual mission planning, trajectory simulation, or flight hardware control.",
        )
