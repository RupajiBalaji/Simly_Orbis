#!/usr/bin/env python3
"""
scripts/check_contrast.py
WCAG 2.1 AA Contrast Ratio Validator for Simly Orbis Design Tokens.

Standard: Section 7.2 & Section 18 (P1-T1) of Simly Orbis MVP Build Specification.
Computes contrast ratios for every text and background token pair and fails under 4.5:1.
Educational simulation platform. Not medical advice. Not clinical evidence.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
TOKENS_CSS = REPO_ROOT / "frontend" / "styles" / "tokens.css"


def relative_luminance(hex_code: str) -> float:
    """Compute relative luminance according to WCAG 2.1 specification."""
    hex_code = hex_code.strip().lstrip("#")
    if len(hex_code) == 3:
        hex_code = "".join(c * 2 for c in hex_code)
    r = int(hex_code[0:2], 16) / 255.0
    g = int(hex_code[2:4], 16) / 255.0
    b = int(hex_code[4:6], 16) / 255.0

    def adjust(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r_adj, g_adj, b_adj = adjust(r), adjust(g), adjust(b)
    return 0.2126 * r_adj + 0.7152 * g_adj + 0.0722 * b_adj


def contrast_ratio(hex1: str, hex2: str) -> float:
    """Compute contrast ratio between two hex colors (range 1:1 to 21:1)."""
    l1 = relative_luminance(hex1)
    l2 = relative_luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def parse_tokens(css_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Parse dark theme (:root) and light theme ([data-theme="light"]) color tokens."""
    content = css_path.read_text(encoding="utf-8")

    # Extract :root block
    root_match = re.search(r":root\s*\{([^}]+)\}", content, re.DOTALL)
    root_vars = {}
    if root_match:
        for line in root_match.group(1).splitlines():
            m = re.search(r"--([a-zA-Z0-9_-]+)\s*:\s*(#[0-9a-fA-F]{3,6})", line)
            if m:
                root_vars[m.group(1)] = m.group(2)

    # Extract light theme block
    light_match = re.search(r'\[data-theme=["\']light["\']\]\s*\{([^}]+)\}', content, re.DOTALL)
    light_vars = {}
    if light_match:
        for line in light_match.group(1).splitlines():
            m = re.search(r"--([a-zA-Z0-9_-]+)\s*:\s*(#[0-9a-fA-F]{3,6})", line)
            if m:
                light_vars[m.group(1)] = m.group(2)

    return root_vars, light_vars


def evaluate_theme(theme_name: str, tokens: dict[str, str], min_ratio: float = 4.5) -> tuple[bool, list[str]]:
    bg_keys = ["bg", "surface", "surface-2"]
    text_keys = [
        "text",
        "text-muted",
        "accent",
        "accent-chem",
        "accent-space",
        "ok",
        "warn",
        "danger",
        "info",
    ]

    lines = []
    lines.append(f"### Theme: {theme_name.upper()}")
    lines.append(f"| Text Token | Hex | Background | Hex | Contrast Ratio | WCAG 2.1 AA (>= {min_ratio}:1) |")
    lines.append("| :--- | :---: | :--- | :---: | :---: | :---: |")

    all_passed = True
    for t_key in text_keys:
        t_hex = tokens.get(t_key)
        if not t_hex:
            lines.append(f"| `{t_key}` | *missing* | - | - | - | **FAIL (Missing)** |")
            all_passed = False
            continue

        for bg_key in bg_keys:
            bg_hex = tokens.get(bg_key)
            if not bg_hex:
                lines.append(f"| `{t_key}` | `{t_hex}` | `{bg_key}` | *missing* | - | **FAIL (Missing)** |")
                all_passed = False
                continue

            ratio = contrast_ratio(t_hex, bg_hex)
            passed = ratio >= min_ratio
            if not passed:
                all_passed = False
            badge = "**PASS**" if passed else "**FAIL**"
            lines.append(f"| `{t_key}` | `{t_hex}` | `{bg_key}` | `{bg_hex}` | **{ratio:.2f}:1** | {badge} |")

    lines.append("")
    return all_passed, lines


def main() -> int:
    print("=" * 65)
    print("=== Simly Orbis WCAG 2.1 AA Design Token Contrast Validator ===")
    print("=" * 65 + "\n")

    if not TOKENS_CSS.exists():
        print(f"Error: {TOKENS_CSS} does not exist.")
        return 1

    dark_tokens, light_tokens = parse_tokens(TOKENS_CSS)

    dark_ok, dark_lines = evaluate_theme("Dark (Default / MUST)", dark_tokens)
    print("\n".join(dark_lines))

    light_ok, light_lines = evaluate_theme("Light (Optional / SHOULD)", light_tokens)
    print("\n".join(light_lines))

    overall_pass = dark_ok and light_ok
    status_msg = "[PASS] All text-on-background pairs achieve WCAG 2.1 AA >= 4.5:1 contrast." if overall_pass else "[FAIL] One or more token pairs failed contrast threshold."
    print("-" * 65)
    print(status_msg)
    print("-" * 65)

    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
