"""
GET /api/validation/summary – Validation harness results and benchmark metrics.
Reads cached evaluation summary against primary literature references.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Query

from app.validation.runner import get_validation_summary

router = APIRouter(prefix="/api/validation", tags=["validation"])


@router.get("/summary", summary="Validation benchmark summary against literature")
async def validation_summary(
    refresh: bool = Query(default=False, description="Force re-evaluation of benchmarks"),
) -> dict[str, Any]:
    """
    Return cached validation metrics: total references, verified count, pass rate,
    median fold error, pending human check count, sensitivity analysis, and provenance banner.
    """
    return get_validation_summary(force_refresh=refresh)
