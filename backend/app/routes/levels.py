"""GET /api/levels – return the level catalogue from levels.json."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api/levels", tags=["levels"])

_LEVELS_JSON = Path(__file__).parent.parent / "sim" / "levels.json"
_LEVELS: list[dict] = json.loads(_LEVELS_JSON.read_text(encoding="utf-8"))


@router.get("", summary="List all levels")
async def list_levels() -> list[dict]:
    """Return every level definition (lock state is managed client-side from saved scores)."""
    return _LEVELS
