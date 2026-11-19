"""
Virtual Clinical Trial API routes (/api/trial).

Provides endpoints for cohort population simulation and comparative trial analysis
("my dose" vs "standard dose").
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app.core.registry import get_module
from app.modules.pharma_trial import PharmaTrialModule, PharmaTrialParams
from app.pharma.pkpd.trial_v2 import (
    TrialRegimen,
    TrialV2Result,
    VirtualCohortConfig,
    compare_trials_v2,
    generate_trial_v2_csv,
    simulate_trial_v2,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/trial", tags=["trial"])


class CompareTrialRequest(BaseModel):
    """Payload to compare two virtual clinical trial regimens."""

    regimen_a: PharmaTrialParams = Field(
        ..., description="Regimen A (e.g. customized or experimental regimen)"
    )
    regimen_b: PharmaTrialParams | None = Field(
        default=None,
        description="Regimen B (e.g. standard baseline comparator; defaults to 500 mg standard single dose)",
    )


class CompareTrialResponse(BaseModel):
    """Comparative clinical analysis of two virtual cohort regimens."""

    trial_a: dict[str, Any]
    trial_b: dict[str, Any]
    comparison: dict[str, Any]


@router.post("/compare", response_model=CompareTrialResponse, summary="Compare two clinical trial regimens")
async def compare_trial_regimens(body: CompareTrialRequest) -> CompareTrialResponse:
    """
    Run population simulations for two regimens and return both summaries and comparative deltas.
    Allows students/researchers to benchmark custom regimens against clinical standards.
    """
    try:
        mod = get_module("pharma.trial")
    except KeyError:
        mod = PharmaTrialModule()

    # If regimen B is omitted, create standard comparator matching drug and cohort size
    regimen_b = body.regimen_b
    if regimen_b is None:
        regimen_b = PharmaTrialParams(
            drug_id=body.regimen_a.drug_id,
            dose_mg=500.0,
            n_doses=1,
            interval_h=6.0,
            n_patients=body.regimen_a.n_patients,
            seed=body.regimen_a.seed,
            pct_reduced_liver=body.regimen_a.pct_reduced_liver,
        )

    res_a = mod.run(body.regimen_a)
    res_b = mod.run(regimen_b)

    sum_a = res_a.summary
    sum_b = res_b.summary

    diff_in_range = round(sum_a["pct_in_range"] - sum_b["pct_in_range"], 2)
    diff_toxic = round(sum_a["pct_toxic"] - sum_b["pct_toxic"], 2)
    diff_peak = round(sum_a["mean_peak"] - sum_b["mean_peak"], 3)
    diff_helped = sum_a["group_counts"]["in_range"] - sum_b["group_counts"]["in_range"]
    diff_toxic_count = sum_a["group_counts"]["toxic"] - sum_b["group_counts"]["toxic"]

    if diff_toxic > 2.0:
        verdict = f"Regimen A yields {diff_in_range:+.1f}% in-range efficacy but increases toxicity by {diff_toxic:+.1f}%."
    elif diff_in_range > 0.0:
        verdict = f"Regimen A improves therapeutic efficacy by {diff_in_range:+.1f}% without excessive toxicity."
    elif diff_in_range < -5.0:
        verdict = f"Regimen A is subtherapeutic compared to Standard Regimen B ({diff_in_range:+.1f}% in-range)."
    else:
        verdict = f"Regimen A and Standard Regimen B exhibit comparable population outcomes (Δ in-range: {diff_in_range:+.1f}%)."

    comparison = {
        "diff_pct_in_range": diff_in_range,
        "diff_pct_toxic": diff_toxic,
        "diff_mean_peak": diff_peak,
        "diff_helped_patients": diff_helped,
        "diff_toxic_patients": diff_toxic_count,
        "verdict": verdict,
    }

    return CompareTrialResponse(
        trial_a=res_a.model_dump(),
        trial_b=res_b.model_dump(),
        comparison=comparison,
    )


@router.post("/run", summary="Run single clinical trial simulation")
async def run_single_trial(body: PharmaTrialParams) -> dict[str, Any]:
    """Convenience endpoint to execute a single virtual clinical trial."""
    try:
        mod = get_module("pharma.trial")
    except KeyError:
        mod = PharmaTrialModule()

    res = mod.run(body)
    return res.model_dump()


# ---------------------------------------------------------------------------
# Virtual Trial v2 Endpoints
# ---------------------------------------------------------------------------


class TrialV2RunRequest(BaseModel):
    """Payload to execute Virtual Trial v2."""

    regimen: TrialRegimen = Field(default_factory=TrialRegimen)
    cohort: VirtualCohortConfig = Field(default_factory=VirtualCohortConfig)


class TrialV2CompareRequest(BaseModel):
    """Payload to compare two Virtual Trial v2 regimens."""

    regimen_a: TrialRegimen = Field(..., description="Experimental regimen")
    regimen_b: TrialRegimen = Field(..., description="Comparator regimen")
    cohort: VirtualCohortConfig = Field(default_factory=VirtualCohortConfig)


@router.post("/v2/run", response_model=TrialV2Result, summary="Run Virtual Trial v2 population simulation")
async def run_trial_v2(body: TrialV2RunRequest) -> TrialV2Result:
    """
    Run multi-compartment population simulation on virtual adult cohort.
    Always returns:
    - Crowd gallery with color and icon per patient
    - Distributions of Cmax and AUC
    - Percent inside target window, below, and above
    - Deterministic code-written insight statement
    - Label: 'virtual population, not a clinical trial'
    """
    return simulate_trial_v2(body.regimen, body.cohort)


@router.post("/v2/compare", summary="Compare two Virtual Trial v2 regimens")
async def compare_trial_v2_endpoint(body: TrialV2CompareRequest) -> dict[str, Any]:
    """Compare two regimens on the identical virtual population (reproducible seed)."""
    return compare_trials_v2(body.regimen_a, body.regimen_b, body.cohort)


@router.post("/v2/export_csv", summary="Export Virtual Trial v2 results to CSV")
async def export_trial_v2_csv(body: TrialV2RunRequest) -> Response:
    """Run simulation and return formatted CSV for educational data analysis."""
    result = simulate_trial_v2(body.regimen, body.cohort)
    csv_content = generate_trial_v2_csv(result)
    filename = f"virtual_trial_{body.regimen.drug_id}_seed{body.cohort.seed}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

