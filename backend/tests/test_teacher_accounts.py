"""Tests for P6-T3: invite-only teacher accounts, expiring tokens, and reuse prevention."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

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


def test_teacher_invite_redeem_and_reuse_rejected(client):
    invite = asyncio.run(
        create_teacher_invite(db_mod.database, email="rao@school.edu", display_name="Prof. Rao", ttl_minutes=60)
    )
    token = invite["invite_token"]

    # First redemption succeeds
    res1 = client.post("/api/classroom/teacher/redeem", json={"invite_token": token})
    assert res1.status_code == 200, res1.text
    session_token = res1.json()["session_token"]

    # Authenticated /me works
    me = client.get("/api/classroom/teacher/me", headers={"Authorization": f"Bearer {session_token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "rao@school.edu"

    # Second redemption of same invite token is rejected (reuse blocked)
    res2 = client.post("/api/classroom/teacher/redeem", json={"invite_token": token})
    assert res2.status_code == 401


def test_teacher_invite_and_session_expiry(client):
    # Expired invite token
    expired_invite = asyncio.run(
        create_teacher_invite(db_mod.database, email="exp@school.edu", display_name="Prof. Exp", ttl_minutes=-5)
    )
    res_exp = client.post("/api/classroom/teacher/redeem", json={"invite_token": expired_invite["invite_token"]})
    assert res_exp.status_code == 401

    # Valid invite -> manually expire the issued session token
    valid_invite = asyncio.run(
        create_teacher_invite(db_mod.database, email="ok@school.edu", display_name="Prof. Ok", ttl_minutes=30)
    )
    sess = asyncio.run(redeem_teacher_invite(db_mod.database, valid_invite["invite_token"], session_ttl_hours=-1))
    assert sess is not None
    me_exp = client.get("/api/classroom/teacher/me", headers={"Authorization": f"Bearer {sess['session_token']}"})
    assert me_exp.status_code == 401


def test_create_teacher_script_cli(capsys):
    import sys
    from pathlib import Path

    scripts_dir = str(Path(__file__).resolve().parents[2] / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import create_teacher

    rc = create_teacher.main(["--email", "cli@school.edu", "--name", "CLI Teacher", "--ttl-minutes", "15"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "cli@school.edu" in out
    assert "invite_token" in out
