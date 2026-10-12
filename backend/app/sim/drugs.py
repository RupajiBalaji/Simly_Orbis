"""
Drug catalogue loader.

Reads app/sim/drugs.json and exposes a typed dict keyed by drug name
(lowercase).  Import DRUGS in other modules to get the catalogue.

DISCLAIMER: Parameters are approximate, game-balanced, and educational only.
Do NOT use for clinical or diagnostic purposes.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.sim.models import Drug

_DRUGS_JSON = Path(__file__).parent / "drugs.json"


def _load_drugs() -> dict[str, Drug]:
    data: list[dict] = json.loads(_DRUGS_JSON.read_text(encoding="utf-8"))
    return {
        entry["name"].lower(): Drug(
            name=entry["name"],
            ka=entry["ka"],
            half_life=entry["half_life"],
            vd_per_kg=entry["vd_per_kg"],
            bioavailability=entry["bioavailability"],
            green_low=entry["green_low"],
            green_high=entry["green_high"],
            red_threshold=entry["red_threshold"],
            standard_dose_mg=entry["standard_dose_mg"],
            provenance=entry.get("provenance", {}),
        )
        for entry in data
    }


# Module-level singleton – loaded once on first import.
DRUGS: dict[str, Drug] = _load_drugs()


def get_drug(name: str) -> Drug:
    """Return a Drug by name (case-insensitive).  Raises KeyError if unknown."""
    key = name.lower()
    if key not in DRUGS:
        raise KeyError(f"Unknown drug: {name!r}. Available: {list(DRUGS)}")
    return DRUGS[key]
