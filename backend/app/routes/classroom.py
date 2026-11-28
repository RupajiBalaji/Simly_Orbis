"""
Classroom API routes (P6):
- Student join by class code + nickname (P6-T2)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app import db as db_mod
from app.classroom.models import MembershipRecord, StudentSessionRecord, utc_now_iso
from app.classroom.security import (
    constant_time_equals,
    expiry_iso,
    generate_token,
    hash_secret,
    is_expired,
    normalize_join_code,
    validate_nickname,
)
from app.config import settings
from app.security import rate_limiter, resolve_client_ip

router = APIRouter(prefix="/api/classroom", tags=["classroom"])


class StudentJoinRequest(BaseModel):
    join_code: str = Field(..., min_length=2, max_length=24)
    nickname: str = Field(..., min_length=1, max_length=64)
    leaderboard_opt_in: bool = False


class StudentJoinResponse(BaseModel):
    student_token: str
    student_id: str
    class_id: str
    class_name: str
    nickname: str
    leaderboard_opt_in: bool
    expires_at: str


def _enforce_auth_rate_limit(request: Request) -> None:
    client_ip = resolve_client_ip(request) or "unknown"
    if not rate_limiter.check(client_ip, "auth"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please wait a minute and try again.",
        )


@router.post("/join", response_model=StudentJoinResponse)
async def student_join_class(payload: StudentJoinRequest, request: Request) -> StudentJoinResponse:
    """
    Allow a student to join a class using a class join code and a nickname.
    No email or password is collected (G10, 13.1).
    """
    _enforce_auth_rate_limit(request)

    ok, nick_or_err = validate_nickname(payload.nickname)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=nick_or_err)
    nickname = nick_or_err

    code_norm = normalize_join_code(payload.join_code)
    if not code_norm:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid class code.")

    code_hash = hash_secret(code_norm)
    # Constant-time lookup across active classes
    classes_col = db_mod.database["classes"]
    all_classes = await classes_col.find({})
    matched_cls = None
    for cls_doc in all_classes:
        stored_hash = cls_doc.get("join_code_hash", "")
        if stored_hash and constant_time_equals(stored_hash, code_hash):
            matched_cls = cls_doc
            break

    if not matched_cls or not matched_cls.get("active", True):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class code not found.")

    if is_expired(matched_cls.get("join_code_expires_at")):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="This class join code has expired. Ask your teacher to reset it.")

    class_id = matched_cls["class_id"]
    student_id = f"stu-{uuid.uuid4().hex[:12]}"
    membership = MembershipRecord(
        membership_id=f"mem-{uuid.uuid4().hex[:12]}",
        class_id=class_id,
        student_id=student_id,
        nickname=nickname,
        leaderboard_opt_in=payload.leaderboard_opt_in,
        joined_at=utc_now_iso(),
    )
    await db_mod.database["class_memberships"].insert_one(membership.model_dump())

    raw_token = generate_token()
    expires_at = expiry_iso(hours=settings.student_session_ttl_hours)
    sess = StudentSessionRecord(
        token_hash=hash_secret(raw_token),
        student_id=student_id,
        class_id=class_id,
        nickname=nickname,
        expires_at=expires_at,
        created_at=utc_now_iso(),
    )
    await db_mod.database["student_sessions"].insert_one(sess.model_dump())

    return StudentJoinResponse(
        student_token=raw_token,
        student_id=student_id,
        class_id=class_id,
        class_name=matched_cls["name"],
        nickname=nickname,
        leaderboard_opt_in=payload.leaderboard_opt_in,
        expires_at=expires_at,
    )
