"""
Tests for Reality Check endpoints and Model Cards (GET /api/modules/{id}/reality-check).

Verifies:
1. Structured checks with PASS/FAIL flags for all three modules (pharma.pk, pharma.trial, chem.titration).
2. All reality checks pass analytical benchmark criteria (11/11 passed total).
3. Model cards returned with underlying models, key assumptions, known limitations, and disclaimer.
4. Disclaimer string matches exact safety wording.
5. GET /api/modules/{id}/model-card returns standalone model card documentation.
6. GET /api/modules/{id}/reality-check?full=true returns complete RealityCheckReport container.
7. GET /api/modules/reality-checks/all returns combined status and 11/11 summary badge.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

TARGET_MODULES = ["pharma.pk", "pharma.trial", "chem.titration"]
MANDATORY_DISCLAIMER = (
    "Educational simulation only. Not validated for clinical dosing "
    "or industrial chemical process control."
)


@pytest.mark.asyncio
@pytest.mark.parametrize("module_id", TARGET_MODULES)
async def test_reality_check_endpoint_structure_and_pass_flags(client: AsyncClient, module_id: str):
    """Each module endpoint returns structured checks with passed=True and attached model cards."""
    res = await client.get(f"/api/modules/{module_id}/reality-check")
    assert res.status_code == 200
    checks = res.json()
    assert isinstance(checks, list)
    assert len(checks) >= 3

    for c in checks:
        assert "name" in c
        assert "description" in c
        assert "expected" in c
        assert "actual" in c
        assert "tolerance" in c
        assert "passed" in c
        assert c["passed"] is True
        assert "source_note" in c
        assert "model_card" in c
        assert c["model_card"] is not None
        assert MANDATORY_DISCLAIMER in c["model_card"]["disclaimer"]


@pytest.mark.asyncio
@pytest.mark.parametrize("module_id", TARGET_MODULES)
async def test_module_model_card_endpoint(client: AsyncClient, module_id: str):
    """GET /api/modules/{id}/model-card returns comprehensive scientific model card."""
    res = await client.get(f"/api/modules/{module_id}/model-card")
    assert res.status_code == 200
    card = res.json()
    assert card["module_id"] == module_id
    assert len(card["underlying_models"]) >= 1
    assert len(card["key_assumptions"]) >= 1
    assert len(card["known_limitations"]) >= 1
    assert MANDATORY_DISCLAIMER in card["disclaimer"]


@pytest.mark.asyncio
@pytest.mark.parametrize("module_id", TARGET_MODULES)
async def test_reality_check_full_report_parameter(client: AsyncClient, module_id: str):
    """GET /api/modules/{id}/reality-check?full=true returns container with summary metrics."""
    res = await client.get(f"/api/modules/{module_id}/reality-check?full=true")
    assert res.status_code == 200
    report = res.json()
    assert report["module_id"] == module_id
    assert report["passed"] is True
    assert report["passed_count"] == report["total"]
    assert report["total"] >= 3
    assert len(report["checks"]) == report["total"]
    assert "model_card" in report


@pytest.mark.asyncio
async def test_all_reality_checks_summary(client: AsyncClient):
    """Combined reality checks endpoint verifies all 11 benchmarks pass."""
    res = await client.get("/api/modules/reality-checks/all")
    assert res.status_code == 200
    data = res.json()
    assert data["total_checks"] == 11
    assert data["total_passed"] == 11
    assert data["all_passed"] is True
    assert data["summary_badge"] == "11/11 passed"
    assert "pharma.pk" in data["modules"]
    assert "pharma.trial" in data["modules"]
    assert "chem.titration" in data["modules"]
