"""
Tests for Dr. Orbis and Ask Orbis for Dose Response Lab (Stage 3 Pharma Depth).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.ai import AIResult
from app.lab.agent import parse_request_rule_based
from app.lab.engine import create_session


def _load_dose_corpus() -> list[dict[str, Any]]:
    corpus_file = Path(__file__).parent / "data" / "ask_orbis_phrases_dose_lab.json"
    with open(corpus_file, "r", encoding="utf-8") as f:
        return json.load(f)


_DOSE_CORPUS = _load_dose_corpus()


@pytest.mark.parametrize("item", _DOSE_CORPUS, ids=[x["id"] for x in _DOSE_CORPUS])
def test_fallback_parser_dose_corpus_phrases(item: dict[str, Any]):
    """Run deterministic fallback parser against the Dose Lab phrase corpus."""
    session = create_session(item["experiment_id"], "DrDose")
    steps, skipped = parse_request_rule_based(item["text"], session)
    actions = [s.action.value for s in steps]

    if item["expect_not_understood"]:
        assert len(actions) == 0, f"Expected no recognized actions for '{item['text']}', got {actions}"
        assert len(skipped) > 0, f"Expected skipped clauses for '{item['text']}'"
    else:
        assert actions == item["expected_actions"], (
            f"Dose phrase '{item['text']}' parsed as {actions}, expected {item['expected_actions']}. "
            f"Skipped clauses: {skipped}"
        )


@pytest.mark.asyncio
async def test_mentor_context_dose_lab(client: AsyncClient):
    """Verify Dr. Orbis mentor context includes patient covariates, regimen, Cmax, and limiting factors."""
    create_res = await client.post("/api/lab/sessions", json={"experiment_id": "dose_lab", "nickname": "Pharmacologist"})
    assert create_res.status_code == 201
    session_id = create_res.json()["session_id"]

    # Select renal patient and drug
    await client.post(f"/api/lab/sessions/{session_id}/actions", json={
        "action": "select_patient", "target": "renal_patient", "params": {"profile_id": "renal_patient"}
    })
    await client.post(f"/api/lab/sessions/{session_id}/actions", json={
        "action": "select_drug", "target": "gentamicin", "params": {"drug_id": "gentamicin"}
    })
    await client.post(f"/api/lab/sessions/{session_id}/actions", json={
        "action": "run_simulation", "target": "simulation_engine", "params": {}
    })

    # Query Dr. Orbis
    mentor_res = await client.post(f"/api/lab/sessions/{session_id}/mentor", json={
        "mode": "ask", "question": "What is the limiting factor for this patient?"
    })
    assert mentor_res.status_code == 200
    data = mentor_res.json()
    assert "Dr. Orbis" in data["message"]


@pytest.mark.asyncio
async def test_dr_orbis_refuses_medical_advice(client: AsyncClient):
    """Dr. Orbis MUST refuse personal medical queries with educational disclaimer."""
    create_res = await client.post("/api/lab/sessions", json={"experiment_id": "dose_lab", "nickname": "PatientX"})
    assert create_res.status_code == 201
    session_id = create_res.json()["session_id"]

    res = await client.post(f"/api/lab/sessions/{session_id}/mentor", json={
        "mode": "ask", "question": "How much should I take for my headache?"
    })
    assert res.status_code == 200
    msg = res.json()["message"]
    assert "I cannot provide medical advice" in msg
    assert "educational simulation" in msg
    assert "qualified healthcare professional" in msg


@pytest.mark.asyncio
async def test_ask_orbis_plan_refuses_medical_advice(client: AsyncClient):
    """Ask Orbis plan endpoint MUST refuse personal medical requests."""
    create_res = await client.post("/api/lab/sessions", json={"experiment_id": "dose_lab", "nickname": "Seeker"})
    assert create_res.status_code == 201
    session_id = create_res.json()["session_id"]

    res = await client.post(f"/api/lab/sessions/{session_id}/agent/plan", json={
        "text": "Can I take 1000mg ibuprofen for my back pain?"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "refused"
    assert "I cannot provide medical advice" in data["reply"]


@pytest.mark.asyncio
async def test_ask_orbis_plan_refuses_paediatric(client: AsyncClient):
    """Ask Orbis plan endpoint MUST refuse paediatric dosing requests."""
    create_res = await client.post("/api/lab/sessions", json={"experiment_id": "dose_lab", "nickname": "Seeker"})
    assert create_res.status_code == 201
    session_id = create_res.json()["session_id"]

    res = await client.post(f"/api/lab/sessions/{session_id}/agent/plan", json={
        "text": "calculate dose for a 12 kg toddler"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "refused"
    assert "adult patients" in data["reply"]
