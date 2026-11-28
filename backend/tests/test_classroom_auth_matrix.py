"""
P6-T7: Authorisation matrix tests generated from Section 13.2 permission table,
plus rate-limit (resolve_client_ip) and token-expiry tests.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app import db as db_mod
from app.classroom.models import StudentSessionRecord
from app.classroom.security import hash_secret
from app.classroom.teachers import create_teacher_invite, redeem_teacher_invite
from app.main import app
from app.security import rate_limiter


@pytest.fixture
def client():
    with TestClient(app) as c:
        rate_limiter._buckets.clear()
        yield c


def _setup_world(client: TestClient) -> dict:
    inv_a = asyncio.run(create_teacher_invite(db_mod.database, email="ta@school.edu", display_name="Teacher A"))
    sess_a = asyncio.run(redeem_teacher_invite(db_mod.database, inv_a["invite_token"]))
    hdr_ta = {"Authorization": f"Bearer {sess_a['session_token']}"}

    inv_b = asyncio.run(create_teacher_invite(db_mod.database, email="tb@school.edu", display_name="Teacher B"))
    sess_b = asyncio.run(redeem_teacher_invite(db_mod.database, inv_b["invite_token"]))
    hdr_tb = {"Authorization": f"Bearer {sess_b['session_token']}"}

    cls_a = client.post("/api/classroom/classes", json={"name": "Class A"}, headers=hdr_ta).json()
    cls_b = client.post("/api/classroom/classes", json={"name": "Class B"}, headers=hdr_tb).json()

    asg_a = client.post(
        f"/api/classroom/classes/{cls_a['class_id']}/assignments",
        json={"experiment_id": "pk_ward", "title": "Asg A"},
        headers=hdr_ta,
    ).json()

    stu_a = client.post(
        "/api/classroom/join",
        json={"join_code": cls_a["join_code"], "nickname": "StuA_01"},
    ).json()
    stu_b = client.post(
        "/api/classroom/join",
        json={"join_code": cls_b["join_code"], "nickname": "StuB_01"},
    ).json()

    return {
        "class_a": cls_a["class_id"],
        "class_b": cls_b["class_id"],
        "asg_a": asg_a["assignment_id"],
        "roles": {
            "guest": {},
            "expert": {"Authorization": "Bearer expert-not-classroom-token"},
            "student_own": {"Authorization": f"Bearer {stu_a['student_token']}"},
            "student_other": {"Authorization": f"Bearer {stu_b['student_token']}"},
            "teacher_own": hdr_ta,
            "teacher_other": hdr_tb,
        },
    }


def test_section_13_2_permission_matrix_zero_unauthorised_access(client):
    world = _setup_world(client)
    c_a = world["class_a"]
    a_a = world["asg_a"]
    roles = world["roles"]

    # Matrix: (method, path, payload, allowed_roles_with_200, cross_tenant_403_roles)
    matrix = [
        ("POST", "/api/classroom/classes", {"name": "NewCls"}, {"teacher_own", "teacher_other"}, set()),
        ("GET", "/api/classroom/classes", None, {"teacher_own", "teacher_other"}, set()),
        ("POST", f"/api/classroom/classes/{c_a}/reset-code", None, {"teacher_own"}, {"teacher_other"}),
        ("GET", f"/api/classroom/classes/{c_a}/roster", None, {"teacher_own"}, {"teacher_other"}),
        ("GET", f"/api/classroom/classes/{c_a}/submissions", None, {"teacher_own"}, {"teacher_other"}),
        ("GET", f"/api/classroom/classes/{c_a}/analytics", None, {"teacher_own"}, {"teacher_other"}),
        ("GET", f"/api/classroom/classes/{c_a}/export.csv", None, {"teacher_own"}, {"teacher_other"}),
        ("POST", f"/api/classroom/classes/{c_a}/assignments", {"experiment_id": "pk_ward", "title": "Assignment X"}, {"teacher_own"}, {"teacher_other"}),
        ("GET", f"/api/classroom/classes/{c_a}/assignments", None, {"teacher_own"}, {"teacher_other"}),
        ("GET", "/api/classroom/student/assignments", None, {"student_own", "student_other"}, set()),
        # Submit: auth check only (422 from business logic is acceptable for student_own with fake session_id)
        ("POST", f"/api/classroom/student/assignments/{a_a}/submit", {"session_id": "s1"}, {"student_own"}, {"student_other"}),
        ("GET", "/api/classroom/student/results", None, {"student_own", "student_other"}, set()),
        ("GET", "/api/classroom/student/leaderboard", None, {"student_own", "student_other"}, set()),
        ("POST", "/api/classroom/student/leaderboard-opt-in", {"opt_in": True}, {"student_own", "student_other"}, set()),
        # Delete tested last
        ("DELETE", f"/api/classroom/classes/{c_a}", None, {"teacher_own"}, {"teacher_other"}),
    ]

    for method, path, payload, allowed, cross_tenant_forbidden in matrix:
        for role_name in ("guest", "expert", "student_own", "student_other", "teacher_other", "teacher_own"):
            hdrs = roles[role_name]
            resp = client.request(method, path, json=payload, headers=hdrs)
            if role_name in allowed:
                assert resp.status_code in (200, 201, 409, 422), (
                    f"{role_name} expected 2xx/4xx-business on {method} {path}, got {resp.status_code}: {resp.text}"
                )
            elif role_name in cross_tenant_forbidden:
                expected_code = 404 if role_name == "teacher_other" else 403
                assert resp.status_code == expected_code, f"{role_name} expected {expected_code} on {method} {path}, got {resp.status_code}"
            else:
                assert resp.status_code == 401, f"{role_name} expected 401 on {method} {path}, got {resp.status_code}"


def test_auth_rate_limit_spoofed_xff_and_student_token_expiry(client):
    rate_limiter._buckets.clear()
    # Spoofed X-Forwarded-For with TRUST_PROXY=False must NOT bypass the 15/min auth bucket
    for i in range(15):
        r = client.post(
            "/api/classroom/teacher/redeem",
            json={"invite_token": "invalid-token-12345"},
            headers={"X-Forwarded-For": f"10.0.0.{i + 1}"},
        )
        assert r.status_code == 401
    r_16 = client.post(
        "/api/classroom/teacher/redeem",
        json={"invite_token": "invalid-token-12345"},
        headers={"X-Forwarded-For": "10.0.0.99"},
    )
    assert r_16.status_code == 429

    # Expired student token is rejected
    expired_raw = "expired-stu-tok-123"
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    asyncio.run(db_mod.database["student_sessions"].insert_one(
        StudentSessionRecord(
            token_hash=hash_secret(expired_raw),
            student_id="stu-exp",
            class_id="cls-exp",
            nickname="ExpStu",
            expires_at=past,
        ).model_dump()
    ))
    res = client.get("/api/classroom/student/assignments", headers={"Authorization": f"Bearer {expired_raw}"})
    assert res.status_code == 401
