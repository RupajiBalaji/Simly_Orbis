"""
GET /api/modules – list registered modules
GET /api/modules/{id} – module details and JSON schema
GET /api/modules/{id}/reality-check – verification benchmarks
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.base import ModelCard, RealityCheck
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


class RealityCheckReport(BaseModel):
    module_id: str
    checks: list[RealityCheck]
    model_card: ModelCard
    passed: bool
    total: int
    passed_count: int


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


@router.get("/reality-checks/all", summary="Get reality checks and model cards across all active modules")
async def get_all_reality_checks() -> dict[str, Any]:
    """Execute reality checks across all modules and return combined status."""
    results: dict[str, Any] = {}
    total_checks = 0
    total_passed = 0
    all_passed = True
    for mod in list_modules():
        checks = mod.reality_checks()
        card = mod.get_model_card()
        p_cnt = sum(1 for c in checks if c.passed)
        total_checks += len(checks)
        total_passed += p_cnt
        if not all(c.passed for c in checks):
            all_passed = False
        results[mod.id] = {
            "module_id": mod.id,
            "name": mod.name,
            "district": mod.district,
            "checks": [c.model_dump() for c in checks],
            "model_card": card.model_dump(),
            "passed": all(c.passed for c in checks),
            "passed_count": p_cnt,
            "total": len(checks),
        }
    return {
        "modules": results,
        "total_checks": total_checks,
        "total_passed": total_passed,
        "summary_badge": f"{total_passed}/{total_checks} passed",
        "all_passed": all_passed,
    }


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
    "/{module_id}/model-card",
    response_model=ModelCard,
    summary="Get module scientific model card documentation",
)
async def get_module_model_card(module_id: str) -> ModelCard:
    """Return scientific documentation card for the requested simulation module."""
    try:
        mod = get_module(module_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return mod.get_model_card()


@router.get(
    "/{module_id}/reality-check",
    summary="Get module reality check benchmarks",
)
async def get_reality_checks(
    module_id: str,
    full: bool = Query(default=False, description="Whether to return full report container"),
) -> Any:
    """Execute and return analytical reality-check benchmarks for a module."""
    try:
        mod = get_module(module_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    checks = mod.reality_checks()
    if full:
        card = mod.get_model_card()
        passed_cnt = sum(1 for c in checks if c.passed)
        return RealityCheckReport(
            module_id=mod.id,
            checks=checks,
            model_card=card,
            passed=all(c.passed for c in checks),
            total=len(checks),
            passed_count=passed_cnt,
        )
    return checks

