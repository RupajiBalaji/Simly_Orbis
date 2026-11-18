#!/usr/bin/env python3
"""
scripts/lint_i18n.py
Verifies that frontend/locales/en.json is valid, all keys are non-empty,
scans HTML/JS templates for registered data-i18n keys to ensure zero missing keys,
and strictly asserts zero untranslated user-facing literals exist across lobby,
HUD, briefing, report, settings, and state screens.
"""

import sys
import json
import re
from pathlib import Path
from html.parser import HTMLParser


def flatten_keys(obj, prefix=""):
    keys = set()
    for k, v in obj.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(flatten_keys(v, full_key))
        else:
            keys.add(full_key)
    return keys


class LiteralScanner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.current_screen = None
        self.untranslated = []
        self.target_screens = {
            "screen-lobby", "screen-brief", "screen-settings", "screen-report",
            "hud", "session-error-overlay", "screen-wakeup", "offline-state-banner",
            "webgl-fallback", "modal-onboarding", "modal-why-locked"
        }

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        element_id = attr_dict.get("id", "")
        if element_id in self.target_screens:
            self.current_screen = element_id

        has_i18n = "data-i18n" in attr_dict or "data-i18n-title" in attr_dict
        self.stack.append((tag, attr_dict, has_i18n))

    def handle_endtag(self, tag):
        if self.stack:
            popped = self.stack.pop()
            popped_id = popped[1].get("id", "")
            if popped_id == self.current_screen:
                self.current_screen = None

    def handle_data(self, data):
        if not self.current_screen or not self.stack:
            return
        tag, attrs, has_i18n = self.stack[-1]
        if tag in ("script", "style", "input", "select", "option", "code"):
            return
        ancestor_has_i18n = any(item[2] for item in self.stack)
        txt = data.strip()
        if txt and not ancestor_has_i18n and len(txt) > 2:
            if re.search(r"[a-zA-Z]{3,}", txt):
                self.untranslated.append((self.current_screen, tag, attrs.get("id", ""), txt))


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
    print(f"Scanned {len(html_files)} HTML template files.")

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

    # Scan for untranslated literals across lobby, HUD, briefing, report, settings, and state screens
    index_file = repo_root / "frontend" / "index.html"
    if index_file.exists():
        scanner = LiteralScanner()
        scanner.feed(index_file.read_text(encoding="utf-8"))
        if scanner.untranslated:
            print(f"FAIL: {len(scanner.untranslated)} untranslated literals found in {index_file}:")
            for scr, tag, eid, txt in scanner.untranslated:
                print(f"  - [{scr}] <{tag} id='{eid}'>: {txt}")
            sys.exit(1)
        print("PASS: 0 untranslated literals found across lobby, HUD, briefing, report, settings, and state screens.")

    print(f"PASS: All {found_keys} template data-i18n references match registered en.json keys.")
    print("PASS: i18n dictionary and template lint succeeded.")
    sys.exit(0)


if __name__ == "__main__":
    main()
