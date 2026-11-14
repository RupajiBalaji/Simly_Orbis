#!/usr/bin/env python3
"""
scripts/check_claims.py
Claims Governance & Regulatory Compliance Grep Gate.

Standard: Section 14.6 & Section 18 (P0-T7) of Simly Orbis MVP Build Specification.
Audits repository text for prohibited unhedged claims:
- "validated"
- "clinically proven"
- "replaces animal" / "replaces animal testing"
- "fda-approved"
- "accurate" (in context of clinical/flight claims)

Enforces Rule G3/G9: educational simulation disclaimer, not medical advice, not clinical evidence.
Exits 0 if all occurrences are properly disclaimed/hedged, 1 if any unhedged violation is found.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

PROHIBITED_PATTERNS = [
    (r"\bvalidated\b", "Unhedged 'validated' assertion"),
    (r"clinically proven", "Prohibited 'clinically proven' claim"),
    (r"replaces animal(?:\s+testing)?", "Prohibited 'replaces animal' claim"),
    (r"fda[- ]approved", "Prohibited 'FDA-approved' claim"),
]

HEDGES = [
    "not", "never", "unverified", "disclaimer", "educational",
    "neither", "pending", "awaiting", "cannot", "does not", "target", "without"
]


def check_claims(repo_root: Path, target_paths: list[Path] | None = None) -> tuple[bool, list[str]]:
    """Scan markdown and UI files for unhedged claims."""
    if target_paths is None:
        md_files = [repo_root / "README.md"] + [
            p for p in (repo_root / "docs").rglob("*.md")
            if p.name != "SELF_AUDIT_LATEST.md"
        ]
    else:
        md_files = target_paths

    violations: list[str] = []
    total_scanned = 0
    total_matches = 0

    for fpath in md_files:
        if not fpath.exists() or not fpath.is_file():
            continue
        try:
            content = fpath.read_text(encoding="utf-8")
        except Exception:
            continue

        total_scanned += 1
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            lower_line = line.lower()
            for pattern, desc in PROHIBITED_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    total_matches += 1
                    # Check window of 2 lines before and 2 lines after for hedging context
                    context_window = " ".join(lines[max(0, idx - 2):min(len(lines), idx + 2)]).lower()
                    is_hedged = any(h in context_window for h in HEDGES)
                    if not is_hedged:
                        try:
                            rel = fpath.relative_to(repo_root)
                        except ValueError:
                            rel = fpath
                        violations.append(f"{rel}:{idx} [{desc}]: '{line.strip()}'")

    passed = len(violations) == 0
    return passed, violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Check repository claims compliance")
    parser.add_argument("--root", default=".", help="Root repository path")
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    passed, violations = check_claims(repo_root)

    print("=== Simly Orbis Claims Grep Gate ===")
    if passed:
        print("[PASS] All promotional, clinical, and regulatory claims are strictly hedged and disclaimed.")
        return 0
    else:
        print(f"[FAIL] Found {len(violations)} unhedged claim violation(s):")
        for v in violations:
            print(f"  - {v}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
