"""Tests for P6-T6: privacy docs/pages, 13.3 data inventory compliance, and retention job."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app import db as db_mod
from app.classroom.models import (
    AssignmentRecord,
    ClassRecord,
    MembershipRecord,
    StudentSessionRecord,
    SubmissionRecord,
    TeacherRecord,
    TeacherTokenRecord,
)
from app.classroom.retention import purge_expired_guest_sessions
from app.config import settings

ROOT = Path(__file__).resolve().parents[2]

# Forbidden PII / non-stored fields per Section 13.3 Data Inventory
FORBIDDEN_STORED_FIELDS = {
    "student_email",
    "ip_address",
    "client_ip",
    "audio",
    "audio_blob",
    "ai_prompt_content",
    "password",
    "password_hash",
}


def test_privacy_docs_and_pages_exist_without_compliance_claim():
    privacy_md = (ROOT / "docs" / "PRIVACY.md").read_text(encoding="utf-8")
    privacy_html = (ROOT / "frontend" / "privacy.html").read_text(encoding="utf-8")
    terms_html = (ROOT / "frontend" / "terms.html").read_text(encoding="utf-8")

    for text in (privacy_md, privacy_html, terms_html):
        assert "pilot with minors requires legal review" in text.lower()
        assert "dpdp compliant" not in text.lower()
        assert "we are compliant with" not in text.lower()


def test_stored_fields_match_section_13_3_data_inventory():
    models = [
        ClassRecord(
            class_id="c1",
            teacher_id="t1",
            name="Bio",
            join_code_hash="h1",
            join_code_expires_at="2099-01-01T00:00:00+00:00",
        ),
        MembershipRecord(membership_id="m1", class_id="c1", student_id="s1", nickname="Curie"),
        AssignmentRecord(assignment_id="a1", class_id="c1", experiment_id="pk_oral_ward", title="Lab 1"),
        SubmissionRecord(
            submission_id="sub1",
            assignment_id="a1",
            class_id="c1",
            student_id="s1",
            nickname="Curie",
            session_id="sess1",
            score=90.0,
            grade="A",
        ),
        TeacherRecord(teacher_id="t1", email="t@school.edu", display_name="Prof"),
        TeacherTokenRecord(
            token_id="tok1",
            token_hash="th1",
            teacher_id="t1",
            token_type="invite",
            expires_at="2099-01-01T00:00:00+00:00",
        ),
        StudentSessionRecord(
            token_hash="sh1",
            student_id="s1",
            class_id="c1",
            nickname="Curie",
            expires_at="2099-01-01T00:00:00+00:00",
        ),
    ]
    for model in models:
        keys = set(model.model_dump().keys())
        overlap = keys & FORBIDDEN_STORED_FIELDS
        assert not overlap, f"Forbidden fields stored in {type(model).__name__}: {overlap}"


def test_retention_job_purges_old_guest_sessions_and_preserves_class_data():
    mem_db = db_mod._InMemoryDatabase()
    now = datetime.now(timezone.utc)
    old_ts = (now - timedelta(days=settings.guest_session_retention_days + 5)).isoformat()
    recent_ts = (now - timedelta(days=10)).isoformat()

    async def _run():
        await mem_db["lab_sessions"].insert_one({"session_id": "guest-old", "created_at": old_ts})
        await mem_db["lab_sessions"].insert_one({"session_id": "guest-new", "created_at": recent_ts})
        await mem_db["lab_sessions"].insert_one({"session_id": "class-old", "class_id": "c1", "created_at": old_ts})
        await mem_db["student_sessions"].insert_one({
            "token_hash": "exp",
            "student_id": "s1",
            "class_id": "c1",
            "nickname": "Curie",
            "expires_at": old_ts,
        })

        res = await purge_expired_guest_sessions(mem_db, now=now)
        assert res["purged_guest_sessions"] == 1
        assert res["purged_student_tokens"] == 1
        assert await mem_db["lab_sessions"].find_one({"session_id": "guest-old"}) is None
        assert await mem_db["lab_sessions"].find_one({"session_id": "guest-new"}) is not None
        # Class data preserved until teacher deletes class
        assert await mem_db["lab_sessions"].find_one({"session_id": "class-old"}) is not None

    asyncio.run(_run())
