"""
Admin script to create an invite-only teacher account and print an expiring invite token (P6-T3).

Usage:
    python scripts/create_teacher.py --email teacher@school.edu --name "Prof. Rao" --ttl-minutes 60
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import db as db_mod  # noqa: E402
from app.classroom.teachers import create_teacher_invite  # noqa: E402


async def _run(email: str, name: str, ttl_minutes: int) -> dict[str, str]:
    await db_mod.init_db()
    try:
        return await create_teacher_invite(
            db_mod.database,
            email=email,
            display_name=name,
            ttl_minutes=ttl_minutes,
        )
    finally:
        await db_mod.close_db()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create an invite-only teacher account and expiring token.")
    parser.add_argument("--email", required=True, help="Teacher email address")
    parser.add_argument("--name", required=True, help="Teacher display name")
    parser.add_argument("--ttl-minutes", type=int, default=60, help="Invite token TTL in minutes (default: 60)")
    args = parser.parse_args(argv)

    result = asyncio.run(_run(args.email, args.name, args.ttl_minutes))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
