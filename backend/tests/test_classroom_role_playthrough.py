"""P6-T8: Role-based QA playthrough across teacher, student, guest, and static classroom pages."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import db as db_mod
from app.classroom.teachers import create_teacher_invite, redeem_teacher_invite
from app.main import app
from app.security import rate_limiter

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def client():
    with TestClient(app) as c:
        rate_limiter._buckets.clear()
        yield c


def test_role_based_classroom_qa_playthrough(client):
    # Static classroom & privacy pages are served
    for page in ("/teacher.html", "/student.html", "/privacy.html", "/terms.html"):
        r = client.get(page)
        assert r.status_code == 200, f"Expected 200 for {page}, got {r.status_code}"

    # Teacher guide exists and documents key workflows
    guide = (ROOT / "docs" / "TEACHER_GUIDE.md").read_text(encoding="utf-8")
    for required in ("create_teacher.py", "/teacher.html", "/student.html", "Export CSV", "Delete Class", "pilot with minors requires legal review"):
        assert required in guide

    # Guest cannot access teacher or student endpoints
    assert client.get("/api/classroom/classes").status_code == 401
    assert client.get("/api/classroom/student/assignments").status_code == 401

    # Teacher workflow
    inv = asyncio.run(create_teacher_invite(db_mod.database, email="qa@school.edu", display_name="QA Teacher"))
    sess = asyncio.run(redeem_teacher_invite(db_mod.database, inv["invite_token"]))
    th = {"Authorization": f"Bearer {sess['session_token']}"}
    cls = client.post("/api/classroom/classes", json={"name": "QA Class"}, headers=th).json()
    asg = client.post(
        f"/api/classroom/classes/{cls['class_id']}/assignments",
        json={"experiment_id": "launch_orbit_bench", "title": "Orbit QA", "graded": False},
        headers=th,
    ).json()

    # Student workflow
    stu = client.post("/api/classroom/join", json={"join_code": cls["join_code"], "nickname": "QA_Orbit_1"}).json()
    sh = {"Authorization": f"Bearer {stu['student_token']}"}
    assert len(client.get("/api/classroom/student/assignments", headers=sh).json()["assignments"]) == 1
    sub = client.post(
        f"/api/classroom/student/assignments/{asg['assignment_id']}/submit",
        json={"session_id": "qa-sess-1", "score": 85.0, "grade": "B", "violations": ["S1"], "time_seconds": 65.0},
        headers=sh,
    )
    assert sub.status_code == 200

    # Student cannot call teacher endpoints
    assert client.get(f"/api/classroom/classes/{cls['class_id']}/analytics", headers=sh).status_code == 401

    # Teacher sees analytics and deletes class cleanly
    ana = client.get(f"/api/classroom/classes/{cls['class_id']}/analytics", headers=th).json()
    assert ana["submission_count"] == 1
    assert client.delete(f"/api/classroom/classes/{cls['class_id']}", headers=th).json()["deleted"] is True
