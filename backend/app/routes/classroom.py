"""
Classroom API routes (P6):
- Student join by class code + nickname (P6-T2)
"""

from __future__ import annotations

from collections import Counter
import csv
import io
import uuid

from fastapi import APIRouter, Header, HTTPException, Request, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app import db as db_mod
from app.classroom.models import (
    AssignmentRecord,
    ClassRecord,
    MembershipRecord,
    StudentSessionRecord,
    SubmissionRecord,
    utc_now_iso,
)
from app.classroom.security import (
    constant_time_equals,
    expiry_iso,
    generate_join_code,
    generate_token,
    hash_secret,
    is_expired,
    normalize_join_code,
    validate_nickname,
)
from app.classroom.teachers import redeem_teacher_invite, verify_student_session, verify_teacher_session
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


class TeacherRedeemRequest(BaseModel):
    invite_token: str = Field(..., min_length=8, max_length=256)


class TeacherRedeemResponse(BaseModel):
    teacher_id: str
    email: str
    display_name: str
    session_token: str
    expires_at: str


def _extract_bearer(authorization: str | None) -> str:
    if not authorization:
        return ""
    parts = authorization.strip().split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return ""


async def require_teacher(authorization: str | None = Header(default=None)) -> dict:
    token = _extract_bearer(authorization)
    teacher = await verify_teacher_session(db_mod.database, token)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid teacher session token required.",
        )
    return teacher


@router.post("/teacher/redeem", response_model=TeacherRedeemResponse)
async def redeem_teacher_token(payload: TeacherRedeemRequest, request: Request) -> TeacherRedeemResponse:
    """Redeem a single-use expiring teacher invite token for a session token."""
    _enforce_auth_rate_limit(request)
    res = await redeem_teacher_invite(db_mod.database, payload.invite_token)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or already-used invite token.",
        )
    return TeacherRedeemResponse(**res)


@router.get("/teacher/me")
async def get_teacher_profile(authorization: str | None = Header(default=None)) -> dict:
    """Return the authenticated teacher's profile."""
    teacher = await require_teacher(authorization)
    return {
        "teacher_id": teacher["teacher_id"],
        "email": teacher["email"],
        "display_name": teacher["display_name"],
    }


# ---------------------------------------------------------------------------
# P6-T4: Teacher Dashboard Routes (classes, roster, submissions, analytics,
# CSV export, reset code, cascading class deletion)
# ---------------------------------------------------------------------------


class CreateClassRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)


async def _get_owned_class(class_id: str, teacher_id: str) -> dict:
    cls_doc = await db_mod.database["classes"].find_one({"class_id": class_id})
    if not cls_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found.")
    if cls_doc.get("teacher_id") != teacher_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this class.")
    return cls_doc


@router.post("/classes")
async def create_class(payload: CreateClassRequest, authorization: str | None = Header(default=None)) -> dict:
    """Create a new class and return its one-time plaintext join code."""
    teacher = await require_teacher(authorization)
    raw_code = generate_join_code()
    rec = ClassRecord(
        class_id=f"cls-{uuid.uuid4().hex[:10]}",
        teacher_id=teacher["teacher_id"],
        name=payload.name.strip(),
        join_code_hash=hash_secret(raw_code),
        join_code_expires_at=expiry_iso(days=settings.join_code_ttl_days),
        active=True,
        created_at=utc_now_iso(),
    )
    await db_mod.database["classes"].insert_one(rec.model_dump())
    return {
        "class_id": rec.class_id,
        "name": rec.name,
        "join_code": raw_code,
        "join_code_expires_at": rec.join_code_expires_at,
        "created_at": rec.created_at,
    }


@router.get("/classes")
async def list_teacher_classes(authorization: str | None = Header(default=None)) -> dict:
    """List classes owned by the authenticated teacher."""
    teacher = await require_teacher(authorization)
    docs = await db_mod.database["classes"].find({"teacher_id": teacher["teacher_id"]})
    classes = [
        {
            "class_id": d["class_id"],
            "name": d["name"],
            "active": d.get("active", True),
            "join_code_expires_at": d.get("join_code_expires_at"),
            "created_at": d.get("created_at"),
        }
        for d in docs
    ]
    return {"classes": classes}


@router.post("/classes/{class_id}/reset-code")
async def reset_class_code(class_id: str, authorization: str | None = Header(default=None)) -> dict:
    """Generate a new join code for a class, invalidating the old code."""
    teacher = await require_teacher(authorization)
    await _get_owned_class(class_id, teacher["teacher_id"])
    new_code = generate_join_code()
    new_exp = expiry_iso(days=settings.join_code_ttl_days)
    await db_mod.database["classes"].update_one(
        {"class_id": class_id},
        {"$set": {"join_code_hash": hash_secret(new_code), "join_code_expires_at": new_exp}},
    )
    return {"class_id": class_id, "join_code": new_code, "join_code_expires_at": new_exp}


@router.get("/classes/{class_id}/roster")
async def get_class_roster(class_id: str, authorization: str | None = Header(default=None)) -> dict:
    """Return nickname-only roster for a class owned by the teacher."""
    teacher = await require_teacher(authorization)
    await _get_owned_class(class_id, teacher["teacher_id"])
    members = await db_mod.database["class_memberships"].find({"class_id": class_id})
    roster = [
        {
            "student_id": m["student_id"],
            "nickname": m["nickname"],
            "leaderboard_opt_in": bool(m.get("leaderboard_opt_in", False)),
            "joined_at": m.get("joined_at"),
        }
        for m in members
    ]
    return {"class_id": class_id, "roster": roster}


@router.get("/classes/{class_id}/submissions")
async def get_class_submissions(class_id: str, authorization: str | None = Header(default=None)) -> dict:
    """Return submissions table with grade, score, violations, and time."""
    teacher = await require_teacher(authorization)
    await _get_owned_class(class_id, teacher["teacher_id"])
    subs = await db_mod.database["submissions"].find({"class_id": class_id})
    rows = [
        {
            "submission_id": s["submission_id"],
            "assignment_id": s["assignment_id"],
            "student_id": s["student_id"],
            "nickname": s["nickname"],
            "grade": s.get("grade", ""),
            "score": s.get("score", 0),
            "violations": list(s.get("violations", [])),
            "time_seconds": s.get("time_seconds", 0.0),
            "submitted_at": s.get("submitted_at"),
        }
        for s in subs
    ]
    return {"class_id": class_id, "submissions": rows}


@router.get("/classes/{class_id}/analytics")
async def get_class_analytics(class_id: str, authorization: str | None = Header(default=None)) -> dict:
    """Compute class analytics: frequent rule violations, average score per experiment, common mistakes."""
    teacher = await require_teacher(authorization)
    await _get_owned_class(class_id, teacher["teacher_id"])

    members = await db_mod.database["class_memberships"].find({"class_id": class_id})
    assignments = await db_mod.database["assignments"].find({"class_id": class_id})
    subs = await db_mod.database["submissions"].find({"class_id": class_id})

    asg_to_exp = {a["assignment_id"]: a.get("experiment_id", "unknown") for a in assignments}
    violation_counts: Counter[str] = Counter()
    exp_scores: dict[str, list[float]] = {}

    for s in subs:
        for v in s.get("violations", []):
            violation_counts[str(v)] += 1
        exp_id = asg_to_exp.get(s.get("assignment_id", ""), "unknown")
        exp_scores.setdefault(exp_id, []).append(float(s.get("score", 0.0)))

    top_violations = [
        {"rule_id": rule_id, "count": count}
        for rule_id, count in violation_counts.most_common(10)
    ]
    avg_score_per_experiment = {
        exp_id: round(sum(vals) / len(vals), 2)
        for exp_id, vals in exp_scores.items()
        if vals
    }
    common_mistakes = [
        f"{item['rule_id']} ({item['count']} occurrences)"
        for item in top_violations[:5]
    ]

    return {
        "class_id": class_id,
        "student_count": len(members),
        "assignment_count": len(assignments),
        "submission_count": len(subs),
        "top_rule_violations": top_violations,
        "average_score_per_experiment": avg_score_per_experiment,
        "common_mistakes": common_mistakes,
    }


@router.get("/classes/{class_id}/export.csv")
async def export_class_csv(class_id: str, authorization: str | None = Header(default=None)) -> Response:
    """Export nickname-only class submissions as CSV (no PII)."""
    teacher = await require_teacher(authorization)
    await _get_owned_class(class_id, teacher["teacher_id"])

    subs = await db_mod.database["submissions"].find({"class_id": class_id})
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["submission_id", "assignment_id", "nickname", "grade", "score", "violations", "time_seconds", "submitted_at"])
    for s in subs:
        writer.writerow([
            s.get("submission_id", ""),
            s.get("assignment_id", ""),
            s.get("nickname", ""),
            s.get("grade", ""),
            s.get("score", 0),
            ";".join(str(v) for v in s.get("violations", [])),
            s.get("time_seconds", 0.0),
            s.get("submitted_at", ""),
        ])

    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="class_{class_id}_submissions.csv"'},
    )


@router.delete("/classes/{class_id}")
async def delete_class_cascade(class_id: str, authorization: str | None = Header(default=None)) -> dict:
    """Delete a class and every record linked to it (memberships, assignments, submissions, student sessions)."""
    teacher = await require_teacher(authorization)
    await _get_owned_class(class_id, teacher["teacher_id"])

    deleted_submissions = await db_mod.database["submissions"].delete_many({"class_id": class_id})
    deleted_assignments = await db_mod.database["assignments"].delete_many({"class_id": class_id})
    deleted_memberships = await db_mod.database["class_memberships"].delete_many({"class_id": class_id})
    deleted_student_sessions = await db_mod.database["student_sessions"].delete_many({"class_id": class_id})
    deleted_lab_sessions = await db_mod.database["lab_sessions"].delete_many({"class_id": class_id})
    deleted_lab_reports = await db_mod.database["lab_reports"].delete_many({"class_id": class_id})
    deleted_classes = await db_mod.database["classes"].delete_one({"class_id": class_id})

    return {
        "deleted": True,
        "class_id": class_id,
        "counts": {
            "classes": deleted_classes,
            "memberships": deleted_memberships,
            "assignments": deleted_assignments,
            "submissions": deleted_submissions,
            "student_sessions": deleted_student_sessions,
            "lab_sessions": deleted_lab_sessions,
            "lab_reports": deleted_lab_reports,
        },
    }


# ---------------------------------------------------------------------------
# P6-T5: Assignments, Student Class View, and Opt-In Leaderboard
# ---------------------------------------------------------------------------


class CreateAssignmentRequest(BaseModel):
    experiment_id: str = Field(..., min_length=2, max_length=64)
    title: str = Field(..., min_length=2, max_length=120)
    parameter_presets: dict = Field(default_factory=dict)
    due_date: str | None = None
    graded: bool = False


class SubmitAssignmentRequest(BaseModel):
    session_id: str = Field(..., min_length=2, max_length=80)
    score: float = Field(..., ge=0.0, le=100.0)
    grade: str = Field(..., min_length=1, max_length=12)
    violations: list[str] = Field(default_factory=list)
    time_seconds: float = Field(default=0.0, ge=0.0)


class LeaderboardOptInRequest(BaseModel):
    opt_in: bool


async def require_student(authorization: str | None = Header(default=None)) -> dict:
    token = _extract_bearer(authorization)
    sess = await verify_student_session(db_mod.database, token)
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid student session token required.",
        )
    return sess


@router.post("/classes/{class_id}/assignments")
async def create_assignment(
    class_id: str,
    payload: CreateAssignmentRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    """Create an assignment for a class owned by the authenticated teacher."""
    teacher = await require_teacher(authorization)
    await _get_owned_class(class_id, teacher["teacher_id"])

    rec = AssignmentRecord(
        assignment_id=f"asg-{uuid.uuid4().hex[:10]}",
        class_id=class_id,
        experiment_id=payload.experiment_id.strip(),
        title=payload.title.strip(),
        parameter_presets=payload.parameter_presets,
        due_date=payload.due_date,
        graded=payload.graded,
        created_at=utc_now_iso(),
    )
    await db_mod.database["assignments"].insert_one(rec.model_dump())
    return rec.model_dump()


@router.get("/classes/{class_id}/assignments")
async def list_class_assignments_teacher(
    class_id: str,
    authorization: str | None = Header(default=None),
) -> dict:
    """List assignments for a class owned by the authenticated teacher."""
    teacher = await require_teacher(authorization)
    await _get_owned_class(class_id, teacher["teacher_id"])
    docs = await db_mod.database["assignments"].find({"class_id": class_id})
    for d in docs:
        d.pop("_id", None)
    return {"class_id": class_id, "assignments": docs}


@router.get("/student/assignments")
async def list_student_assignments(authorization: str | None = Header(default=None)) -> dict:
    """List assignments for the authenticated student's class."""
    sess = await require_student(authorization)
    docs = await db_mod.database["assignments"].find({"class_id": sess["class_id"]})
    for d in docs:
        d.pop("_id", None)
    return {"class_id": sess["class_id"], "assignments": docs}


@router.post("/student/assignments/{assignment_id}/submit")
async def submit_student_assignment(
    assignment_id: str,
    payload: SubmitAssignmentRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    """Submit a student's experiment result for an assignment in their own class."""
    sess = await require_student(authorization)
    asg = await db_mod.database["assignments"].find_one({"assignment_id": assignment_id})
    if not asg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")
    if asg.get("class_id") != sess["class_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Assignment belongs to another class.")

    rec = SubmissionRecord(
        submission_id=f"sub-{uuid.uuid4().hex[:10]}",
        assignment_id=assignment_id,
        class_id=sess["class_id"],
        student_id=sess["student_id"],
        nickname=sess["nickname"],
        session_id=payload.session_id,
        score=payload.score,
        grade=payload.grade,
        violations=payload.violations,
        time_seconds=payload.time_seconds,
        submitted_at=utc_now_iso(),
    )
    await db_mod.database["submissions"].insert_one(rec.model_dump())
    return rec.model_dump()


@router.get("/student/results")
async def get_student_own_results(authorization: str | None = Header(default=None)) -> dict:
    """Return only the authenticated student's own submissions."""
    sess = await require_student(authorization)
    docs = await db_mod.database["submissions"].find({
        "class_id": sess["class_id"],
        "student_id": sess["student_id"],
    })
    for d in docs:
        d.pop("_id", None)
    return {"student_id": sess["student_id"], "nickname": sess["nickname"], "results": docs}


@router.post("/student/leaderboard-opt-in")
async def update_leaderboard_opt_in(
    payload: LeaderboardOptInRequest,
    authorization: str | None = Header(default=None),
) -> dict:
    """Update the authenticated student's class leaderboard opt-in preference."""
    sess = await require_student(authorization)
    await db_mod.database["class_memberships"].update_one(
        {"class_id": sess["class_id"], "student_id": sess["student_id"]},
        {"$set": {"leaderboard_opt_in": payload.opt_in}},
    )
    return {"student_id": sess["student_id"], "leaderboard_opt_in": payload.opt_in}


@router.get("/student/leaderboard")
async def get_class_leaderboard(authorization: str | None = Header(default=None)) -> dict:
    """Return opt-in class leaderboard (only students with leaderboard_opt_in=True)."""
    sess = await require_student(authorization)
    members = await db_mod.database["class_memberships"].find({
        "class_id": sess["class_id"],
        "leaderboard_opt_in": True,
    })
    opted_in_ids = {m["student_id"] for m in members}
    subs = await db_mod.database["submissions"].find({"class_id": sess["class_id"]})

    best_by_student: dict[str, dict] = {}
    for s in subs:
        sid = s["student_id"]
        if sid not in opted_in_ids:
            continue
        prev = best_by_student.get(sid)
        if prev is None or float(s.get("score", 0)) > float(prev.get("score", 0)):
            best_by_student[sid] = {
                "nickname": s["nickname"],
                "score": s["score"],
                "grade": s.get("grade", ""),
                "assignment_id": s["assignment_id"],
            }

    entries = sorted(best_by_student.values(), key=lambda x: float(x["score"]), reverse=True)
    return {"class_id": sess["class_id"], "leaderboard": entries}
