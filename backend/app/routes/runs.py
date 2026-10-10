"""
POST /api/run – execute a module run and store record
GET  /api/runs – list recent run records
GET  /api/runs/{run_id} – get single run record
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, ValidationError

import app.db as _db
from app.core.base import RunResult
from app.core.registry import get_module

router = APIRouter(tags=["runs"])


class RunRequest(BaseModel):
    module_id: str = Field(..., description="Target simulation module identifier (e.g. 'pharma.pk')")
    params: dict[str, Any] = Field(..., description="Simulation input parameters matching module schema")
    nickname: str | None = Field(default=None, max_length=64, description="Optional player/user nickname")
    parent_run_id: str | None = Field(default=None, description="Optional parent run id for lineage/branching")


class RunExecutionResponse(BaseModel):
    run_id: str
    result: RunResult


class RunRecordResponse(BaseModel):
    run_id: str
    module_id: str
    district: str
    params: dict[str, Any]
    summary: dict[str, Any]
    series: dict[str, list[float]] | None = None
    series_omitted: bool = False
    warnings: list[str] = []
    nickname: str | None = None
    parent_run_id: str | None = None
    engine_version: str
    duration_ms: float
    created_at: str
    storage_mode: str


@router.post("/api/run", response_model=RunExecutionResponse, summary="Execute simulation module and record run")
async def execute_run(body: RunRequest) -> RunExecutionResponse:
    """
    Validate parameters against module's schema, execute computation,
    persist a run record in the database, and return {run_id, result}.
    """
    try:
        mod = get_module(body.module_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        validated_params = mod.params_model.model_validate(body.params)
    except ValidationError as err:
        raise HTTPException(status_code=422, detail=err.errors()) from err

    # Pure computation run
    result = mod.run(validated_params)

    # Prepare persistent run record
    run_id = str(uuid.uuid4())
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Series storage limit check (cap at 5,000 points)
    total_points = 0
    series_data = result.series
    series_omitted = False
    if series_data:
        total_points = sum(len(v) for v in series_data.values() if isinstance(v, list))
        if total_points > 5000:
            series_data = None
            series_omitted = True

    record = {
        "run_id": run_id,
        "module_id": mod.id,
        "district": mod.district,
        "params": result.params,
        "summary": result.summary,
        "series": series_data,
        "series_omitted": series_omitted,
        "warnings": result.warnings,
        "nickname": body.nickname,
        "parent_run_id": body.parent_run_id,
        "engine_version": result.engine_version,
        "duration_ms": result.duration_ms,
        "created_at": now_iso,
        "storage_mode": _db.STORAGE_MODE,
    }

    try:
        await _db.insert_run(record)
    except Exception as exc:  # noqa: BLE001
        import logging  # noqa: PLC0415
        logging.getLogger(__name__).warning("Failed to persist run record: %s", exc)

    return RunExecutionResponse(run_id=run_id, result=result)


@router.get("/api/runs", response_model=list[RunRecordResponse], summary="List recent simulation runs")
async def list_runs_endpoint(
    limit: int = Query(20, ge=1, le=100, description="Max run records to return (1-100)"),
    module_id: str | None = Query(None, description="Optional module_id filter"),
) -> list[RunRecordResponse]:
    """Return latest simulation runs ordered by created_at descending."""
    docs = await _db.list_runs(module_id=module_id, limit=limit)
    return [RunRecordResponse(**d) for d in docs]


@router.get("/api/runs/{run_id}", response_model=RunRecordResponse, summary="Get single simulation run record")
async def get_run_endpoint(run_id: str) -> RunRecordResponse:
    """Retrieve details for a specific run_id."""
    doc = await _db.get_run(run_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return RunRecordResponse(**doc)
