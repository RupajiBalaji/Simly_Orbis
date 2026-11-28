"""CLI runner for the configurable data retention purge job (P6-T6)."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import db as db_mod  # noqa: E402
from app.classroom.retention import purge_expired_guest_sessions  # noqa: E402


async def _run() -> dict[str, int]:
    await db_mod.init_db()
    try:
        return await purge_expired_guest_sessions(db_mod.database)
    finally:
        await db_mod.close_db()


def main() -> int:
    res = asyncio.run(_run())
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
