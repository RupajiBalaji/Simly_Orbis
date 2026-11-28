"""
A1: Server-verified submissions tests.

The backend is the single source of truth: score, grade, violations, and time
come from the stored finished lab report – never from the request body.
Tests:
- Forged score is ignored; server uses the report's actual score
- Another student's session is rejected (403)
- Unfinished session is rejected (422 – report not found)
- Wrong experiment is rejected (422)
- Double submit is rejected (409)
- Valid flow succeeds
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from app import db as db_mod
from app.classroom.teachers import create_teacher_invite, redeem_teacher_invite
from app.main import app
from app.security import rate_limiter


@pytest.fixture
def client():
    with TestClient(app) as c:
        rate_limiter._buckets.clear()
        yield c


def _make_world(client: TestClient) -> dict:
    """Create a minimal world: one teacher, one class, one assignment, two students."""
    inv = asyncio.run(create_teacher_invite(db_mod.database, email="sv_teacher@test.edu", display_name="SV Teacher"))
    sess = asyncio.run(redeem_teacher_invite(db_mod.database, inv["invite_token"]))
    hdr_t = {"Authorization": f"Bearer {sess['session_token']}"}

    cls = client.post("/api/classroom/classes", json={"name": "SV Class"}, headers=hdr_t).json()
    class_id = cls["class_id"]
    join_code = cls["join_code"]

    asg = client.post(
        f"/api/classroom/classes/{class_id}/assignments",
        json={"experiment_id": "pk_ward", "title": "PK Ward Assignment", "graded": True},
        headers=hdr_t,
    ).json()
    assignment_id = asg["assignment_id"]

    stu_a = client.post("/api/classroom/join", json={"join_code": join_code, "nickname": "StuA"}).json()
    stu_b = client.post("/api/classroom/join", json={"join_code": join_code, "nickname": "StuB"}).json()

    return {
        "class_id": class_id,
        "assignment_id": assignment_id,
        "stu_a": stu_a,  # dict with student_token, student_id, class_id
        "stu_b": stu_b,
    }


def _start_and_finish_session(client: TestClient, stu: dict, assignment_id: str) -> dict:
    """Start a lab session linked to classroom, finish it, return session_id + report."""
    hdr = {"Authorization": f"Bearer {stu['student_token']}"}

    # Start session with classroom linkage
    start_resp = client.post(
        "/api/lab/sessions",
        json={
            "experiment_id": "pk_ward",
            "nickname": stu.get("nickname", "Student"),
            "class_id": stu["class_id"],
            "student_id": stu["student_id"],
            "assignment_id": assignment_id,
        },
    )
    assert start_resp.status_code == 201, f"start failed: {start_resp.text}"
    session_id = start_resp.json()["session_id"]

    # Finish the session to generate a report
    finish_resp = client.post(f"/api/lab/sessions/{session_id}/finish")
    assert finish_resp.status_code == 200, f"finish failed: {finish_resp.text}"
    report = finish_resp.json()

    return {"session_id": session_id, "report": report}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_valid_submission_uses_server_score(client: TestClient) -> None:
    """Happy path: valid submission; server score used, client score ignored."""
    world = _make_world(client)
    stu_a = world["stu_a"]
    assignment_id = world["assignment_id"]

    info = _start_and_finish_session(client, stu_a, assignment_id)
    session_id = info["session_id"]
    server_score = info["report"]["score"]

    hdr = {"Authorization": f"Bearer {stu_a['student_token']}"}

    # Submit with only session_id (new API – client score fields are stripped)
    resp = client.post(
        f"/api/classroom/student/assignments/{assignment_id}/submit",
        json={"session_id": session_id},
        headers=hdr,
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    sub = resp.json()

    # Verify the submission uses the server's score, not some client-fabricated value
    assert sub["score"] == server_score, (
        f"Server score should be {server_score}, got {sub['score']}"
    )
    assert sub["session_id"] == session_id
    assert sub["class_id"] == world["class_id"]
    assert sub["student_id"] == stu_a["student_id"]


def test_forged_score_field_is_ignored(client: TestClient) -> None:
    """Extra score/grade in body must not be used; server authoritative values apply."""
    world = _make_world(client)
    stu_a = world["stu_a"]
    assignment_id = world["assignment_id"]

    info = _start_and_finish_session(client, stu_a, assignment_id)
    session_id = info["session_id"]
    server_score = info["report"]["score"]

    hdr = {"Authorization": f"Bearer {stu_a['student_token']}"}

    # Try submitting with fabricated score 999 (should be silently ignored by new API)
    resp = client.post(
        f"/api/classroom/student/assignments/{assignment_id}/submit",
        json={"session_id": session_id, "score": 999, "grade": "SSS", "violations": [], "time_seconds": 0},
        headers=hdr,
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    sub = resp.json()
    # Score must be from server, not 999
    assert sub["score"] != 999, "Forged score must not be accepted"
    assert sub["score"] == server_score


def test_unfinished_session_rejected(client: TestClient) -> None:
    """Session without a finished report (no lab_reports entry) must be rejected."""
    world = _make_world(client)
    stu_a = world["stu_a"]
    assignment_id = world["assignment_id"]

    hdr = {"Authorization": f"Bearer {stu_a['student_token']}"}

    # Start session but do NOT finish it
    start_resp = client.post(
        "/api/lab/sessions",
        json={
            "experiment_id": "pk_ward",
            "nickname": "StuA",
            "class_id": stu_a["class_id"],
            "student_id": stu_a["student_id"],
            "assignment_id": assignment_id,
        },
    )
    assert start_resp.status_code == 201
    session_id = start_resp.json()["session_id"]

    resp = client.post(
        f"/api/classroom/student/assignments/{assignment_id}/submit",
        json={"session_id": session_id},
        headers=hdr,
    )
    assert resp.status_code == 422, f"Expected 422 for unfinished session, got {resp.status_code}"


def test_another_students_session_rejected(client: TestClient) -> None:
    """Student B cannot submit Student A's session."""
    world = _make_world(client)
    stu_a = world["stu_a"]
    stu_b = world["stu_b"]
    assignment_id = world["assignment_id"]

    info = _start_and_finish_session(client, stu_a, assignment_id)
    session_id = info["session_id"]

    # Student B tries to submit Student A's session
    hdr_b = {"Authorization": f"Bearer {stu_b['student_token']}"}
    resp = client.post(
        f"/api/classroom/student/assignments/{assignment_id}/submit",
        json={"session_id": session_id},
        headers=hdr_b,
    )
    # Should be 403 (session belongs to another student) or 422 (no cross-session report)
    assert resp.status_code in (403, 422), (
        f"Expected 403 or 422 when submitting another student's session, got {resp.status_code}"
    )


def test_wrong_experiment_rejected(client: TestClient) -> None:
    """Session for a different experiment than the assignment must be rejected."""
    world = _make_world(client)
    stu_a = world["stu_a"]
    assignment_id = world["assignment_id"]  # assignment is for pk_ward

    hdr = {"Authorization": f"Bearer {stu_a['student_token']}"}

    # Start and finish a titration_bench session (wrong experiment)
    start_resp = client.post(
        "/api/lab/sessions",
        json={
            "experiment_id": "titration_bench",
            "nickname": "StuA",
            "class_id": stu_a["class_id"],
            "student_id": stu_a["student_id"],
            "assignment_id": assignment_id,
        },
    )
    assert start_resp.status_code == 201
    session_id = start_resp.json()["session_id"]
    finish_resp = client.post(f"/api/lab/sessions/{session_id}/finish")
    assert finish_resp.status_code == 200

    resp = client.post(
        f"/api/classroom/student/assignments/{assignment_id}/submit",
        json={"session_id": session_id},
        headers=hdr,
    )
    assert resp.status_code == 422, f"Expected 422 for wrong experiment, got {resp.status_code}: {resp.text}"


def test_double_submit_rejected(client: TestClient) -> None:
    """Submitting the same session_id twice returns 409 Conflict."""
    world = _make_world(client)
    stu_a = world["stu_a"]
    assignment_id = world["assignment_id"]

    info = _start_and_finish_session(client, stu_a, assignment_id)
    session_id = info["session_id"]

    hdr = {"Authorization": f"Bearer {stu_a['student_token']}"}

    # First submit succeeds
    resp1 = client.post(
        f"/api/classroom/student/assignments/{assignment_id}/submit",
        json={"session_id": session_id},
        headers=hdr,
    )
    assert resp1.status_code == 200, f"First submit should succeed: {resp1.text}"

    # Second submit must return 409
    resp2 = client.post(
        f"/api/classroom/student/assignments/{assignment_id}/submit",
        json={"session_id": session_id},
        headers=hdr,
    )
    assert resp2.status_code == 409, f"Expected 409 on double submit, got {resp2.status_code}"


def test_csv_export_sanitizes_formula_injection(client: TestClient) -> None:
    """CSV export prefixes dangerous formula characters (=, +, -, @) with a single quote."""
    inv = asyncio.run(create_teacher_invite(db_mod.database, email="csv_t@test.edu", display_name="CSV Teacher"))
    sess = asyncio.run(redeem_teacher_invite(db_mod.database, inv["invite_token"]))
    hdr_t = {"Authorization": f"Bearer {sess['session_token']}"}
    cls = client.post("/api/classroom/classes", json={"name": "CSV Class"}, headers=hdr_t).json()
    class_id = cls["class_id"]

    # Insert a submission record directly with a formula-like nickname
    asyncio.run(
        db_mod.database["submissions"].insert_one(
            {
                "submission_id": "sub-csv-1",
                "assignment_id": "asg-csv-1",
                "class_id": class_id,
                "student_id": "stu-csv-1",
                "nickname": "=CMD|'/C calc'!A0",
                "session_id": "sess-csv-1",
                "score": 80,
                "grade": "B",
                "violations": ["+R1", "-R2", "@R3"],
                "time_seconds": 10.0,
                "submitted_at": "2026-01-01T00:00:00Z",
            }
        )
    )
    csv_resp = client.get(f"/api/classroom/classes/{class_id}/export.csv", headers=hdr_t)
    assert csv_resp.status_code == 200
    body = csv_resp.text
    assert "'=CMD" in body
    assert "'+R1" in body
