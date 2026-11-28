"""
P8: Apply human-verified provenance updates from an external worksheet (--file).

Governance rules:
- Never invents reviewer names, dates, or values.
- Only accepts explicit `name:YYYY-MM-DD` format for `verified_by` and `YYYY-MM-DD` for `retrieved_on`.
- Never touches any `*tolerances*` file.
- Only updates `verified_by` and `retrieved_on` columns for matching row IDs.
- Appends an audit trail entry to `validation/verification_log.csv`.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = ROOT / "validation" / "data"
DEFAULT_LOG_PATH = ROOT / "validation" / "verification_log.csv"

_VERIFIED_BY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9 ._'-]{1,60}):(\d{4}-\d{2}-\d{2})$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DISALLOWED_NAMES = {"auto", "agent", "ai", "bot", "claude", "gemini", "gpt", "llm", "unverified", "tbd", "n/a", "none", "unknown"}


def validate_verified_by(value: str) -> tuple[str, str]:
    """Validate `name:YYYY-MM-DD` format and return (reviewer_name, date_str)."""
    raw = (value or "").strip()
    m = _VERIFIED_BY_RE.match(raw)
    if not m:
        raise ValueError(
            f"Invalid verified_by '{value}'. Expected 'ReviewerName:YYYY-MM-DD' (e.g. 'Dr. Sharma:2026-11-28')."
        )
    name, date_str = m.group(1).strip(), m.group(2)
    if name.lower() in _DISALLOWED_NAMES:
        raise ValueError(f"Disallowed placeholder/automated reviewer name '{name}'. A real human reviewer is required.")
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Invalid calendar date in verified_by: '{date_str}'.") from exc
    return name, date_str


def validate_retrieved_on(value: str) -> str:
    """Validate `YYYY-MM-DD` retrieval date."""
    raw = (value or "").strip()
    if not _DATE_RE.match(raw):
        raise ValueError(f"Invalid retrieved_on '{value}'. Expected 'YYYY-MM-DD'.")
    try:
        datetime.strptime(raw, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Invalid calendar date in retrieved_on: '{raw}'.") from exc
    return raw


def _load_worksheet(file_path: Path) -> list[dict[str, Any]]:
    if not file_path.exists():
        raise FileNotFoundError(f"Worksheet file not found: {file_path}")
    if "tolerances" in file_path.name.lower():
        raise ValueError(f"Refusing to read/modify tolerances file: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix == ".json":
        data = json.loads(file_path.read_text(encoding="utf-8"))
        rows = data if isinstance(data, list) else data.get("rows", [])
        if not isinstance(rows, list):
            raise ValueError("JSON worksheet must be a list of objects or contain a 'rows' list.")
        return rows
    if suffix == ".csv":
        with file_path.open("r", encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))
    raise ValueError(f"Unsupported worksheet format '{suffix}'. Use .csv or .json.")


def apply_verification(
    worksheet_path: Path,
    *,
    data_dir: Path = DEFAULT_DATA_DIR,
    log_path: Path = DEFAULT_LOG_PATH,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Validate and apply human verification entries from a worksheet."""
    if "tolerances" in str(data_dir).lower() or "tolerances" in str(log_path).lower():
        raise ValueError("Refusing to touch tolerances paths.")

    entries = _load_worksheet(worksheet_path)
    if not entries:
        raise ValueError("Worksheet contains no verification entries.")

    updates_by_id: dict[str, tuple[str, str]] = {}
    for entry in entries:
        decision = str(entry.get("decision", "confirm")).strip().lower()
        if decision in ("disagree", "skip", "reject"):
            continue
        row_id = str(entry.get("id", "")).strip()
        if not row_id:
            raise ValueError("Worksheet entry missing 'id'.")
        verified_by = str(entry.get("verified_by", "")).strip()
        retrieved_on = str(entry.get("retrieved_on", "")).strip()
        validate_verified_by(verified_by)
        validate_retrieved_on(retrieved_on)
        updates_by_id[row_id] = (verified_by, retrieved_on)

    if not updates_by_id:
        return {"updated_count": 0, "dry_run": dry_run, "matched_ids": []}

    matched_ids: list[str] = []
    log_rows: list[list[str]] = []
    now_utc = datetime.now(timezone.utc).isoformat()

    for csv_path in sorted(data_dir.glob("*.csv")):
        if "tolerances" in csv_path.name.lower():
            raise ValueError(f"Refusing to touch tolerances file: {csv_path}")
        with csv_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            fieldnames = reader.fieldnames
            if not fieldnames:
                continue
            rows = list(reader)

        changed = False
        for row in rows:
            rid = row.get("id", "")
            if rid in updates_by_id:
                vb, ro = updates_by_id[rid]
                row["verified_by"] = vb
                row["retrieved_on"] = ro
                changed = True
                matched_ids.append(rid)
                log_rows.append([now_utc, rid, csv_path.name, vb, ro, "verified"])

        if changed and not dry_run:
            with csv_path.open("w", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

    missing = sorted(set(updates_by_id.keys()) - set(matched_ids))
    if missing:
        raise ValueError(f"Worksheet contains unknown row IDs not found in {data_dir}: {missing}")

    if not dry_run and log_rows:
        log_exists = log_path.exists()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            if not log_exists:
                writer.writerow(["timestamp_utc", "row_id", "file", "verified_by", "retrieved_on", "action"])
            writer.writerows(log_rows)

    return {
        "updated_count": len(matched_ids),
        "dry_run": dry_run,
        "matched_ids": matched_ids,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply human verification worksheet to validation CSVs.")
    parser.add_argument("--file", required=True, help="Path to CSV or JSON verification worksheet.")
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing files.")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), help="Validation CSV directory.")
    parser.add_argument("--log-file", default=str(DEFAULT_LOG_PATH), help="Audit log CSV path.")
    args = parser.parse_args(argv)

    try:
        result = apply_verification(
            Path(args.file),
            data_dir=Path(args.data_dir),
            log_path=Path(args.log_file),
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
