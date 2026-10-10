"""POST /api/simulate – run the PK engine and return the time series."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.sim.drugs import get_drug
from app.sim.models import Patient
from app.sim.pk_engine import simulate

router = APIRouter(prefix="/api/simulate", tags=["simulate"])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class SimulateRequest(BaseModel):
    drug_id: str = Field(..., description="Drug identifier (e.g. 'paracetamol')")
    weight_kg: float = Field(..., gt=0, le=300, description="Patient weight (kg)")
    clearance_multiplier: float = Field(
        1.0, gt=0, le=5.0,
        description="Multiplier on ke; <1 = reduced clearance, >1 = increased",
    )
    dose_mg: float = Field(..., ge=0, description="Dose per administration (mg)")
    n_doses: int = Field(..., ge=1, le=6, description="Number of doses (1–6)")
    interval_h: float = Field(
        6.0, gt=0, le=24.0,
        description="Dosing interval in hours (ignored when n_doses == 1)",
    )


class SimulateResponse(BaseModel):
    drug_id: str
    times: list[float]
    concentrations: list[float]
    peak_concentration: float
    time_of_peak: float
    pct_green: float
    pct_below_green: float
    pct_red: float


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("", response_model=SimulateResponse, summary="Run PK simulation")
async def run_simulate(body: SimulateRequest) -> SimulateResponse:
    """
    Run a one-compartment Bateman simulation and return the 0–24 h
    concentration time series with summary statistics.
    """
    try:
        drug = get_drug(body.drug_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    patient = Patient(
        weight_kg=body.weight_kg,
        clearance_multiplier=body.clearance_multiplier,
    )

    result = simulate(
        drug=drug,
        patient=patient,
        dose_mg=body.dose_mg,
        n_doses=body.n_doses,
        interval_h=body.interval_h,
    )

    return SimulateResponse(
        drug_id=body.drug_id,
        times=result.times,
        concentrations=result.concentrations,
        peak_concentration=result.peak_concentration,
        time_of_peak=result.time_of_peak,
        pct_green=result.pct_green,
        pct_below_green=result.pct_below_green,
        pct_red=result.pct_red,
    )
