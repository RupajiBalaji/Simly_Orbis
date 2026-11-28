"""Tests for P6-T1: classroom data models, indexes, and idempotent migrations."""

from __future__ import annotations

import asyncio
import pytest

from app import db as db_mod
from app.classroom.models import (
    CLASSROOM_SCHEMA_VERSION,
    AssignmentRecord,
    ClassRecord,
    MembershipRecord,
    SubmissionRecord,
    ensure_classroom_indexes,
    run_classroom_migrations,
)


def test_classroom_migrations_and_indexes_idempotent():
    mem_db = db_mod._InMemoryDatabase()

    async def _run():
        v1 = await run_classroom_migrations(mem_db)
        v2 = await run_classroom_migrations(mem_db)
        assert v1 == CLASSROOM_SCHEMA_VERSION
        assert v2 == CLASSROOM_SCHEMA_VERSION

        mig_count = await mem_db["schema_migrations"].count_documents({})
        assert mig_count == 1

        idx_map = await ensure_classroom_indexes(mem_db)
        for col_name, expected_names in idx_map.items():
            actual_names = [idx.get("name") for idx in mem_db[col_name]._indexes]
            for name in expected_names:
                assert name in actual_names
            assert len(actual_names) == len(set(actual_names))

    asyncio.run(_run())


def test_classroom_models_and_inmemory_crud():
    mem_db = db_mod._InMemoryDatabase()

    async def _run():
        await run_classroom_migrations(mem_db)

        cls = ClassRecord(
            class_id="cls-1",
            teacher_id="tch-1",
            name="Pharm 101",
            join_code_hash="hash-abc",
            join_code_expires_at="2099-01-01T00:00:00+00:00",
        )
        await mem_db["classes"].insert_one(cls.model_dump())

        mem = MembershipRecord(
            membership_id="mem-1",
            class_id="cls-1",
            student_id="stu-1",
            nickname="Curie_01",
        )
        await mem_db["class_memberships"].insert_one(mem.model_dump())

        asgn = AssignmentRecord(
            assignment_id="asg-1",
            class_id="cls-1",
            experiment_id="pk_oral_ward",
            title="Oral PK Practice",
            parameter_presets={"dose_mg": 500},
            graded=True,
        )
        await mem_db["assignments"].insert_one(asgn.model_dump())

        sub = SubmissionRecord(
            submission_id="sub-1",
            assignment_id="asg-1",
            class_id="cls-1",
            student_id="stu-1",
            nickname="Curie_01",
            session_id="sess-1",
            score=92.0,
            grade="A",
            violations=["R1"],
            time_seconds=120.5,
        )
        await mem_db["submissions"].insert_one(sub.model_dump())

        assert await mem_db["classes"].count_documents({"teacher_id": "tch-1"}) == 1
        assert await mem_db["submissions"].count_documents({"assignment_id": "asg-1"}) == 1

        deleted = await mem_db["submissions"].delete_many({"class_id": "cls-1"})
        assert deleted == 1
        assert await mem_db["submissions"].count_documents({}) == 0

    asyncio.run(_run())
