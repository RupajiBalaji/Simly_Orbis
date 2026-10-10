"""
Unit and integration tests for Core Simulation Modules, Registry, Reality Checks, and Runs.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.base import SimModule
from app.core.registry import get_module, list_modules, register
from app.modules.pharma_pk import PharmaPKModule, PharmaPKParams


# ---------------------------------------------------------------------------
# Module Registry Tests
# ---------------------------------------------------------------------------

def test_module_registry_list_and_get():
    pharma = PharmaPKModule()
    register(pharma)
    modules = list_modules()
    assert any(m.id == "pharma.pk" for m in modules)

    retrieved = get_module("pharma.pk")
    assert retrieved.id == "pharma.pk"
    assert retrieved.district == "pharma"
    assert retrieved.version == "1.0.0"


def test_module_registry_unknown_raises():
    with pytest.raises(KeyError, match="Unknown simulation module 'quantum.teleport'"):
        get_module("quantum.teleport")


def test_pharma_pk_reality_checks():
    pharma = PharmaPKModule()
    checks = pharma.reality_checks()
    assert len(checks) == 3

    names = {c.name for c in checks}
    assert names == {"Analytic tmax", "Terminal half-life", "Dose proportionality"}

    for c in checks:
        assert c.passed is True, f"Reality check '{c.name}' failed: expected {c.expected}, got {c.actual}"
        assert c.source_note != ""


# ---------------------------------------------------------------------------
# API Endpoints: /api/modules
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_modules_endpoint(client: AsyncClient):
    r = await client.get("/api/modules")
    assert r.status_code == 200
    modules = r.json()
    assert isinstance(modules, list)
    assert any(m["id"] == "pharma.pk" for m in modules)


@pytest.mark.asyncio
async def test_get_module_schema_endpoint(client: AsyncClient):
    r = await client.get("/api/modules/pharma.pk")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "pharma.pk"
    assert "params_schema" in data
    assert "properties" in data["params_schema"]
    assert "drug_id" in data["params_schema"]["properties"]


@pytest.mark.asyncio
async def test_get_module_schema_unknown_404(client: AsyncClient):
    r = await client.get("/api/modules/nonexistent.module")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_module_reality_checks_endpoint(client: AsyncClient):
    r = await client.get("/api/modules/pharma.pk/reality-check")
    assert r.status_code == 200
    checks = r.json()
    assert len(checks) == 3
    assert all(c["passed"] is True for c in checks)


# ---------------------------------------------------------------------------
# API Endpoints: POST /api/run & GET /api/runs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_module_happy_path(client: AsyncClient):
    payload = {
        "module_id": "pharma.pk",
        "params": {
            "drug_id": "paracetamol",
            "weight_kg": 70,
            "clearance_multiplier": 1.0,
            "dose_mg": 500,
            "n_doses": 1,
            "interval_h": 6,
        },
        "nickname": "TestScientist",
    }
    r = await client.post("/api/run", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "run_id" in data
    assert "result" in data
    res = data["result"]
    assert res["module_id"] == "pharma.pk"
    assert "summary" in res
    assert "peak_concentration" in res["summary"]
    assert "series" in res
    assert "time_h" in res["series"]

    run_id = data["run_id"]

    # Verify retrieval by run_id
    r_get = await client.get(f"/api/runs/{run_id}")
    assert r_get.status_code == 200
    run_rec = r_get.json()
    assert run_rec["run_id"] == run_id
    assert run_rec["module_id"] == "pharma.pk"
    assert run_rec["district"] == "pharma"
    assert run_rec["nickname"] == "TestScientist"
    assert run_rec["engine_version"] == "0.1.0"
    assert "created_at" in run_rec
    assert "storage_mode" in run_rec


@pytest.mark.asyncio
async def test_run_module_invalid_params_422(client: AsyncClient):
    payload = {
        "module_id": "pharma.pk",
        "params": {
            "drug_id": "paracetamol",
            "weight_kg": -10,  # Invalid: must be >= 10
            "dose_mg": 500,
        },
    }
    r = await client.post("/api/run", json=payload)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_run_module_unknown_404(client: AsyncClient):
    payload = {
        "module_id": "chemistry.reactor",
        "params": {"temperature": 300},
    }
    r = await client.post("/api/run", json=payload)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_runs_filtering_and_limits(client: AsyncClient):
    # Execute a run
    payload = {
        "module_id": "pharma.pk",
        "params": {
            "drug_id": "caffeine",
            "weight_kg": 65,
            "clearance_multiplier": 1.0,
            "dose_mg": 100,
            "n_doses": 1,
            "interval_h": 6,
        },
        "nickname": "NightNurse",
    }
    await client.post("/api/run", json=payload)

    r = await client.get("/api/runs", params={"limit": 10, "module_id": "pharma.pk"})
    assert r.status_code == 200
    runs = r.json()
    assert isinstance(runs, list)
    assert len(runs) >= 1
    assert runs[0]["module_id"] == "pharma.pk"
