"""End-to-end test for P6-T5: teacher creates assignment, students join/submit, opt-in leaderboard."""

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


def test_end_to_end_teacher_assignment_and_student_run(client):
    # 1. Teacher invite -> redeem -> create class -> create assignment
    inv = asyncio.run(create_teacher_invite(db_mod.database, email="e2e@school.edu", display_name="Prof. E2E"))
    sess = asyncio.run(redeem_teacher_invite(db_mod.database, inv["invite_token"]))
    t_headers = {"Authorization": f"Bearer {sess['session_token']}"}

    cls_res = client.post("/api/classroom/classes", json={"name": "PK Cohort A"}, headers=t_headers)
    assert cls_res.status_code == 200
    class_id = cls_res.json()["class_id"]
    join_code = cls_res.json()["join_code"]

    asg_res = client.post(
        f"/api/classroom/classes/{class_id}/assignments",
        json={
            "experiment_id": "pk_ward",
            "title": "Oral PK Graded Run",
            "parameter_presets": {"dose_mg": 500, "interval_h": 8},
            "due_date": "2026-12-31T23:59:00Z",
            "graded": True,
        },
        headers=t_headers,
    )
    assert asg_res.status_code == 200, asg_res.text
    asg_id = asg_res.json()["assignment_id"]
    assert asg_res.json()["graded"] is True
    assert asg_res.json()["parameter_presets"] == {"dose_mg": 500, "interval_h": 8}

    # 2. Two students join: Alice (opt_in=True) and Bob (opt_in=False)
    alice_join = client.post(
        "/api/classroom/join",
        json={"join_code": join_code, "nickname": "Alice_Rx", "leaderboard_opt_in": True},
    )
    bob_join = client.post(
        "/api/classroom/join",
        json={"join_code": join_code, "nickname": "Bob_Rx", "leaderboard_opt_in": False},
    )
    assert alice_join.status_code == 200
    assert bob_join.status_code == 200
    a_headers = {"Authorization": f"Bearer {alice_join.json()['student_token']}"}
    b_headers = {"Authorization": f"Bearer {bob_join.json()['student_token']}"}

    # 3. Both view assignments and see preset + due_date + graded
    a_asgs = client.get("/api/classroom/student/assignments", headers=a_headers)
    assert a_asgs.status_code == 200
    assert len(a_asgs.json()["assignments"]) == 1
    assert a_asgs.json()["assignments"][0]["parameter_presets"]["dose_mg"] == 500

    # 4. Both run and finish real lab sessions, then submit
    sess_a = client.post(
        "/api/lab/sessions",
        json={
            "experiment_id": "pk_ward",
            "nickname": "Alice_Rx",
            "class_id": class_id,
            "student_id": alice_join.json()["student_id"],
            "assignment_id": asg_id,
        },
    ).json()
    client.post(f"/api/lab/sessions/{sess_a['session_id']}/finish")

    sess_b = client.post(
        "/api/lab/sessions",
        json={
            "experiment_id": "pk_ward",
            "nickname": "Bob_Rx",
            "class_id": class_id,
            "student_id": bob_join.json()["student_id"],
            "assignment_id": asg_id,
        },
    ).json()
    client.post(f"/api/lab/sessions/{sess_b['session_id']}/finish")

    s_alice = client.post(
        f"/api/classroom/student/assignments/{asg_id}/submit",
        json={"session_id": sess_a["session_id"]},
        headers=a_headers,
    )
    s_bob = client.post(
        f"/api/classroom/student/assignments/{asg_id}/submit",
        json={"session_id": sess_b["session_id"]},
        headers=b_headers,
    )
    assert s_alice.status_code == 200
    assert s_bob.status_code == 200

    # 5. Each student sees only their own results
    a_results = client.get("/api/classroom/student/results", headers=a_headers).json()["results"]
    b_results = client.get("/api/classroom/student/results", headers=b_headers).json()["results"]
    assert len(a_results) == 1 and a_results[0]["nickname"] == "Alice_Rx"
    assert len(b_results) == 1 and b_results[0]["nickname"] == "Bob_Rx"

    # 6. Leaderboard shows ONLY Alice (opt-in), NOT Bob
    lb = client.get("/api/classroom/student/leaderboard", headers=b_headers).json()["leaderboard"]
    assert [entry["nickname"] for entry in lb] == ["Alice_Rx"]

    # 7. Teacher sees both submissions
    t_subs = client.get(f"/api/classroom/classes/{class_id}/submissions", headers=t_headers).json()["submissions"]
    assert len(t_subs) == 2
