"""
backend/tests/test_proof_gate.py
Tests the semantic proof gate in scripts/check_proof_unique.py.
Verifies rejection of:
- missing sidecars
- planted modal dialogues
- planted solid-color overlays (> 40% uniform pixels)
- element count discrepancies
And verifies acceptance of valid HUD screenshots.

Fast, zero-network, no-browser unit tests.
"""

import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.check_proof_unique import (
    validate_screenshot_semantic,
    check_proof_files,
)


def _create_rich_test_image(path: Path, width: int = 400, height: int = 300) -> None:
    """Generate a synthetic test image with diverse colors so no 8-unit bin exceeds 20%."""
    x = np.linspace(0, 255, width, dtype=np.uint8)
    y = np.linspace(0, 255, height, dtype=np.uint8)
    xx, yy = np.meshgrid(x, y)
    r = xx
    g = yy
    b = ((xx.astype(np.uint16) + yy.astype(np.uint16)) // 2).astype(np.uint8)
    rgb = np.stack([r, g, b], axis=-1)
    img = Image.fromarray(rgb, "RGB")
    img.save(path, format="PNG")


def test_valid_screenshot_passes(tmp_path: Path) -> None:
    img_path = tmp_path / "after_1920x1080.png"
    _create_rich_test_image(img_path, 1920, 1080)

    sidecar_path = tmp_path / "after_1920x1080.json"
    sidecar_data = {
        "scenario": "pk_ward",
        "viewport": {"width": 1920, "height": 1080},
        "visible_persistent_elements_count": 5,
        "modal_count": 0,
        "canvas_frame_count": 60,
    }
    sidecar_path.write_text(json.dumps(sidecar_data), encoding="utf-8")

    ok, reason = validate_screenshot_semantic(img_path)
    assert ok is True, f"Expected pass, got: {reason}"

    passed, report, msgs = check_proof_files([img_path])
    assert passed is True
    assert "PASS" in report
    assert any("PASSED" in m for m in msgs)


def test_missing_sidecar_fails(tmp_path: Path) -> None:
    img_path = tmp_path / "after_1366x768.png"
    _create_rich_test_image(img_path, 1366, 768)
    # Intentionally do NOT create after_1366x768.json

    ok, reason = validate_screenshot_semantic(img_path)
    assert ok is False
    assert "Missing sidecar JSON" in reason

    passed, report, msgs = check_proof_files([img_path])
    assert passed is False
    assert "semantic failures" in report.lower()


def test_planted_modal_screenshot_fails(tmp_path: Path) -> None:
    img_path = tmp_path / "after_768x1024.png"
    _create_rich_test_image(img_path, 768, 1024)

    sidecar_path = tmp_path / "after_768x1024.json"
    sidecar_data = {
        "scenario": "pk_ward",
        "viewport": {"width": 768, "height": 1024},
        "visible_persistent_elements_count": 5,
        "modal_count": 1,  # Planted modal failure!
        "visible_modals": ["Laboratory Controls Walkthrough"],
    }
    sidecar_path.write_text(json.dumps(sidecar_data), encoding="utf-8")

    ok, reason = validate_screenshot_semantic(img_path)
    assert ok is False
    assert "modal_count=1" in reason

    passed, report, msgs = check_proof_files([img_path])
    assert passed is False
    assert "modal_count=1" in "".join(msgs)


def test_planted_solid_color_screenshot_fails(tmp_path: Path) -> None:
    img_path = tmp_path / "after_390x844.png"
    # Create solid white blank overlay
    solid_img = Image.new("RGB", (390, 844), color=(255, 255, 255))
    solid_img.save(img_path, format="PNG")

    sidecar_path = tmp_path / "after_390x844.json"
    sidecar_data = {
        "scenario": "pk_ward",
        "viewport": {"width": 390, "height": 844},
        "visible_persistent_elements_count": 5,
        "modal_count": 0,
    }
    sidecar_path.write_text(json.dumps(sidecar_data), encoding="utf-8")

    ok, reason = validate_screenshot_semantic(img_path)
    assert ok is False
    assert "Color bin" in reason or "outside bounds" in reason

    passed, report, msgs = check_proof_files([img_path])
    assert passed is False


def test_corrupted_sidecar_json_fails(tmp_path: Path) -> None:
    img_path = tmp_path / "after_corrupt.png"
    _create_rich_test_image(img_path, 800, 600)

    sidecar_path = tmp_path / "after_corrupt.json"
    sidecar_path.write_text("{broken json syntax: unclosed", encoding="utf-8")

    ok, reason = validate_screenshot_semantic(img_path)
    assert ok is False
    assert "failed to parse" in reason.lower()


def test_wrong_element_count_fails(tmp_path: Path) -> None:
    img_path = tmp_path / "after_bad_elements.png"
    _create_rich_test_image(img_path, 800, 600)

    sidecar_path = tmp_path / "after_bad_elements.json"
    sidecar_data = {
        "scenario": "pk_ward",
        "viewport": {"width": 800, "height": 600},
        "visible_persistent_elements_count": 8,  # Expected 5 for after_*
        "modal_count": 0,
    }
    sidecar_path.write_text(json.dumps(sidecar_data), encoding="utf-8")

    ok, reason = validate_screenshot_semantic(img_path)
    assert ok is False
    assert "persistent_elements=8" in reason
