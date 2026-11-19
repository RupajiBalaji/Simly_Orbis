"""
backend/app/chem/titration_curve.py
Titration Live Curve & Indicator Band Generator.

Implements Section 9.2 & Section 18 (P3-T3) of Simly Orbis MVP Build Specification:
- Live titration curve (pH against volume delivered) drawn from backend points
- Indicator transition band definition and color interpolation
- Serves as the single backend source of truth for the HUD live curve widget
"""

from __future__ import annotations

from typing import Any, Dict, List
from app.modules.chem_titration import compute_indicator_color, compute_ph_strong, compute_ph_weak

INDICATOR_BANDS: Dict[str, Dict[str, Any]] = {
    "phenolphthalein": {
        "transition_low": 8.2,
        "transition_high": 10.0,
        "color_acid": "#f8fafc",
        "color_transition": "#fbcfe8",
        "color_base": "#ec4899",
        "name": "Phenolphthalein",
    },
    "methyl_orange": {
        "transition_low": 3.1,
        "transition_high": 4.4,
        "color_acid": "#ef4444",
        "color_transition": "#f97316",
        "color_base": "#eab308",
        "name": "Methyl Orange",
    },
    "bromothymol_blue": {
        "transition_low": 6.0,
        "transition_high": 7.6,
        "color_acid": "#eab308",
        "color_transition": "#22c55e",
        "color_base": "#3b82f6",
        "name": "Bromothymol Blue",
    },
}


def build_titration_curve(
    analyte: str = "hcl_0.1M",
    analyte_volume_ml: float = 25.0,
    titrant_conc_m: float = 0.1,
    titrant_added_ml: float = 0.0,
    indicator: str = "phenolphthalein",
    max_volume_ml: float = 50.0,
) -> Dict[str, Any]:
    """
    Generate complete live titration curve dataset with indicator transition band.
    """
    is_weak = (analyte == "acetic_0.1M")
    ca = 0.1
    cb = titrant_conc_m
    va = analyte_volume_ml
    eq_volume_ml = (ca * va) / cb

    # Current state
    if is_weak:
        current_ph = compute_ph_weak(ca, va, cb, titrant_added_ml)
    else:
        current_ph = compute_ph_strong(ca, va, cb, titrant_added_ml)

    current_color = compute_indicator_color(current_ph, indicator)

    # Sample discrete curve points across 0..max_volume_ml
    # Denser sampling around the equivalence point for sharp sigmoid transition
    v_samples = [
        0.0, 5.0, 10.0, 15.0, 18.0, 20.0, 22.0, 23.5, 24.0, 24.5, 24.8,
        24.9, 25.0, 25.1, 25.2, 25.5, 26.0, 26.5, 28.0, 30.0, 35.0, 40.0, 50.0
    ]

    points: List[Dict[str, Any]] = []
    for v in v_samples:
        if is_weak:
            ph = compute_ph_weak(ca, va, cb, v)
        else:
            ph = compute_ph_strong(ca, va, cb, v)
        c = compute_indicator_color(ph, indicator)
        points.append({
            "volume_ml": v,
            "ph": round(ph, 3),
            "color_hex": c,
        })

    band_info = INDICATOR_BANDS.get(indicator, INDICATOR_BANDS["phenolphthalein"])

    # Equivalence point pH: 7.0 for strong/strong, ~8.72 for acetic/NaOH
    eq_ph = compute_ph_weak(ca, va, cb, eq_volume_ml) if is_weak else 7.0

    summary_text = (
        f"pH: {current_ph:.2f} | V: {titrant_added_ml:.2f} mL | "
        f"Equivalence: {eq_volume_ml:.2f} mL (pH {eq_ph:.2f}) | "
        f"Indicator Band: {band_info['transition_low']:.1f}-{band_info['transition_high']:.1f}"
    )

    return {
        "analyte": analyte,
        "analyte_volume_ml": analyte_volume_ml,
        "titrant": "naoh_0.1M",
        "titrant_conc_m": titrant_conc_m,
        "titrant_added_ml": round(titrant_added_ml, 2),
        "current_ph": round(current_ph, 2),
        "current_color": current_color,
        "equivalence_volume_ml": round(eq_volume_ml, 2),
        "equivalence_ph": round(eq_ph, 2),
        "indicator": indicator,
        "indicator_band": band_info,
        "points": points,
        "summary_text": summary_text,
    }
