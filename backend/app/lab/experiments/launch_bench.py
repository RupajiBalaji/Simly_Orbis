"""
Launch & Orbit Bench Experiment Definition ("launch_bench").

Simulate multi-stage orbital launch vehicle configuration, propellant loading,
preflight safety clearance, Keplerian orbital insertion, and Hohmann orbital transfers.
"""

from __future__ import annotations

from app.lab.experiments.base import ExperimentDefinition


LAUNCH_BENCH_EXPERIMENT = ExperimentDefinition(
    id="launch_bench",
    title="Launch & Orbit Bench",
    district="space",
    description=(
        "Design rocket staging, verify Tsiolkovsky delta-v budgets and liftoff TWR, "
        "execute preflight safety checklists, launch into low Earth orbit from Pad 39A, "
        "and execute precision Hohmann orbital transfer maneuvers."
    ),
    learning_goals=[
        "Calculate multi-stage rocket mass budgets and Tsiolkovsky delta-v.",
        "Ensure liftoff thrust-to-weight ratio (TWR > 1.0) and verify stage propellant capacities.",
        "Execute preflight diagnostic checklists and obtain range safety clearance.",
        "Achieve stable low Earth orbit (LEO) insertion with minimal ascent gravity and steering losses.",
        "Execute Hohmann transfer burns and circularization at target orbital altitudes.",
        "Debrief flight telemetry and verify Keplerian energy conservation.",
    ],
    required_ppe=[],
    apparatus={
        "launch_pad": {
            "type": "launch_pad",
            "status": "clear",
            "pad_id": "pad_39a",
            "rocket_mounted": None,
        },
        "rocket": {
            "type": "rocket",
            "preset_id": None,
            "name": None,
            "stages": [],
            "total_mass_t": 0.0,
            "payload_kg": 0.0,
            "payload_declared": False,
            "fueled": False,
            "status": "prelaunch",
            "current_stage": 1,
            "liftoff_twr": None,
            "total_delta_v_ms": 0.0,
            "required_delta_v_ms": 9300.0,
        },
        "propellant_tanks": {
            "type": "propellant_tanks",
            "available_fuel_t": 1000.0,
            "cryo_chilldown": True,
        },
        "range_control": {
            "type": "range_control",
            "cleared": False,
            "radar_status": "tracking",
            "corridor": "eastward_28.5_deg",
        },
        "flight_computer": {
            "type": "flight_computer",
            "checklist_complete": False,
            "target_orbit_km": 200.0,
            "transfer_orbit_km": 35786.0,
            "guidance_mode": "inertial_gravity_turn",
        },
        "tracking_station": {
            "type": "tracking_station",
            "telemetry": {},
            "mission_status": "prelaunch",
            "outcome": None,
            "debriefed": False,
        },
    },
    inventory={
        "cubesat_50kg": {
            "type": "payload",
            "mass_kg": 50.0,
            "description": "Educational 3U CubeSat constellation payload.",
        },
        "comm_sat_500kg": {
            "type": "payload",
            "mass_kg": 500.0,
            "description": "Geostationary communications technology demonstrator satellite.",
        },
        "iss_cargo_800kg": {
            "type": "payload",
            "mass_kg": 800.0,
            "description": "Low Earth orbit scientific resupply capsule.",
        },
        "heavy_payload_1500kg": {
            "type": "payload",
            "mass_kg": 1500.0,
            "description": "High-capacity deep-space sensor probe platform.",
        },
    },
    allowed_actions=[
        "choose_rocket",
        "declare_payload",
        "fuel_rocket",
        "run_checklist",
        "clear_range",
        "launch",
        "coast",
        "burn_transfer",
        "circularize",
        "debrief",
        "submit_report",
    ],
    protocol=[
        {
            "id": "choose_rocket",
            "title": "Select Launch Vehicle",
            "hint_text": "Select an orbital launch vehicle configuration (e.g. Orbis 1 or Orbis Heavy).",
            "hint": "Select an orbital launch vehicle configuration (e.g. Orbis 1 or Orbis Heavy).",
        },
        {
            "id": "declare_payload",
            "title": "Declare Payload Mass",
            "hint_text": "Specify mission payload mass (kg) within vehicle capacity.",
            "hint": "Specify mission payload mass (kg) within vehicle capacity.",
        },
        {
            "id": "fuel_rocket",
            "title": "Load Propellant",
            "hint_text": "Load propellant into launch vehicle stages according to capacity limits.",
            "hint": "Load propellant into launch vehicle stages according to capacity limits.",
        },
        {
            "id": "run_checklist",
            "title": "Preflight Diagnostic Checklist",
            "hint_text": "Execute preflight flight computer diagnostic checklist.",
            "hint": "Execute preflight flight computer diagnostic checklist.",
        },
        {
            "id": "clear_range",
            "title": "Clear Range Safety",
            "hint_text": "Confirm range safety clearance with tracking and range control.",
            "hint": "Confirm range safety clearance with tracking and range control.",
        },
        {
            "id": "launch",
            "title": "Ignition & Orbital Ascent",
            "hint_text": "Ignite stage 1 and launch vehicle to reach orbital insertion altitude.",
            "hint": "Ignite stage 1 and launch vehicle to reach orbital insertion altitude.",
        },
        {
            "id": "coast",
            "title": "Orbital Coast",
            "hint_text": "Coast to parking orbit apoapsis or transfer point.",
            "hint": "Coast to parking orbit apoapsis or transfer point.",
        },
        {
            "id": "burn_transfer",
            "title": "Hohmann Transfer Burn",
            "hint_text": "Execute apogee or Hohmann transfer burn to target orbit altitude.",
            "hint": "Execute apogee or Hohmann transfer burn to target orbit altitude.",
        },
        {
            "id": "circularize",
            "title": "Circularize Orbit",
            "hint_text": "Execute final circularization burn to achieve target circular orbit.",
            "hint": "Execute final circularization burn to achieve target circular orbit.",
        },
        {
            "id": "debrief",
            "title": "Flight Telemetry Debrief",
            "hint_text": "Analyze orbital telemetry and flight parameters before final sign-off.",
            "hint": "Analyze orbital telemetry and flight parameters before final sign-off.",
        },
    ],
    scoring_weights={
        "safety": 40,
        "accuracy": 30,
        "technique": 20,
        "protocol": 10,
    },
)
