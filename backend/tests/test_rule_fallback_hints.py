"""Tests for P7-T5: every rule ID (R1-R10, S1-S8, D1-D8, K1-K4, B1-B4) has a rule-based hint using engine values."""

from __future__ import annotations

import pytest

from app.lab.rule_hints import ALL_RULE_IDS, build_rule_based_hint


def test_all_34_rule_ids_present():
    assert len(ALL_RULE_IDS) == 34


@pytest.mark.parametrize("rule_id", ALL_RULE_IDS)
def test_rule_based_hint_uses_engine_values(rule_id: str):
    engine_vals = {
        "ppe": ["goggles"],
        "mass_mg": 612.5,
        "cmax_mg_l": 14.25,
        "ph": 8.15,
        "titrant_volume_ml": 18.4,
        "twr": 1.12,
        "total_dv": 8950.0,
        "apoapsis_km": 220.0,
        "periapsis_km": 110.0,
        "payload_kg": 1450.0,
        "dose_mg": 750.0,
        "temp_k": 310.5,
        "rate_constant": 0.045,
        "pka": 4.76,
    }
    hint = build_rule_based_hint(rule_id, engine_vals)
    assert rule_id in hint
    assert len(hint) > 20
    # Verify at least one engine value from the dict is interpolated into the hint
    engine_tokens = ["1/3", "612.5", "14.25", "8.15", "18.4", "1.12", "8950", "220.0", "110.0", "1450", "750.0", "310.5", "0.045", "4.76"]
    assert any(tok in hint for tok in engine_tokens), f"{rule_id} hint did not include engine values: {hint}"
