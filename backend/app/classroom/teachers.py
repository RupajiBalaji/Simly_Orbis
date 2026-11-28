"""
Invite-only teacher account management & token verification (P6-T3, 13.1, 13.6).
"""

from __future__ import annotations

import re
import uuid
from typing import Any

from app.classroom.models import TeacherRecord, TeacherTokenRecord, utc_now_iso
from app.classroom.security import (
    constant_time_equals,
    expiry_iso,
    generate_token,
    hash_secret,
    is_expired,
)
from app.config import settings

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


async def create_teacher_invite(
    db: Any,
    email: str,
    display_name: str,
    ttl_minutes: int | None = None,
) -> dict[str, str]:
    """
    Create or look up an invite-only teacher account and issue a single-use
    expiring invite token.
    """
    clean_email = (email or "").strip().lower()
    if not _EMAIL_RE.match(clean_email):
        raise ValueError("Invalid teacher email address.")
    clean_name = (display_name or "").strip() or clean_email.split("@")[0]

    teachers_col = db["teachers"]
    existing = await teachers_col.find_one({"email": clean_email})
    if existing:
        teacher_id = existing["teacher_id"]
        if clean_name and existing.get("display_name") != clean_name:
            await teachers_col.update_one({"teacher_id": teacher_id}, {"$set": {"display_name": clean_name}})
    else:
        teacher_id = f"tch-{uuid.uuid4().hex[:12]}"
        rec = TeacherRecord(
            teacher_id=teacher_id,
            email=clean_email,
            display_name=clean_name,
            active=True,
            created_at=utc_now_iso(),
        )
        await teachers_col.insert_one(rec.model_dump())

    raw_invite = generate_token()
    ttl = ttl_minutes if ttl_minutes is not None else settings.teacher_invite_ttl_minutes
    expires_at = expiry_iso(minutes=ttl)
    tok = TeacherTokenRecord(
        token_id=f"tok-{uuid.uuid4().hex[:12]}",
        token_hash=hash_secret(raw_invite),
        teacher_id=teacher_id,
        token_type="invite",
        expires_at=expires_at,
        used_at=None,
        created_at=utc_now_iso(),
    )
    await db["teacher_tokens"].insert_one(tok.model_dump())

    return {
        "teacher_id": teacher_id,
        "email": clean_email,
        "display_name": clean_name,
        "invite_token": raw_invite,
        "expires_at": expires_at,
    }


async def redeem_teacher_invite(
    db: Any,
    raw_token: str,
    session_ttl_hours: int | None = None,
) -> dict[str, str] | None:
    """
    Redeem a single-use, non-expired teacher invite token for a session token.
    Returns None if token is invalid, expired, or already used.
    """
    if not raw_token or not isinstance(raw_token, str):
        return None
    target_hash = hash_secret(raw_token.strip())
    tokens_col = db["teacher_tokens"]
    invite_tokens = await tokens_col.find({"token_type": "invite"})

    matched = None
    for doc in invite_tokens:
        stored_hash = doc.get("token_hash", "")
        if stored_hash and constant_time_equals(stored_hash, target_hash):
            matched = doc
            break

    if not matched:
        return None
    if matched.get("used_at") is not None:
        return None
    if is_expired(matched.get("expires_at")):
        return None

    teacher = await db["teachers"].find_one({"teacher_id": matched["teacher_id"]})
    if not teacher or not teacher.get("active", True):
        return None

    # Mark invite token as used immediately to prevent reuse
    await tokens_col.update_one(
        {"token_id": matched["token_id"]},
        {"$set": {"used_at": utc_now_iso()}},
    )

    raw_session = generate_token()
    ttl_h = session_ttl_hours if session_ttl_hours is not None else settings.teacher_session_ttl_hours
    expires_at = expiry_iso(hours=ttl_h)
    sess_rec = TeacherTokenRecord(
        token_id=f"tok-{uuid.uuid4().hex[:12]}",
        token_hash=hash_secret(raw_session),
        teacher_id=teacher["teacher_id"],
        token_type="session",
        expires_at=expires_at,
        used_at=None,
        created_at=utc_now_iso(),
    )
    await tokens_col.insert_one(sess_rec.model_dump())

    return {
        "teacher_id": teacher["teacher_id"],
        "email": teacher["email"],
        "display_name": teacher["display_name"],
        "session_token": raw_session,
        "expires_at": expires_at,
    }


async def verify_teacher_session(db: Any, raw_token: str) -> dict[str, Any] | None:
    """Verify a teacher bearer session token using constant-time comparison."""
    if not raw_token:
        return None
    target_hash = hash_secret(raw_token.strip())
    session_tokens = await db["teacher_tokens"].find({"token_type": "session"})
    matched = None
    for doc in session_tokens:
        stored_hash = doc.get("token_hash", "")
        if stored_hash and constant_time_equals(stored_hash, target_hash):
            matched = doc
            break
    if not matched or is_expired(matched.get("expires_at")):
        return None
    teacher = await db["teachers"].find_one({"teacher_id": matched["teacher_id"]})
    if not teacher or not teacher.get("active", True):
        return None
    return teacher


async def verify_student_session(db: Any, raw_token: str) -> dict[str, Any] | None:
    """Verify a student bearer session token using constant-time comparison."""
    if not raw_token:
        return None
    target_hash = hash_secret(raw_token.strip())
    sessions = await db["student_sessions"].find({})
    matched = None
    for doc in sessions:
        stored_hash = doc.get("token_hash", "")
        if stored_hash and constant_time_equals(stored_hash, target_hash):
            matched = doc
            break
    if not matched or is_expired(matched.get("expires_at")):
        return None
    return matched
