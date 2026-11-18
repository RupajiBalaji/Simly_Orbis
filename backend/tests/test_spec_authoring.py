"""
Tests for Spec Authoring Form, Field-Level Errors, Dry-Run, and Export (P2-T6).

Verifies:
1. Field-level validation returns exact JSON paths and helpful error descriptions.
2. Dry-run executes scripted actions against in-memory authoring spec without database writes.
3. Export endpoint attaches approval flag (approved=False) per section 8.14.
4. Exported spec validates cleanly against Section 10 rules.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import pytest
from httpx import AsyncClient

from app.specs.loader import load_raw_spec
from app.specs.validator import validate_spec_data


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURE_PATH = REPO_ROOT / "specs" / "fixtures" / "worked_example_neutralization.json"


@pytest.fixture
def sample_spec_data() -> dict:
    return load_raw_spec(FIXTURE_PATH)


@pytest.mark.asyncio
async def test_authoring_validate_endpoint_valid_spec(client: AsyncClient, sample_spec_data: dict):
    """POST /api/specs/validate on a valid spec returns valid=True and 0 errors."""
    res = await client.post("/api/specs/validate", json={"spec_data": sample_spec_data})
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["error_count"] == 0
    assert len(data["errors"]) == 0


@pytest.mark.asyncio
async def test_authoring_validate_endpoint_field_level_errors(client: AsyncClient, sample_spec_data: dict):
    """POST /api/specs/validate on an invalid spec returns exact field paths."""
    # 1. Pydantic schema validation error (unknown field)
    bad_data1 = copy.deepcopy(sample_spec_data)
    bad_data1["unknown_authoring_prop"] = "disallowed"
    res1 = await client.post("/api/specs/validate", json={"spec_data": bad_data1})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["valid"] is False
    assert any("unknown_authoring_prop" in e["path"] for e in data1["errors"])

    # 2. Semantic validation errors (min > max and duplicate rule id)
    bad_data2 = copy.deepcopy(sample_spec_data)
    bad_data2["engine"]["parameter_bounds"]["analyte_volume_ml"]["min"] = 100.0
    bad_data2["engine"]["parameter_bounds"]["analyte_volume_ml"]["max"] = 10.0
    bad_data2["rules"].append(copy.deepcopy(bad_data2["rules"][0]))
    res2 = await client.post("/api/specs/validate", json={"spec_data": bad_data2})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["valid"] is False
    assert data2["error_count"] >= 2
    paths2 = [e["path"] for e in data2["errors"]]
    assert any("engine.parameter_bounds.analyte_volume_ml" in p for p in paths2)
    assert any("rules[10].id" in p for p in paths2)


@pytest.mark.asyncio
async def test_authoring_dry_run_endpoint(client: AsyncClient, sample_spec_data: dict):
    """POST /api/specs/dry-run executes scripted actions against an in-memory session."""
    actions = [
        {"action": "wear_ppe", "target": "avatar", "params": {"item": "all"}},
        {"action": "rinse_burette", "target": "burette", "params": {"solvent": "naoh"}},
        {"action": "fill_burette", "target": "burette", "params": {"titrant": "naoh", "volume_ml": 50.0}},
    ]

    res = await client.post(
        "/api/specs/dry-run",
        json={"spec_data": sample_spec_data, "actions": actions},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["total_steps_executed"] == 3
    assert len(data["step_results"]) == 3
    assert data["step_results"][0]["action"] == "wear_ppe"
    assert data["step_results"][0]["accepted"] is True
    assert data["step_results"][1]["action"] == "rinse_burette"
    assert data["step_results"][1]["accepted"] is True
    assert data["step_results"][2]["action"] == "fill_burette"
    assert data["step_results"][2]["accepted"] is True


@pytest.mark.asyncio
async def test_authoring_dry_run_rejects_invalid_spec(client: AsyncClient, sample_spec_data: dict):
    """POST /api/specs/dry-run rejects invalid spec with 422 Unprocessable Entity."""
    bad_data = copy.deepcopy(sample_spec_data)
    bad_data["district"] = "invalid_district"

    res = await client.post(
        "/api/specs/dry-run",
        json={"spec_data": bad_data, "actions": []},
    )
    assert res.status_code == 422
    assert "Cannot dry run invalid spec" in res.json()["detail"]


@pytest.mark.asyncio
async def test_authoring_export_endpoint(client: AsyncClient, sample_spec_data: dict):
    """POST /api/specs/export attaches approved=False approval flag per Section 8.14."""
    res = await client.post("/api/specs/export", json={"spec_data": sample_spec_data})
    assert res.status_code == 200
    data = res.json()
    assert data["approved"] is False
    assert data["approval_status"] == "pending_admin_approval"

    exported = data["exported_spec"]
    assert exported["approved"] is False
    assert exported["approval_status"] == "pending_admin_approval"
    assert exported["id"] == sample_spec_data["id"]

    # Verify that stripping metadata leaves the spec 100% valid
    cleaned = copy.deepcopy(exported)
    cleaned.pop("approved", None)
    cleaned.pop("approval_status", None)
    report = validate_spec_data(cleaned)
    assert report.valid is True
