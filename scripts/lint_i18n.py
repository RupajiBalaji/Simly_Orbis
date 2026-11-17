#!/usr/bin/env python3
"""
scripts/lint_i18n.py
Verifies that frontend/locales/en.json is valid, all keys are non-empty,
and scans HTML/JS templates for registered data-i18n keys to ensure zero missing keys.
"""

import sys
import json
import re
from pathlib import Path


def flatten_keys(obj, prefix=""):
    keys = set()
    for k, v in obj.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(flatten_keys(v, full_key))
        else:
            keys.add(full_key)
    return keys


def main():
    repo_root = Path(__file__).resolve().parent.parent
    en_file = repo_root / "frontend" / "locales" / "en.json"

    if not en_file.exists():
        print(f"FAIL: {en_file} does not exist.")
        sys.exit(1)

    try:
        data = json.loads(en_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FAIL: {en_file} is not valid JSON: {e}")
        sys.exit(1)

    keys = flatten_keys(data)
    print(f"Loaded {len(keys)} registered localization keys from en.json.")

    # Check for empty string values
    def check_empty(obj, prefix=""):
        violations = []
        for k, v in obj.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                violations.extend(check_empty(v, full_key))
            elif isinstance(v, str) and not v.strip():
                violations.append(full_key)
        return violations

    empty = check_empty(data)
    if empty:
        print(f"FAIL: Empty translation strings detected for keys: {empty}")
        sys.exit(1)

    # Scan HTML files for data-i18n usage
    html_files = list((repo_root / "frontend").rglob("*.html"))
    missing = []
    found_keys = 0

    pattern = re.compile(r'data-i18n(?:-title)?=["\']([a-zA-Z0-9_.]+)["\']')

    for hf in html_files:
        content = hf.read_text(encoding="utf-8")
        for match in pattern.finditer(content):
            key = match.group(1)
            found_keys += 1
            if key not in keys:
                missing.append((str(hf.relative_to(repo_root)), key))

    if missing:
        print(f"FAIL: {len(missing)} data-i18n keys referenced in templates are missing from en.json:")
        for file_path, k in missing:
            print(f"  - {file_path}: {k}")
        sys.exit(1)

    print(f"PASS: All {found_keys} template data-i18n references match registered en.json keys.")
    print("PASS: i18n dictionary and template lint succeeded.")
    sys.exit(0)


if __name__ == "__main__":
    main()
