"""
Rule-based fallback hints grounded in engine values for all 34 rule IDs (P7-T5):
- R1..R10 (Lab & PK / Titration safety & protocol rules)
- S1..S8  (Space Launch & Orbit Bench rules)
- D1..D8  (Dose Lab rules)
- K1..K4  (Kinetics Bench rules)
- B1..B4  (Buffer Bench rules)
"""

from __future__ import annotations

from typing import Any

ALL_RULE_IDS: tuple[str, ...] = (
    *(f"R{i}" for i in range(1, 11)),
    *(f"S{i}" for i in range(1, 9)),
    *(f"D{i}" for i in range(1, 9)),
    *(f"K{i}" for i in range(1, 5)),
    *(f"B{i}" for i in range(1, 5)),
)


def _num(ev: dict[str, Any], key: str, default: float) -> float:
    val = ev.get(key)
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def build_rule_based_hint(rule_id: str, engine_values: dict[str, Any] | None = None) -> str:
    """
    Return a deterministic, educational rule-based hint for any rule ID
    using live engine values from the session's apparatus_state.
    """
    rid = (rule_id or "").strip().upper()
    ev = engine_values or {}

    ppe_list = ev.get("ppe") or []
    ppe_count = len(ppe_list) if isinstance(ppe_list, (list, set, tuple)) else int(_num(ev, "ppe_count", 0))
    mass_mg = _num(ev, "mass_mg", 500.0)
    cmax = _num(ev, "cmax_mg_l", 0.0)
    ph = _num(ev, "ph", 7.0)
    vol_ml = _num(ev, "titrant_volume_ml", 0.0)
    twr = _num(ev, "twr", 0.0)
    total_dv = _num(ev, "total_dv", 0.0)
    ap_km = _num(ev, "apoapsis_km", 0.0)
    pe_km = _num(ev, "periapsis_km", 0.0)
    payload_kg = _num(ev, "payload_kg", 0.0)
    dose_mg = _num(ev, "dose_mg", 500.0)
    temp_k = _num(ev, "temp_k", 298.15)
    rate_k = _num(ev, "rate_constant", 0.0)
    pka = _num(ev, "pka", 4.76)

    hints: dict[str, str] = {
        # R1-R10: Core PK Ward & Titration Lab rules
        "R1": f"Rule R1 (PPE Required): You currently have {ppe_count}/3 PPE items equipped. Put on goggles, gloves, and lab coat before handling reagents.",
        "R2": f"Rule R2 (Tare Balance First): Current weighed mass is {mass_mg:.1f} mg. Always tare the analytical balance to 0.0 mg before weighing.",
        "R3": f"Rule R3 (Dose Bounds): Measured mass is {mass_mg:.1f} mg. Keep paracetamol preparation within safe simulation bounds (250-1000 mg) before administration.",
        "R4": f"Rule R4 (Preparation Sequence): Dissolve and verify the {mass_mg:.1f} mg dose before administering; predicted Cmax is {cmax:.2f} mg/L.",
        "R5": f"Rule R5 (Sampling Timing): Advance simulation time after dosing before drawing blood; current peak Cmax readout is {cmax:.2f} mg/L.",
        "R6": f"Rule R6 (Educational Simulation Scope): This simulator reports model values (Cmax {cmax:.2f} mg/L) for learning only, not clinical dosing advice.",
        "R7": f"Rule R7 (Burette Rinse & Fill): Current titrant dispensed is {vol_ml:.1f} mL at pH {ph:.2f}. Rinse and fill the burette before titrating.",
        "R8": f"Rule R8 (Indicator Before Titration): At pH {ph:.2f} ({vol_ml:.1f} mL added), add phenolphthalein indicator to the flask before titrating.",
        "R9": f"Rule R9 (Endpoint Control): Current flask pH is {ph:.2f} after {vol_ml:.1f} mL NaOH. Add titrant dropwise near pH 7.0-8.2 to avoid overshooting.",
        "R10": f"Rule R10 (Swirl & Record): After adding {vol_ml:.1f} mL (pH {ph:.2f}), swirl the flask to equilibrate before recording the endpoint.",
        # S1-S8: Space Launch & Orbit Bench rules
        "S1": f"Rule S1 (Select Mission Satellite): Current payload is {payload_kg:.0f} kg. Select a target satellite mission before configuring vehicle stages.",
        "S2": f"Rule S2 (Liftoff TWR >= 1.2): Current liftoff TWR is {twr:.2f}. Reduce payload ({payload_kg:.0f} kg) or increase thrust so TWR exceeds 1.20.",
        "S3": f"Rule S3 (Delta-v Budget): Current total delta-v is {total_dv:.0f} m/s. Ensure sufficient propellant/staging for LEO (>9300 m/s total).",
        "S4": f"Rule S4 (Periapsis Clearance): Current periapsis is {pe_km:.1f} km (apoapsis {ap_km:.1f} km). Raise periapsis above 160 km to avoid atmospheric reentry.",
        "S5": f"Rule S5 (Target Orbit Window): Current orbit is {pe_km:.1f} x {ap_km:.1f} km. Adjust burn parameters to match the target mission altitude.",
        "S6": f"Rule S6 (Staging Safety): With delta-v {total_dv:.0f} m/s and TWR {twr:.2f}, verify stage separation sequence before orbital insertion.",
        "S7": f"Rule S7 (Payload Envelope): Current payload mass is {payload_kg:.0f} kg (TWR {twr:.2f}). Stay within the launch vehicle's structural payload limit.",
        "S8": f"Rule S8 (Telemetry Verification): Confirm apoapsis {ap_km:.1f} km and periapsis {pe_km:.1f} km telemetry before finalizing mission report.",
        # D1-D8: Dose Lab rules
        "D1": f"Rule D1 (Dose Lab PPE): {ppe_count}/3 PPE items equipped. Equip goggles, gloves, and coat before preparing {dose_mg:.1f} mg dose.",
        "D2": f"Rule D2 (Concentration & Volume): Current dose is {dose_mg:.1f} mg. Verify stock concentration and target volume before mixing.",
        "D3": f"Rule D3 (Therapeutic Window): Current dose {dose_mg:.1f} mg yields Cmax {cmax:.2f} mg/L. Keep plasma concentration inside the target window.",
        "D4": f"Rule D4 (Dosing Interval): At {dose_mg:.1f} mg (Cmax {cmax:.2f} mg/L), space repeat doses according to half-life to prevent accumulation.",
        "D5": f"Rule D5 (Renal/Hepatic Check): Current Cmax is {cmax:.2f} mg/L for {dose_mg:.1f} mg. Adjust dose when clearance is reduced.",
        "D6": f"Rule D6 (Measurement Precision): Verify {dose_mg:.1f} mg measurement on a tared balance before transferring to solution.",
        "D7": f"Rule D7 (Educational Non-Clinical Rule): Dose Lab values ({dose_mg:.1f} mg, Cmax {cmax:.2f} mg/L) are simulation outputs, not medical advice.",
        "D8": f"Rule D8 (Report Submission): Complete all sampling points (current Cmax {cmax:.2f} mg/L) before submitting the Dose Lab report.",
        # K1-K4: Kinetics Bench rules
        "K1": f"Rule K1 (Kinetics PPE & Setup): {ppe_count}/3 PPE items equipped at {temp_k:.1f} K. Equip full PPE before starting reaction kinetics.",
        "K2": f"Rule K2 (Temperature Control): Current reaction temperature is {temp_k:.1f} K (k={rate_k:.4g}). Stabilize temperature before sampling.",
        "K3": f"Rule K3 (Rate Sampling): At {temp_k:.1f} K with rate constant k={rate_k:.4g}, collect at least 3 timepoints to fit order and activation energy.",
        "K4": f"Rule K4 (Arrhenius Analysis): Use measured k={rate_k:.4g} across temperatures (current {temp_k:.1f} K) before submitting kinetics report.",
        # B1-B4: Buffer Bench rules
        "B1": f"Rule B1 (Buffer PPE & Calibration): {ppe_count}/3 PPE items equipped; pH meter reads {ph:.2f}. Equip PPE and calibrate meter first.",
        "B2": f"Rule B2 (Henderson-Hasselbalch Ratio): Target pKa is {pka:.2f} and current pH is {ph:.2f}. Select conjugate acid/base ratio within pKa +/- 1.",
        "B3": f"Rule B3 (Buffer Capacity): At pH {ph:.2f} (pKa {pka:.2f}), add strong acid/base in small increments ({vol_ml:.1f} mL) to test capacity.",
        "B4": f"Rule B4 (Verify Final Buffer pH): Confirm stabilized pH {ph:.2f} relative to pKa {pka:.2f} before submitting the Buffer Bench report.",
    }
    return hints.get(
        rid,
        f"Rule {rid}: Follow the active protocol step and verify engine readouts (pH {ph:.2f}, Cmax {cmax:.2f} mg/L).",
    )
