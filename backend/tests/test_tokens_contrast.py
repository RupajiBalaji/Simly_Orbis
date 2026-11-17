"""
backend/tests/test_tokens_contrast.py
Unit tests verifying design tokens contrast ratios and typography per Section 7.2 & P1-T1.

Standard: Section 7.2 of Simly Orbis MVP Build Specification.
- frontend/styles/tokens.css defines standard design tokens.
- All text and background token pairs achieve >= 4.5:1 contrast (WCAG 2.1 AA).
- Self-hosted fonts referenced and present.
"""

from __future__ import annotations

from pathlib import Path
import pytest
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOKENS_CSS = REPO_ROOT / "frontend" / "styles" / "tokens.css"
FONTS_CSS = REPO_ROOT / "frontend" / "vendor" / "fonts" / "fonts.css"


def test_tokens_css_exists_and_declares_tokens():
    """Verify that tokens.css exists and defines mandatory colors, spacing, and typography."""
    assert TOKENS_CSS.exists(), "frontend/styles/tokens.css missing"

    content = TOKENS_CSS.read_text(encoding="utf-8")
    mandatory_vars = [
        "--bg",
        "--surface",
        "--surface-2",
        "--text",
        "--text-muted",
        "--accent",
        "--accent-chem",
        "--accent-space",
        "--ok",
        "--warn",
        "--danger",
        "--info",
        "--space-1",
        "--space-4",
        "--radius-md",
        "--elevation-1",
        "--font-sans",
        "--font-mono",
    ]
    for v in mandatory_vars:
        assert v in content, f"tokens.css missing variable: '{v}'"


def test_self_hosted_fonts_present():
    """Verify that self-hosted font files and stylesheet are present."""
    assert FONTS_CSS.exists(), "frontend/vendor/fonts/fonts.css missing"
    fonts_dir = FONTS_CSS.parent
    woff2_files = list(fonts_dir.glob("*.woff2"))
    assert len(woff2_files) >= 2, f"Expected at least 2 woff2 font files, found {len(woff2_files)}"


def test_contrast_validation_script_passes():
    """Verify that scripts/check_contrast.py executes cleanly and all contrast ratios pass."""
    script_path = REPO_ROOT / "scripts" / "check_contrast.py"
    assert script_path.exists(), "scripts/check_contrast.py missing"

    proc = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"check_contrast.py failed with return code {proc.returncode}:\n{proc.stdout}\n{proc.stderr}"
    assert "[PASS]" in proc.stdout
    assert "WCAG 2.1 AA >= 4.5:1" in proc.stdout
