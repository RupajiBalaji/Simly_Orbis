"""
Laboratory interaction API routes (/api/lab).

Provides endpoints for experiment catalog, interactive session lifecycles,
context-aware available actions, action execution, and final reports.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any
import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app import db as _db
from app.lab.engine import apply_action, create_session, get_available_actions
from app.lab.experiments import get_experiment, list_experiments
from app.lab.models import (
    ActionRequest,
    ActionResult,
    AvailableAction,
    LabSession,
    Violation,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/lab", tags=["lab"])


class CreateSessionRequest(BaseModel):
    """Payload to initialize a new laboratory session."""

    experiment_id: str = Field(..., description="Target experiment ID ('pk_ward' or 'titration_bench')")
    nickname: str = Field(default="Researcher", description="Player or researcher nickname")


class LabReportResponse(BaseModel):
    """Structured report returned upon finishing a lab session."""

    report_id: str
    session_id: str
    experiment_id: str
    nickname: str
    score: int
    score_breakdown: dict[str, int]
    grade: str
    violations: list[Violation]
    lessons_learned: list[str]
    created_at: str


class LabLeaderboardEntry(BaseModel):
    """Leaderboard entry for laboratory experiments."""

    rank: int
    nickname: str
    experiment_id: str
    score: int
    grade: str
    created_at: str


# ---------------------------------------------------------------------------
# Experiments Catalog
# ---------------------------------------------------------------------------

@router.get("/experiments", summary="List all lab experiments")
async def get_experiments() -> list[dict[str, Any]]:
    """Return all available laboratory experiments."""
    return [exp.model_dump() for exp in list_experiments()]


@router.get("/experiments/{experiment_id}", summary="Get lab experiment details")
async def get_experiment_by_id(experiment_id: str) -> dict[str, Any]:
    """Return experiment definition including apparatus, inventory, and protocol."""
    try:
        exp = get_experiment(experiment_id)
        return exp.model_dump()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.") from exc


# ---------------------------------------------------------------------------
# Session Lifecycle
# ---------------------------------------------------------------------------

@router.post("/sessions", summary="Start a new lab session", status_code=201)
async def start_session(body: CreateSessionRequest) -> dict[str, Any]:
    """Initialize a stateful lab session and persist to database."""
    try:
        get_experiment(body.experiment_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Experiment '{body.experiment_id}' not found.") from exc

    session = create_session(body.experiment_id, body.nickname)
    session_dict = session.model_dump()
    await _db.upsert_lab_session(session_dict)
    return session_dict


@router.get("/sessions/{session_id}", summary="Get lab session state")
async def get_session(session_id: str) -> dict[str, Any]:
    """Retrieve current session state."""
    doc = await _db.get_lab_session(session_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Lab session '{session_id}' not found.")
    return doc


@router.get("/sessions/{session_id}/available-actions", response_model=list[AvailableAction], summary="Context-aware actions")
async def available_actions(session_id: str) -> list[AvailableAction]:
    """Return enabled and disabled actions with targets and explanations."""
    doc = await _db.get_lab_session(session_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Lab session '{session_id}' not found.")
    session = LabSession(**doc)
    return get_available_actions(session)


@router.post("/sessions/{session_id}/actions", response_model=ActionResult, summary="Execute a lab action")
async def execute_action(session_id: str, body: ActionRequest) -> ActionResult:
    """Apply an action to the lab session, advance physical state, and log execution."""
    doc = await _db.get_lab_session(session_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Lab session '{session_id}' not found.")

    session = LabSession(**doc)
    result = apply_action(session, body)

    # Persist updated session
    await _db.upsert_lab_session(session.model_dump())
    return result


@router.post("/sessions/{session_id}/finish", response_model=LabReportResponse, summary="Finish session and compile report")
async def finish_session(session_id: str) -> LabReportResponse:
    """Complete lab session, calculate final scores, assign grade, and persist report."""
    doc = await _db.get_lab_session(session_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Lab session '{session_id}' not found.")

    session = LabSession(**doc)
    session.status = "completed"

    # Compute final score
    score_breakdown = session.score_parts
    total_score = max(0, min(100, sum(score_breakdown.values())))

    if total_score >= 85:
        grade = "A"
    elif total_score >= 70:
        grade = "B"
    elif total_score >= 50:
        grade = "C"
    else:
        grade = "D"

    # Lessons learned generator
    lessons: list[str] = []
    if session.violations:
        for v in session.violations:
            lessons.append(f"Safety: {v.title} – {v.explanation}")
    else:
        lessons.append("Safety: Flawless PPE and contamination protocol adherence.")

    if session.experiment_id == "pk_ward":
        lessons.append("Pharmacokinetics: Oral drug peak concentration depends on absorption rate ka vs clearance ke.")
    elif session.experiment_id == "titration_bench":
        lessons.append("Titration: Stoichiometric equivalence point occurs when moles of base equal moles of acid.")

    report_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    report_doc = {
        "report_id": report_id,
        "session_id": session_id,
        "experiment_id": session.experiment_id,
        "nickname": session.nickname,
        "score": total_score,
        "score_breakdown": score_breakdown,
        "grade": grade,
        "violations": [v.model_dump() for v in session.violations],
        "lessons_learned": lessons,
        "created_at": now_iso,
    }

    await _db.save_lab_report(report_doc)
    await _db.upsert_lab_session(session.model_dump())

    return LabReportResponse(**report_doc)


@router.get("/leaderboard", response_model=list[LabLeaderboardEntry], summary="Lab experiment leaderboard")
async def get_lab_leaderboard(
    experiment_id: str = Query(..., description="Experiment ID to filter leaderboard"),
) -> list[LabLeaderboardEntry]:
    """Retrieve top-10 finished experiment sessions."""
    docs = await _db.list_lab_leaderboard(experiment_id, limit=10)
    entries: list[LabLeaderboardEntry] = []
    for i, d in enumerate(docs):
        entries.append(
            LabLeaderboardEntry(
                rank=i + 1,
                nickname=d.get("nickname", "Anonymous"),
                experiment_id=d.get("experiment_id", experiment_id),
                score=d.get("score", 0),
                grade=d.get("grade", "C"),
                created_at=d.get("created_at", ""),
            )
        )
    return entries
