"""GET /api/drugs – return the full drug catalogue from drugs.json."""

from __future__ import annotations

from fastapi import APIRouter

from app.sim.drugs import DRUGS

router = APIRouter(prefix="/api/drugs", tags=["drugs"])


@router.get("", summary="List all drugs")
async def list_drugs() -> list[dict]:
    """Return PK parameters for every drug in the catalogue."""
    return [
        {
            "id": key,
            "name": drug.name,
            "ka": drug.ka,
            "half_life": drug.half_life,
            "vd_per_kg": drug.vd_per_kg,
            "bioavailability": drug.bioavailability,
            "green_low": drug.green_low,
            "green_high": drug.green_high,
            "red_threshold": drug.red_threshold,
            "standard_dose_mg": drug.standard_dose_mg,
            "provenance": drug.provenance,
        }
        for key, drug in DRUGS.items()
    ]
