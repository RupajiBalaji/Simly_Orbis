"""Tests for P6-T4: teacher dashboard analytics, CSV export, reset code, and cascading deletion."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from app import db as db_mod
from app.classroom.models import AssignmentRecord, SubmissionRecord
from app.classroom.teachers import create_teacher_invite, redeem_teacher_invite
from app.main import app
from app.security import rate_limiter


@pytest.fixture
def client():
    with TestClient(app) as c:
        rate_limiter._buckets.clear()
        yield c


def _teacher_headers(email: str, name: str) -> dict[str, str]:
    inv = asyncio.run(create_teacher_invite(db_mod.database, email=email, display_name=name))
    sess = asyncio.run(redeem_teacher_invite(db_mod.database, inv["invite_token"]))
    assert sess is not None
    return {"Authorization": f"Bearer {sess['session_token']}"}


def test_teacher_dashboard_analytics_csv_reset_and_cascade_delete(client):
    headers = _teacher_headers("dash@school.edu", "Prof. Dash")

    # Create two classes so we can verify deletion of class 1 does not touch class 2
    c1 = client.post("/api/classroom/classes", json={"name": "PK 101"}, headers=headers)
    assert c1.status_code == 200, c1.text
    c1_id = c1.json()["class_id"]
    c1_code = c1.json()["join_code"]

    c2 = client.post("/api/classroom/classes", json={"name": "Orbit 102"}, headers=headers)
    assert c2.status_code == 200
    c2_id = c2.json()["class_id"]

    # Student joins class 1
    j1 = client.post("/api/classroom/join", json={"join_code": c1_code, "nickname": "Curie_01"})
    assert j1.status_code == 200
    stu_id = j1.json()["student_id"]

    # Seed an assignment & two submissions for class 1, plus one for class 2
    asyncio.run(db_mod.database["assignments"].insert_one(
        AssignmentRecord(
            assignment_id="asg-c1",
            class_id=c1_id,
            experiment_id="pk_oral_ward",
            title="Oral PK",
        ).model_dump()
    ))
    asyncio.run(db_mod.database["submissions"].insert_one(
        SubmissionRecord(
            submission_id="sub-c1-1",
            assignment_id="asg-c1",
            class_id=c1_id,
            student_id=stu_id,
            nickname="Curie_01",
            session_id="sess-1",
            score=80.0,
            grade="B",
            violations=["R1", "R3"],
            time_seconds=90.0,
        ).model_dump()
    ))
    asyncio.run(db_mod.database["submissions"].insert_one(
        SubmissionRecord(
            submission_id="sub-c1-2",
            assignment_id="asg-c1",
            class_id=c1_id,
            student_id=stu_id,
            nickname="Curie_01",
            session_id="sess-2",
            score=100.0,
            grade="A",
            violations=["R1"],
            time_seconds=75.0,
        ).model_dump()
    ))
    asyncio.run(db_mod.database["submissions"].insert_one(
        SubmissionRecord(
            submission_id="sub-c2-1",
            assignment_id="asg-c2",
            class_id=c2_id,
            student_id="stu-other",
            nickname="Newton_02",
            session_id="sess-3",
            score=95.0,
            grade="A",
            violations=[],
            time_seconds=60.0,
        ).model_dump()
    ))

    # Roster, submissions, analytics, CSV export
    roster = client.get(f"/api/classroom/classes/{c1_id}/roster", headers=headers)
    assert roster.status_code == 200
    assert [r["nickname"] for r in roster.json()["roster"]] == ["Curie_01"]

    subs = client.get(f"/api/classroom/classes/{c1_id}/submissions", headers=headers)
    assert subs.status_code == 200
    assert len(subs.json()["submissions"]) == 2

    ana = client.get(f"/api/classroom/classes/{c1_id}/analytics", headers=headers)
    assert ana.status_code == 200
    ana_data = ana.json()
    assert ana_data["student_count"] == 1
    assert ana_data["submission_count"] == 2
    assert ana_data["average_score_per_experiment"]["pk_oral_ward"] == 90.0
    assert ana_data["top_rule_violations"][0] == {"rule_id": "R1", "count": 2}

    csv_res = client.get(f"/api/classroom/classes/{c1_id}/export.csv", headers=headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "Curie_01" in csv_res.text
    assert "dash@school.edu" not in csv_res.text

    # Reset code invalidates old code and enables new code
    reset_res = client.post(f"/api/classroom/classes/{c1_id}/reset-code", headers=headers)
    assert reset_res.status_code == 200
    new_code = reset_res.json()["join_code"]
    assert new_code != c1_code
    assert client.post("/api/classroom/join", json={"join_code": c1_code, "nickname": "Bohr_03"}).status_code == 404
    assert client.post("/api/classroom/join", json={"join_code": new_code, "nickname": "Bohr_03"}).status_code == 200

    # Cascading class deletion removes EVERY linked record for c1, leaves c2 untouched
    del_res = client.delete(f"/api/classroom/classes/{c1_id}", headers=headers)
    assert del_res.status_code == 200
    assert asyncio.run(db_mod.database["classes"].count_documents({"class_id": c1_id})) == 0
    assert asyncio.run(db_mod.database["class_memberships"].count_documents({"class_id": c1_id})) == 0
    assert asyncio.run(db_mod.database["assignments"].count_documents({"class_id": c1_id})) == 0
    assert asyncio.run(db_mod.database["submissions"].count_documents({"class_id": c1_id})) == 0
    assert asyncio.run(db_mod.database["student_sessions"].count_documents({"class_id": c1_id})) == 0
    # Class 2 remains intact
    assert asyncio.run(db_mod.database["classes"].count_documents({"class_id": c2_id})) == 1
    assert asyncio.run(db_mod.database["submissions"].count_documents({"class_id": c2_id})) == 1
