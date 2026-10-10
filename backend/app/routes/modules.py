"""
GET /api/modules – list registered modules
GET /api/modules/{id} – module details and JSON schema
GET /api/modules/{id}/reality-check – verification benchmarks
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.base import RealityCheck
from app.core.registry import get_module, list_modules

router = APIRouter(prefix="/api/modules", tags=["modules"])


class ModuleSummary(BaseModel):
    id: str
    name: str
    district: str
    description: str
    version: str


class ModuleDetail(ModuleSummary):
    params_schema: dict[str, Any]


@router.get("", response_model=list[ModuleSummary], summary="List registered simulation modules")
async def get_modules() -> list[ModuleSummary]:
    """Return all registered simulation district modules."""
    return [
        ModuleSummary(
            id=m.id,
            name=m.name,
            district=m.district,
            description=m.description,
            version=m.version,
        )
        for m in list_modules()
    ]


@router.get("/{module_id}", response_model=ModuleDetail, summary="Get module details and parameters schema")
async def get_module_detail(module_id: str) -> ModuleDetail:
    """Return module metadata and its Pydantic JSON schema."""
    try:
        mod = get_module(module_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ModuleDetail(
        id=mod.id,
        name=mod.name,
        district=mod.district,
        description=mod.description,
        version=mod.version,
        params_schema=mod.params_model.model_json_schema(),
    )


@router.get(
    "/{module_id}/reality-check",
    response_model=list[RealityCheck],
    summary="Get module reality check benchmarks",
)
async def get_reality_checks(module_id: str) -> list[RealityCheck]:
    """Execute and return analytical reality-check benchmarks for a module."""
    try:
        mod = get_module(module_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return mod.reality_checks()
