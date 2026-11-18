#!/usr/bin/env python3
"""
Simly Orbis — Experiment Specification Validator CLI
Validates experiment spec files (.json, .yaml, .yml) against Section 10 schema and business rules.

Usage:
    python scripts/validate_specs.py [paths...]
    python scripts/validate_specs.py specs/
    python scripts/validate_specs.py specs/titration.json
"""

import argparse
import sys
from pathlib import Path

# Add backend directory to sys.path so app modules import cleanly
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.specs.loader import load_and_validate_spec, SpecLoadError
from app.specs.validator import ValidationReport


def find_spec_files(paths: list[str]) -> list[Path]:
    """Resolve argument paths to a sorted list of spec files."""
    files: list[Path] = []
    if not paths:
        default_dir = REPO_ROOT / "specs"
        if default_dir.is_dir():
            paths = [str(default_dir)]
        else:
            return []

    for p_str in paths:
        p = Path(p_str)
        if p.is_file() and p.suffix.lower() in (".json", ".yaml", ".yml"):
            files.append(p)
        elif p.is_dir():
            for ext in ("*.json", "*.yaml", "*.yml"):
                files.extend(p.glob(ext))
    return sorted(set(files))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Simly Orbis experiment specifications.")
    parser.add_argument("paths", nargs="*", help="File or directory paths to validate. Defaults to specs/")
    parser.add_argument("--quiet", action="store_true", help="Only output errors.")
    args = parser.parse_args()

    files = find_spec_files(args.paths)
    if not files:
        if not args.quiet:
            print("No spec files found to validate.")
        return 0

    total_files = len(files)
    passed_count = 0
    failed_count = 0

    print(f"Validating {total_files} experiment specification(s)...")
    print("=" * 60)

    for fpath in files:
        rel_path = fpath.relative_to(REPO_ROOT) if fpath.is_relative_to(REPO_ROOT) else fpath
        try:
            spec, report = load_and_validate_spec(fpath)
            if report.valid and spec is not None:
                passed_count += 1
                if not args.quiet:
                    print(f"[PASS] {rel_path} ({spec.id} v{spec.version})")
            else:
                failed_count += 1
                print(f"[FAIL] {rel_path} (id: {report.spec_id or 'unknown'})")
                for err in report.errors:
                    print(f"  - {err.path}: {err.message}")
        except SpecLoadError as exc:
            failed_count += 1
            print(f"[ERROR] {rel_path}: {exc}")

    print("=" * 60)
    print(f"Summary: {passed_count}/{total_files} passed, {failed_count} failed.")

    return 1 if failed_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
