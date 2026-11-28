"""
A2: Nickname uniqueness per class (case-insensitive).
A3: Join code lookup by indexed hash (no full scan).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app import db as db_mod
from app.classroom.models import ClassRecord
from app.classroom.security import hash_secret
from app.main import app
from app.security import rate_limiter


@pytest.fixture
def client():
    with TestClient(app) as c:
        rate_limiter._buckets.clear()
        yield c


def _seed_class(class_id: str, code: str) -> None:
    exp = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    rec = ClassRecord(
        class_id=class_id,
        teacher_id="tch-unique-nick",
        name="Uniqueness Test Class",
        join_code_hash=hash_secret(code),
        join_code_expires_at=exp,
        active=True,
    )
    asyncio.run(db_mod.database["classes"].insert_one(rec.model_dump()))


def test_duplicate_nickname_same_class_rejected(client: TestClient) -> None:
    """Joining with an already-used nickname (case-insensitive) in the same class returns 409."""
    _seed_class("cls-nick-unique", "NUNIQ1")

    # First join succeeds
    r1 = client.post("/api/classroom/join", json={"join_code": "NUNIQ1", "nickname": "Darwin"})
    assert r1.status_code == 200, r1.text

    # Same nickname same class → 409
    r2 = client.post("/api/classroom/join", json={"join_code": "NUNIQ1", "nickname": "Darwin"})
    assert r2.status_code == 409, f"Expected 409 for duplicate nickname, got {r2.status_code}"

    # Case-insensitive duplicate → 409
    r3 = client.post("/api/classroom/join", json={"join_code": "NUNIQ1", "nickname": "darwin"})
    assert r3.status_code == 409, f"Expected 409 for case-insensitive duplicate, got {r3.status_code}"

    # Different nickname in same class → 200
    r4 = client.post("/api/classroom/join", json={"join_code": "NUNIQ1", "nickname": "Darwin2"})
    assert r4.status_code == 200, f"Different nickname should work, got {r4.status_code}: {r4.text}"


def test_same_nickname_different_classes_allowed(client: TestClient) -> None:
    """The same nickname is allowed in two different classes."""
    _seed_class("cls-nick-a", "NICKA1")
    _seed_class("cls-nick-b", "NICKB1")

    # Join class A
    r1 = client.post("/api/classroom/join", json={"join_code": "NICKA1", "nickname": "Curie"})
    assert r1.status_code == 200, r1.text

    # Join class B with same nickname → should succeed
    r2 = client.post("/api/classroom/join", json={"join_code": "NICKB1", "nickname": "Curie"})
    assert r2.status_code == 200, f"Same nickname in different class should succeed: {r2.text}"


def test_indexed_join_code_lookup_correctness(client: TestClient) -> None:
    """Indexed lookup by join_code_hash returns correct class (not just first match)."""
    # Seed multiple classes; indexed lookup must return the right one
    for i in range(5):
        _seed_class(f"cls-idx-{i}", f"IDX{i:04d}")

    # Join using the third class's code
    r = client.post("/api/classroom/join", json={"join_code": "IDX0002", "nickname": "IndexTester"})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    assert r.json()["class_id"] == "cls-idx-2"


def test_profanity_false_positives_allowed(client: TestClient) -> None:
    """Names like 'Essex' and 'Dickens' must NOT be blocked (whole-token matching)."""
    from app.classroom.security import validate_nickname

    for name in ("Essex", "Dickens", "Cocktail_lover", "Sextet_fan"):
        ok, result = validate_nickname(name)
        # We expect these to pass since the filter uses token-only matching now
        # Essex, Dickens → fine; Cocktail_lover, Sextet_fan → fine (tokens: cocktail_lover, sextet_fan)
        # Note: 'sex' as a standalone token would still be blocked; 'sextet' is not in profanity list
        # We just check they're not false-positives from substring matching in collapsed string
        # The key ones to verify: Essex (tokens: ["essex"]) and Dickens (tokens: ["dickens"])
        assert ok, f"'{name}' should be accepted by nickname filter but got error: {result}"
