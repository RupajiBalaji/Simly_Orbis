"""
Unit tests for proof image uniqueness checker (backend/tests/test_proof_unique.py).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from scripts.check_proof_unique import check_proof_directory, check_proof_files


def test_proof_unique_passing_set():
    """Directory with unique non-empty files passes validation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        p = Path(tmp_dir)

        # Create distinct test images
        img1 = Image.fromarray(np.zeros((64, 64, 3), dtype=np.uint8))
        img2 = Image.fromarray(np.full((64, 64, 3), 200, dtype=np.uint8))
        img1.save(p / "shot1.png")
        img2.save(p / "shot2.png")
        (p / "video.webm").write_bytes(b"video_stream_alpha")

        passed, md_table, msgs = check_proof_directory(p)
        assert passed is True
        assert "**Proof Uniqueness Overall:** PASS" in md_table
        assert any("strictly non-empty, unique" in m for m in msgs)


def test_proof_unique_failing_set_duplicate():
    """Directory with identical file contents fails validation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        p = Path(tmp_dir)
        (p / "shot_a.png").write_bytes(b"identical_png_bytes_alpha")
        (p / "shot_b.png").write_bytes(b"identical_png_bytes_alpha")

        passed, md_table, msgs = check_proof_directory(p)
        assert passed is False
        assert "FAIL (COLLISION" in md_table
        assert any("duplicate hash collisions" in m for m in msgs)


def test_proof_unique_failing_set_near_duplicate():
    """Directory with two visually almost identical images (difference < 0.1%) fails validation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        p = Path(tmp_dir)

        # Base image
        arr1 = np.full((100, 100, 3), 128, dtype=np.uint8)
        # Almost identical image (only 1 pixel changed by 1 level)
        arr2 = arr1.copy()
        arr2[0, 0, 0] = 129

        Image.fromarray(arr1).save(p / "frame1.png")
        Image.fromarray(arr2).save(p / "frame2.png")

        passed, md_table, msgs = check_proof_directory(p)
        assert passed is False
        assert "suspiciously identical frame pairs" in " ".join(msgs)


def test_proof_unique_failing_set_empty():
    """Directory with 0-byte file fails validation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        p = Path(tmp_dir)
        (p / "empty.png").write_bytes(b"")
        (p / "good.png").write_bytes(b"data_stream")

        passed, md_table, msgs = check_proof_directory(p)
        assert passed is False
        assert any("empty files" in m for m in msgs)
