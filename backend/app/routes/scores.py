"""
POST /api/score   – save a score and upsert the player record
GET  /api/leaderboard?level_id=  – top-10 scores for a level
"""

from __future__ import annotations

import datetime

import pymongo
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import app.db as _db

router = APIRouter(tags=["scores"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ScoreRequest(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=32, description="Player nickname")
    level_id: str = Field(..., min_length=1, max_length=64, description="Level identifier")
    score: int = Field(..., ge=0, description="Numeric score achieved")
    stars: int = Field(..., ge=0, le=3, description="Stars awarded (0–3)")


class ScoreEntry(BaseModel):
    nickname: str
    level_id: str
    score: int
    stars: int
    saved_at: str


class LeaderboardEntry(BaseModel):
    rank: int
    nickname: str
    score: int
    stars: int
    is_sample: bool = False



# ---------------------------------------------------------------------------
# POST /api/score
# ---------------------------------------------------------------------------

@router.post("/api/score", response_model=ScoreEntry, status_code=201, summary="Save a score")
async def save_score(body: ScoreRequest) -> ScoreEntry:
    """
    Persist a score document and upsert the player record.

    - Inserts a new document in the **scores** collection.
    - Upserts the **players** collection: sets ``last_seen`` and increments
      nothing (keep it simple – a richer stats system can extend this later).
    """
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    score_doc = {
        "nickname": body.nickname,
        "level_id": body.level_id,
        "score": body.score,
        "stars": body.stars,
        "saved_at": now,
    }

    try:
        await _db.database["scores"].insert_one(score_doc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save score: {exc}") from exc

    # Upsert player: create if absent, update last_seen
    try:
        await _db.database["players"].update_one(
            {"nickname": body.nickname},
            {
                "$set": {"last_seen": now},
                "$setOnInsert": {"nickname": body.nickname, "joined_at": now},
            },
            upsert=True,
        )
    except Exception as exc:
        import logging  # noqa: PLC0415
        logging.getLogger(__name__).warning("Player upsert failed: %s", exc)

    return ScoreEntry(**score_doc)


# ---------------------------------------------------------------------------
# GET /api/leaderboard
# ---------------------------------------------------------------------------

@router.get(
    "/api/leaderboard",
    response_model=list[LeaderboardEntry],
    summary="Top-10 leaderboard for a level",
)
async def leaderboard(
    level_id: str = Query(..., description="Level identifier to query"),
) -> list[LeaderboardEntry]:
    """Return the top-10 scores for *level_id*, sorted by score descending."""
    try:
        docs = await _db.database["scores"].find(
            {"level_id": level_id},
            sort=[("score", pymongo.DESCENDING)],
            limit=10,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Leaderboard query failed: {exc}") from exc

    return [
        LeaderboardEntry(
            rank=i + 1,
            nickname=doc["nickname"],
            score=doc["score"],
            stars=doc["stars"],
            is_sample=doc.get("is_sample", False),
        )
        for i, doc in enumerate(docs)
    ]

