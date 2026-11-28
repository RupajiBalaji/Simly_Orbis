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


@pytest.mark.asyncio
async def test_validate_endpoint_oversize_payload_rejected_413(client: AsyncClient, sample_spec_data: dict):
    """Payloads exceeding 512KB must be rejected with 413 Payload Too Large."""
    # Generate large payload (> 512KB)
    large_data = copy.deepcopy(sample_spec_data)
    large_data["equipment"] = ["large_item_" + ("x" * 1000) for _ in range(600)]
    body_str = json.dumps({"spec_data": large_data})
    assert len(body_str.encode("utf-8")) > 512 * 1024

    res = await client.post(
        "/api/specs/validate",
        content=body_str,
        headers={"content-type": "application/json", "content-length": str(len(body_str.encode("utf-8")))},
    )
    assert res.status_code == 413
    assert "Payload exceeds maximum limit" in res.json()["detail"]


@pytest.mark.asyncio
async def test_validate_endpoint_malformed_json_rejected_400(client: AsyncClient):
    """Malformed non-JSON payloads must be rejected with 400 Bad Request."""
    res = await client.post(
        "/api/specs/validate",
        content=b"{bad json, not closed...",
        headers={"content-type": "application/json"},
    )
    assert res.status_code == 400
    assert "Malformed JSON" in res.json()["detail"]


@pytest.mark.asyncio
async def test_validate_endpoint_hostile_input_rejected_400(client: AsyncClient, sample_spec_data: dict):
    """Hostile prototype injection or non-dict payloads must be rejected with 400 Bad Request."""
    # 1. Non-dict spec_data
    res1 = await client.post("/api/specs/validate", json={"spec_data": "not_a_dict"})
    assert res1.status_code == 400

    # 2. Hostile __proto__ key
    hostile_data = copy.deepcopy(sample_spec_data)
    hostile_data["__proto__"] = {"admin": True}
    res2 = await client.post("/api/specs/validate", json={"spec_data": hostile_data})
    assert res2.status_code == 400
    assert "Hostile payload property detected" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_validate_endpoint_rate_limit_429(client: AsyncClient, sample_spec_data: dict):
    """Enforce sliding-window rate limit: exceeding 60 requests/minute triggers 429."""
    from app.routes import specs
    # Artificially fill rate limit bucket for client socket IP (AsyncClient uses 127.0.0.1)
    client_ip = "127.0.0.1"
    now = specs.time.time()
    specs._IP_TIMESTAMPS[client_ip] = [now] * 65

    res = await client.post(
        "/api/specs/validate",
        json={"spec_data": sample_spec_data},
    )
    assert res.status_code == 429
    assert "Rate limit exceeded" in res.json()["detail"]
    # Clear bucket after test
    specs._IP_TIMESTAMPS.clear()


@pytest.mark.asyncio
async def test_validate_spoofed_xff_with_trust_proxy_off_gets_no_new_bucket(
    client: AsyncClient, sample_spec_data: dict, monkeypatch: pytest.MonkeyPatch
):
    """Spoofed X-Forwarded-For with TRUST_PROXY off must NOT create a new bucket; 61st call returns 429."""
    from app.routes import specs

    monkeypatch.setenv("TRUST_PROXY", "false")
    specs._IP_TIMESTAMPS.clear()
    try:
        for i in range(60):
            res = await client.post(
                "/api/specs/validate",
                json={"spec_data": sample_spec_data},
                headers={"x-forwarded-for": f"10.0.0.{i + 1}"},
            )
            assert res.status_code == 200, f"Unexpected status at call {i + 1}: {res.status_code}"

        # 61st call with another spoofed XFF still hits the same client bucket and returns 429
        res61 = await client.post(
            "/api/specs/validate",
            json={"spec_data": sample_spec_data},
            headers={"x-forwarded-for": "203.0.113.99"},
        )
        assert res61.status_code == 429
    finally:
        specs._IP_TIMESTAMPS.clear()


@pytest.mark.asyncio
async def test_validate_trust_proxy_on_uses_last_hop(
    client: AsyncClient, sample_spec_data: dict, monkeypatch: pytest.MonkeyPatch
):
    """With TRUST_PROXY on, the LAST hop in X-Forwarded-For is used as the rate-limit bucket."""
    from app.routes import specs

    monkeypatch.setenv("TRUST_PROXY", "true")
    specs._IP_TIMESTAMPS.clear()
    try:
        # Exhaust bucket for last-hop 198.51.100.77 using varying spoofed first hops
        for i in range(60):
            res = await client.post(
                "/api/specs/validate",
                json={"spec_data": sample_spec_data},
                headers={"x-forwarded-for": f"10.0.0.{i + 1}, 198.51.100.77"},
            )
            assert res.status_code == 200

        # 61st call with same last hop returns 429
        res61 = await client.post(
            "/api/specs/validate",
            json={"spec_data": sample_spec_data},
            headers={"x-forwarded-for": "172.16.0.5, 198.51.100.77"},
        )
        assert res61.status_code == 429

        # Different last hop still has its own fresh bucket
        res_other = await client.post(
            "/api/specs/validate",
            json={"spec_data": sample_spec_data},
            headers={"x-forwarded-for": "10.0.0.1, 198.51.100.88"},
        )
        assert res_other.status_code == 200
    finally:
        specs._IP_TIMESTAMPS.clear()


@pytest.mark.asyncio
async def test_validate_with_inline_dry_run_actions(client: AsyncClient, sample_spec_data: dict):
    """Validation payload with scripted dry_run_actions executes dry run in-memory."""
    actions = [
        {"action": "wear_ppe", "target": "avatar", "params": {"item": "all"}},
        {"action": "rinse_burette", "target": "burette", "params": {"solvent": "naoh"}},
    ]
    res = await client.post(
        "/api/specs/validate",
        json={"spec_data": sample_spec_data, "dry_run_actions": actions},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["dry_run"] is not None
    assert data["dry_run"]["success"] is True
    assert data["dry_run"]["total_steps_executed"] == 2


def test_unapproved_spec_never_served_to_students():
    """Unapproved specs are strictly excluded from public experiment listing."""
    from app.config import settings
    from app.lab.experiments import list_experiments

    original = settings.spec_runtime
    try:
        settings.spec_runtime = True
        public_exps = list_experiments(include_all=True)
        # All public experiments must be approved
        for exp in public_exps:
            assert getattr(exp, "approved", True) is True
    finally:
        settings.spec_runtime = original

