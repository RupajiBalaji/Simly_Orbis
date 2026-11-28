"""
Classroom data models, collections, and idempotent index migrations (P6-T1).

Collections:
- classes
- class_memberships
- assignments
- submissions
- teachers
- teacher_tokens
- student_sessions
- schema_migrations
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

CLASSROOM_SCHEMA_VERSION = 1


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ClassRecord(BaseModel):
    class_id: str
    teacher_id: str
    name: str
    join_code_hash: str
    join_code_expires_at: str
    active: bool = True
    created_at: str = Field(default_factory=utc_now_iso)


class MembershipRecord(BaseModel):
    membership_id: str
    class_id: str
    student_id: str
    nickname: str
    nickname_lower: str = ""  # for case-insensitive uniqueness checks
    leaderboard_opt_in: bool = False
    joined_at: str = Field(default_factory=utc_now_iso)


class AssignmentRecord(BaseModel):
    assignment_id: str
    class_id: str
    experiment_id: str
    title: str
    parameter_presets: dict[str, Any] = Field(default_factory=dict)
    due_date: str | None = None
    graded: bool = False
    created_at: str = Field(default_factory=utc_now_iso)


class SubmissionRecord(BaseModel):
    submission_id: str
    assignment_id: str
    class_id: str
    student_id: str
    nickname: str
    session_id: str
    score: float
    grade: str
    violations: list[str] = Field(default_factory=list)
    time_seconds: float = 0.0
    submitted_at: str = Field(default_factory=utc_now_iso)


class TeacherRecord(BaseModel):
    teacher_id: str
    email: str
    display_name: str
    active: bool = True
    created_at: str = Field(default_factory=utc_now_iso)


class TeacherTokenRecord(BaseModel):
    token_id: str
    token_hash: str
    teacher_id: str
    token_type: str  # "invite" | "session"
    expires_at: str
    used_at: str | None = None
    created_at: str = Field(default_factory=utc_now_iso)


class StudentSessionRecord(BaseModel):
    token_hash: str
    student_id: str
    class_id: str
    nickname: str
    expires_at: str
    created_at: str = Field(default_factory=utc_now_iso)


async def ensure_classroom_indexes(db: Any) -> dict[str, list[str]]:
    """Create all indexes for classroom collections (idempotent)."""
    import pymongo  # noqa: PLC0415

    created: dict[str, list[str]] = {}

    classes = db["classes"]
    await classes.create_index([("class_id", pymongo.ASCENDING)], unique=True, name="classes_id_unique_idx")
    await classes.create_index([("teacher_id", pymongo.ASCENDING)], name="classes_teacher_idx")
    await classes.create_index([("join_code_hash", pymongo.ASCENDING)], unique=True, name="classes_code_hash_unique_idx")
    created["classes"] = ["classes_id_unique_idx", "classes_teacher_idx", "classes_code_hash_unique_idx"]

    memberships = db["class_memberships"]
    await memberships.create_index([("membership_id", pymongo.ASCENDING)], unique=True, name="memberships_id_unique_idx")
    await memberships.create_index(
        [("class_id", pymongo.ASCENDING), ("student_id", pymongo.ASCENDING)],
        unique=True,
        name="memberships_class_student_unique_idx",
    )
    await memberships.create_index(
        [("class_id", pymongo.ASCENDING), ("nickname", pymongo.ASCENDING)],
        name="memberships_class_nickname_idx",
    )
    await memberships.create_index(
        [("class_id", pymongo.ASCENDING), ("nickname_lower", pymongo.ASCENDING)],
        unique=True,
        name="memberships_class_nickname_lower_unique_idx",
    )
    created["class_memberships"] = [
        "memberships_id_unique_idx",
        "memberships_class_student_unique_idx",
        "memberships_class_nickname_idx",
        "memberships_class_nickname_lower_unique_idx",
    ]

    assignments = db["assignments"]
    await assignments.create_index([("assignment_id", pymongo.ASCENDING)], unique=True, name="assignments_id_unique_idx")
    await assignments.create_index(
        [("class_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
        name="assignments_class_created_idx",
    )
    created["assignments"] = ["assignments_id_unique_idx", "assignments_class_created_idx"]

    submissions = db["submissions"]
    await submissions.create_index([("submission_id", pymongo.ASCENDING)], unique=True, name="submissions_id_unique_idx")
    await submissions.create_index(
        [("assignment_id", pymongo.ASCENDING), ("score", pymongo.DESCENDING)],
        name="submissions_assignment_score_idx",
    )
    await submissions.create_index(
        [("class_id", pymongo.ASCENDING), ("student_id", pymongo.ASCENDING)],
        name="submissions_class_student_idx",
    )
    created["submissions"] = [
        "submissions_id_unique_idx",
        "submissions_assignment_score_idx",
        "submissions_class_student_idx",
    ]

    teachers = db["teachers"]
    await teachers.create_index([("teacher_id", pymongo.ASCENDING)], unique=True, name="teachers_id_unique_idx")
    await teachers.create_index([("email", pymongo.ASCENDING)], unique=True, name="teachers_email_unique_idx")
    created["teachers"] = ["teachers_id_unique_idx", "teachers_email_unique_idx"]

    teacher_tokens = db["teacher_tokens"]
    await teacher_tokens.create_index([("token_hash", pymongo.ASCENDING)], unique=True, name="teacher_tokens_hash_unique_idx")
    await teacher_tokens.create_index([("teacher_id", pymongo.ASCENDING)], name="teacher_tokens_teacher_idx")
    created["teacher_tokens"] = ["teacher_tokens_hash_unique_idx", "teacher_tokens_teacher_idx"]

    student_sessions = db["student_sessions"]
    await student_sessions.create_index([("token_hash", pymongo.ASCENDING)], unique=True, name="student_sessions_hash_unique_idx")
    await student_sessions.create_index([("class_id", pymongo.ASCENDING)], name="student_sessions_class_idx")
    created["student_sessions"] = ["student_sessions_hash_unique_idx", "student_sessions_class_idx"]

    return created


async def run_classroom_migrations(db: Any) -> int:
    """Run idempotent classroom schema migrations and record version."""
    await ensure_classroom_indexes(db)
    migrations = db["schema_migrations"]
    existing = await migrations.find_one({"migration_id": f"classroom_v{CLASSROOM_SCHEMA_VERSION}"})
    if not existing:
        await migrations.insert_one({
            "migration_id": f"classroom_v{CLASSROOM_SCHEMA_VERSION}",
            "version": CLASSROOM_SCHEMA_VERSION,
            "applied_at": utc_now_iso(),
        })
    return CLASSROOM_SCHEMA_VERSION
