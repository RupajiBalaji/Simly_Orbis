"""
GET /api/validation/summary – Validation harness results and benchmark metrics.
Reads cached evaluation summary against primary literature references.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any
from fastapi import APIRouter, Query

from app.validation.runner import get_validation_summary

router = APIRouter(prefix="/api/validation", tags=["validation"])
_VAL_DATA_DIR = Path(__file__).resolve().parents[3] / "validation" / "data"


@router.get("/summary", summary="Validation benchmark summary against literature")
async def validation_summary(
    refresh: bool = Query(default=False, description="Force re-evaluation of benchmarks"),
) -> dict[str, Any]:
    """
    Return cached validation metrics: total references, verified count, pass rate,
    median fold error, pending human check count, sensitivity analysis, and provenance banner.
    """
    return get_validation_summary(force_refresh=refresh)


@router.get("/review", summary="Read-only list of validation reference rows for human expert review")
async def validation_review_rows() -> dict[str, Any]:
    """Return all validation CSV rows (read-only) for the expert review UI."""
    rows: list[dict[str, Any]] = []
    if _VAL_DATA_DIR.exists():
        for csv_path in sorted(_VAL_DATA_DIR.glob("*.csv")):
            with csv_path.open("r", encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    if not row or not row.get("id"):
                        continue
                    rows.append({
                        "file": csv_path.name,
                        "id": row.get("id", ""),
                        "quantity": row.get("quantity", ""),
                        "value": row.get("value", ""),
                        "unit": row.get("unit", ""),
                        "population_or_condition": row.get("population_or_condition", ""),
                        "dose_or_regimen": row.get("dose_or_regimen", ""),
                        "source_citation": row.get("source_citation", ""),
                        "source_url_or_doi": row.get("source_url_or_doi", ""),
                        "retrieved_on": row.get("retrieved_on", ""),
                        "verified_by": row.get("verified_by", "unverified"),
                        "notes": row.get("notes", ""),
                    })
    verified = sum(1 for r in rows if r.get("verified_by", "unverified") not in ("", "unverified"))
    return {
        "total": len(rows),
        "verified": verified,
        "unverified": len(rows) - verified,
        "rows": rows,
    }
