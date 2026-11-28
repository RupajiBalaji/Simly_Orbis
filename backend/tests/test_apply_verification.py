"""P8: Tests for scripts/apply_verification.py and read-only /api/validation/review."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from scripts.apply_verification import apply_verification, validate_retrieved_on, validate_verified_by


def _write_sample_csv(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "quantity", "value", "unit", "retrieved_on", "verified_by", "notes"])
        w.writerow(["row_1", "cmax", "8.33", "mg/L", "", "unverified", "orig note"])


def test_refuses_invented_or_placeholder_names(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_sample_csv(data_dir / "sample.csv")

    for bad_name in ("auto:2026-11-28", "agent:2026-11-28", "Claude:2026-11-28", "Dr. Foo", "unverified:2026-11-28"):
        ws = tmp_path / "ws.json"
        ws.write_text(json.dumps([{"id": "row_1", "verified_by": bad_name, "retrieved_on": "2026-11-28"}]), encoding="utf-8")
        with pytest.raises(ValueError):
            apply_verification(ws, data_dir=data_dir, log_path=tmp_path / "log.csv")


def test_validates_date_formats() -> None:
    assert validate_verified_by("Dr. Sharma:2026-11-28") == ("Dr. Sharma", "2026-11-28")
    assert validate_retrieved_on("2026-11-28") == "2026-11-28"
    with pytest.raises(ValueError):
        validate_verified_by("Dr. Sharma:2026-13-40")
    with pytest.raises(ValueError):
        validate_retrieved_on("28-11-2026")


def test_refuses_to_touch_tolerances(tmp_path: Path) -> None:
    tol_ws = tmp_path / "tolerances_patch.json"
    tol_ws.write_text(json.dumps([{"id": "row_1", "verified_by": "Dr. A:2026-11-28", "retrieved_on": "2026-11-28"}]), encoding="utf-8")
    with pytest.raises(ValueError, match="tolerances"):
        apply_verification(tol_ws, data_dir=tmp_path, log_path=tmp_path / "log.csv")


def test_apply_verification_updates_only_provenance_and_appends_log(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    csv_path = data_dir / "sample.csv"
    _write_sample_csv(csv_path)
    log_path = tmp_path / "verification_log.csv"

    ws = tmp_path / "ws.json"
    ws.write_text(
        json.dumps([{"id": "row_1", "verified_by": "Prof. Rao:2026-11-28", "retrieved_on": "2026-11-28"}]),
        encoding="utf-8",
    )

    # Dry-run does not modify CSV or create log
    dry_res = apply_verification(ws, data_dir=data_dir, log_path=log_path, dry_run=True)
    assert dry_res["updated_count"] == 1
    assert not log_path.exists()
    assert "unverified" in csv_path.read_text(encoding="utf-8")

    # Real run updates only verified_by and retrieved_on and appends to log
    res = apply_verification(ws, data_dir=data_dir, log_path=log_path, dry_run=False)
    assert res["updated_count"] == 1
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert rows[0]["verified_by"] == "Prof. Rao:2026-11-28"
    assert rows[0]["retrieved_on"] == "2026-11-28"
    assert rows[0]["value"] == "8.33"
    assert rows[0]["notes"] == "orig note"
    assert log_path.exists()
    assert "Prof. Rao:2026-11-28" in log_path.read_text(encoding="utf-8")


def test_expert_html_and_validation_review_endpoint() -> None:
    with TestClient(app) as client:
        r_html = client.get("/expert.html")
        assert r_html.status_code == 200
        assert "Expert Evidence Review" in r_html.text

        r_api = client.get("/api/validation/review")
        assert r_api.status_code == 200
        body = r_api.json()
        assert body["total"] > 0
        assert body["verified"] == 0
        assert isinstance(body["rows"], list)
