"""
Configurable data retention & purge job (P6-T6, Section 13.4).
Purges guest lab sessions older than GUEST_SESSION_RETENTION_DAYS (default 90)
and expired tokens/student sessions, while preserving class data until teacher deletion.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import settings


async def purge_expired_guest_sessions(
    db: Any,
    retention_days: int | None = None,
    now: datetime | None = None,
) -> dict[str, int]:
    """Purge guest sessions older than retention_days and expired tokens."""
    days = retention_days if retention_days is not None else settings.guest_session_retention_days
    ref_now = now or datetime.now(timezone.utc)
    cutoff_iso = (ref_now - timedelta(days=days)).isoformat()
    now_iso = ref_now.isoformat()

    # Only purge guest lab_sessions (those without a class_id) older than cutoff
    all_sessions = await db["lab_sessions"].find({})
    expired_guest_ids = [
        s["session_id"]
        for s in all_sessions
        if not s.get("class_id") and (s.get("created_at") or "") < cutoff_iso
    ]
    purged_sessions = 0
    if expired_guest_ids:
        purged_sessions = await db["lab_sessions"].delete_many({"session_id": {"$in": expired_guest_ids}})

    purged_student_tokens = await db["student_sessions"].delete_many({"expires_at": {"$lt": now_iso}})
    purged_teacher_tokens = await db["teacher_tokens"].delete_many({"expires_at": {"$lt": now_iso}})

    return {
        "purged_guest_sessions": purged_sessions,
        "purged_student_tokens": purged_student_tokens,
        "purged_teacher_tokens": purged_teacher_tokens,
    }
