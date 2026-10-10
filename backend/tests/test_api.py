"""
httpx integration tests for the Simly Orbis API.

Uses the in-memory storage fallback (no MONGODB_URI required).
Run with:  pytest tests/test_api.py -v
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# /api/health
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["storage_mode"] in ("memory", "mongodb")
    assert "players" in body["collections"]
    assert "scores" in body["collections"]
    assert "runs" in body["collections"]
    assert "pharma.pk" in body["modules"]



# ---------------------------------------------------------------------------
# /api/drugs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_drugs(client: AsyncClient):
    r = await client.get("/api/drugs")
    assert r.status_code == 200
    drugs = r.json()
    assert isinstance(drugs, list)
    assert len(drugs) == 3

    ids = {d["id"] for d in drugs}
    assert ids == {"paracetamol", "ibuprofen", "caffeine"}

    for drug in drugs:
        assert drug["ka"] > 0
        assert drug["half_life"] > 0
        assert 0 < drug["bioavailability"] <= 1.0
        assert drug["green_low"] < drug["green_high"] < drug["red_threshold"]


# ---------------------------------------------------------------------------
# /api/simulate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_simulate_paracetamol(client: AsyncClient):
    payload = {
        "drug_id": "paracetamol",
        "weight_kg": 70,
        "clearance_multiplier": 1.0,
        "dose_mg": 500,
        "n_doses": 1,
        "interval_h": 6,
    }
    r = await client.post("/api/simulate", json=payload)
    assert r.status_code == 200
    body = r.json()

    assert body["drug_id"] == "paracetamol"
    assert len(body["times"]) == 241        # 0–24h in 0.1h steps
    assert len(body["concentrations"]) == 241
    assert body["concentrations"][0] == pytest.approx(0.0, abs=1e-12)
    assert body["peak_concentration"] > 0
    total_pct = body["pct_green"] + body["pct_below_green"] + body["pct_red"]
    assert total_pct == pytest.approx(100.0, abs=1e-6)


@pytest.mark.asyncio
async def test_simulate_unknown_drug(client: AsyncClient):
    r = await client.post("/api/simulate", json={
        "drug_id": "unicorn",
        "weight_kg": 70,
        "dose_mg": 100,
        "n_doses": 1,
        "interval_h": 6,
    })
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_simulate_validation_n_doses_out_of_range(client: AsyncClient):
    r = await client.post("/api/simulate", json={
        "drug_id": "caffeine",
        "weight_kg": 70,
        "dose_mg": 100,
        "n_doses": 10,   # > 6, should be rejected
        "interval_h": 6,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_simulate_reduced_clearance(client: AsyncClient):
    """Reduced clearance (multiplier < 1) should raise peak concentration."""
    base = {
        "drug_id": "caffeine",
        "weight_kg": 70,
        "dose_mg": 100,
        "n_doses": 1,
        "interval_h": 6,
    }
    normal = (await client.post("/api/simulate", json={**base, "clearance_multiplier": 1.0})).json()
    reduced = (await client.post("/api/simulate", json={**base, "clearance_multiplier": 0.5})).json()

    # With slower elimination, AUC is higher but peak depends on timing;
    # the reduced-clearance curve should have a higher peak for a single dose.
    assert reduced["peak_concentration"] > normal["peak_concentration"]


# ---------------------------------------------------------------------------
# /api/score  and  /api/leaderboard
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_save_score_and_leaderboard(client: AsyncClient):
    level = "level-pk-01"

    # Save three scores
    scores_to_post = [
        {"nickname": "Alice", "level_id": level, "score": 900, "stars": 3},
        {"nickname": "Bob",   "level_id": level, "score": 750, "stars": 2},
        {"nickname": "Carol", "level_id": level, "score": 500, "stars": 1},
    ]
    for payload in scores_to_post:
        r = await client.post("/api/score", json=payload)
        assert r.status_code == 201
        body = r.json()
        assert body["nickname"] == payload["nickname"]
        assert body["score"] == payload["score"]
        assert "saved_at" in body

    # Leaderboard should return them ranked by score descending
    r = await client.get("/api/leaderboard", params={"level_id": level})
    assert r.status_code == 200
    board = r.json()
    assert len(board) == 3
    assert board[0]["nickname"] == "Alice"
    assert board[0]["rank"] == 1
    assert board[1]["nickname"] == "Bob"
    assert board[2]["nickname"] == "Carol"


@pytest.mark.asyncio
async def test_leaderboard_top10_cap(client: AsyncClient):
    """More than 10 entries → only top 10 returned."""
    level = "level-cap-test"
    for i in range(15):
        await client.post("/api/score", json={
            "nickname": f"Player{i:02d}",
            "level_id": level,
            "score": i * 10,
            "stars": 1,
        })

    r = await client.get("/api/leaderboard", params={"level_id": level})
    assert r.status_code == 200
    assert len(r.json()) == 10


@pytest.mark.asyncio
async def test_leaderboard_missing_level_id(client: AsyncClient):
    """level_id is required."""
    r = await client.get("/api/leaderboard")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_save_score_invalid_stars(client: AsyncClient):
    r = await client.post("/api/score", json={
        "nickname": "Cheater",
        "level_id": "level-x",
        "score": 9999,
        "stars": 5,   # max is 3
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_health_counts_after_scores(client: AsyncClient):
    """Health endpoint document counts reflect saved data."""
    # Save a score so both collections are non-empty
    await client.post("/api/score", json={
        "nickname": "HealthTest",
        "level_id": "level-health",
        "score": 100,
        "stars": 1,
    })
    r = await client.get("/api/health")
    body = r.json()
    assert body["collections"]["scores"] >= 1
    assert body["collections"]["players"] >= 1


# ---------------------------------------------------------------------------
# /api/tutor
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tutor_feedback_template_fallback(client: AsyncClient):
    """When ANTHROPIC_API_KEY is unset or invalid, returns 200 with template response."""
    payload = {
        "drug_name": "Paracetamol",
        "dose_mg": 500,
        "n_doses": 1,
        "interval_h": 6,
        "weight_kg": 70,
        "clearance_multiplier": 1.0,
        "peak_concentration": 6.8,
        "time_of_peak": 1.2,
        "pct_green": 65.0,
        "pct_red": 0.0,
        "score": 65,
    }
    r = await client.post("/api/tutor", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "message" in body
    assert len(body["message"]) > 0
    assert body["source"] in ("fallback", "ai")
    if body["source"] == "fallback":
        assert body["fallback_reason"] in ("no_api_key", "api_error")
        assert "Paracetamol" in body["message"]


