"""Tests for P6-T2: student join by class code and nickname filter."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app import db as db_mod
from app.classroom.models import ClassRecord
from app.classroom.security import hash_secret, validate_nickname
from app.main import app
from app.security import rate_limiter


@pytest.fixture
def client():
    with TestClient(app) as c:
        rate_limiter._buckets.clear()
        yield c


def _seed_class(class_id: str, code: str, *, expired: bool = False, active: bool = True) -> None:
    delta = timedelta(days=-1 if expired else 30)
    exp = (datetime.now(timezone.utc) + delta).isoformat()
    rec = ClassRecord(
        class_id=class_id,
        teacher_id="tch-test-1",
        name="Biology 101",
        join_code_hash=hash_secret(code),
        join_code_expires_at=exp,
        active=active,
    )
    asyncio.run(db_mod.database["classes"].insert_one(rec.model_dump()))


def test_nickname_filter_rejects_bad_inputs():
    bad = [
        "a",
        "student@school.edu",
        "9876543210",
        "https://evil.com",
        "<script>alert(1)</script>",
        "b@d_fuck_name",
        "sh1t_user",
    ]
    for nick in bad:
        ok, _ = validate_nickname(nick)
        assert not ok, f"Expected rejection for {nick!r}"

    ok, cleaned = validate_nickname("  Curie_07  ")
    assert ok
    assert cleaned == "Curie_07"


def test_student_join_valid_invalid_and_expired_codes(client):
    _seed_class("cls-valid", "ORB123")
    _seed_class("cls-exp", "EXP999", expired=True)
    _seed_class("cls-off", "OFF000", active=False)

    # Valid join
    res = client.post("/api/classroom/join", json={"join_code": "orb-123", "nickname": "Curie_07"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["class_id"] == "cls-valid"
    assert body["class_name"] == "Biology 101"
    assert body["nickname"] == "Curie_07"
    assert len(body["student_token"]) > 20

    # Invalid code
    res_bad = client.post("/api/classroom/join", json={"join_code": "NOPE99", "nickname": "Curie_07"})
    assert res_bad.status_code == 404

    # Expired code
    res_exp = client.post("/api/classroom/join", json={"join_code": "EXP999", "nickname": "Curie_07"})
    assert res_exp.status_code == 410

    # Inactive class
    res_off = client.post("/api/classroom/join", json={"join_code": "OFF000", "nickname": "Curie_07"})
    assert res_off.status_code == 404

    # Bad nickname rejected even with valid code
    res_nick = client.post("/api/classroom/join", json={"join_code": "ORB123", "nickname": "alice@example.com"})
    assert res_nick.status_code == 400


def test_student_join_rate_limit(client):
    _seed_class("cls-rl", "RL1234")
    rate_limiter._buckets.clear()
    statuses = []
    for _ in range(16):
        r = client.post("/api/classroom/join", json={"join_code": "NOPE", "nickname": "Curie_01"})
        statuses.append(r.status_code)
    assert statuses[-1] == 429
