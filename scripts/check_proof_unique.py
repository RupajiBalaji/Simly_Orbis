#!/usr/bin/env python3
"""
scripts/check_proof_unique.py
Verifies proof uniqueness across image and video files.

Behavior:
- Accepts a directory (or list of files) as argument.
- Recursively finds all .png, .jpg, .jpeg, .webp, .webm, .mp4 files.
- Computes SHA-256 (and MD5) for each.
- Detects duplicate hashes.
- Computes pairwise pixel MAE between images of identical dimensions to flag near-duplicate frames (< 0.1% diff).
- Outputs a Markdown table and exits 0 on unique, 1 on duplicate/near-duplicate/empty.

Educational simulation platform. Not medical advice. Not clinical evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Sequence

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

try:
    import numpy as np
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


def compute_hashes(file_path: Path) -> tuple[str, str]:
    """Return (sha256, md5) hex strings for file."""
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
            md5.update(chunk)
    return sha256.hexdigest(), md5.hexdigest()


def compute_image_mae_exact(p1: Path, p2: Path) -> float | None:
    """Compute normalized Mean Absolute Error (0.0 to 1.0) between full-resolution images."""
    if not HAS_PILLOW:
        return None
    try:
        with Image.open(p1) as img1, Image.open(p2) as img2:
            if img1.size != img2.size:
                return None
            arr1 = np.array(img1.convert("RGB"), dtype=float)
            arr2 = np.array(img2.convert("RGB"), dtype=float)
            return float(np.mean(np.abs(arr1 - arr2)) / 255.0)
    except Exception:
        return None


def check_proof_files(files: Sequence[Path]) -> tuple[bool, str, list[str]]:
    """
    Scan list of media files, assert non-empty, strictly unique hashes,
    and pairwise distinct image contents (MAE >= 0.001).

    Returns:
        (passed, markdown_report, log_messages)
    """
    messages: list[str] = []
    if not files:
        return False, "No files evaluated.", ["Error: No files provided for proof check."]

    seen_sha: dict[str, Path] = {}
    duplicates: list[tuple[Path, Path, str]] = []
    empty_files: list[Path] = []
    file_records: list[dict] = []

    for f in sorted(files):
        if not f.exists() or not f.is_file():
            continue
        size = f.stat().st_size
        if size == 0:
            empty_files.append(f)
            file_records.append({
                "path": f,
                "name": f.name,
                "size": 0,
                "sha256": "EMPTY_FILE",
                "md5": "EMPTY_FILE",
                "status": "FAIL (0 bytes)"
            })
            continue

        sha_val, md5_val = compute_hashes(f)
        status = "OK"
        if sha_val in seen_sha:
            duplicates.append((f, seen_sha[sha_val], sha_val))
            status = f"FAIL (COLLISION with {seen_sha[sha_val].name})"
        else:
            seen_sha[sha_val] = f

        file_records.append({
            "path": f,
            "name": f.name,
            "size": size,
            "sha256": sha_val,
            "md5": md5_val,
            "status": status
        })

    # Perceptual near-duplicate check for images (MAE < 0.1% -> 0.001)
    near_duplicates: list[tuple[Path, Path, float]] = []
    image_exts = {".png", ".jpg", ".jpeg", ".webp"}
    image_records = [r for r in file_records if r["path"].suffix.lower() in image_exts and r["size"] > 0]

    # Pre-cache thumbnails for fast screening
    cached_thumbs: dict[Path, tuple[tuple[int, int], np.ndarray] | None] = {}
    if HAS_PILLOW:
        for ir in image_records:
            try:
                with Image.open(ir["path"]) as img:
                    orig_size = img.size
                    thumb_arr = np.array(img.convert("RGB").resize((96, 96)), dtype=float)
                    cached_thumbs[ir["path"]] = (orig_size, thumb_arr)
            except Exception:
                cached_thumbs[ir["path"]] = None

    for i in range(len(image_records)):
        for j in range(i + 1, len(image_records)):
            r1, r2 = image_records[i], image_records[j]
            if r1["sha256"] == r2["sha256"]:
                continue
            c1 = cached_thumbs.get(r1["path"])
            c2 = cached_thumbs.get(r2["path"])
            if not c1 or not c2:
                continue
            # If dimensions differ, they cannot be identical frames
            if c1[0] != c2[0]:
                continue
            thumb_mae = float(np.mean(np.abs(c1[1] - c2[1])) / 255.0)
            # Screen with thumbnail: only compute full MAE if thumbnail diff is tiny (< 1%)
            if thumb_mae < 0.01:
                full_mae = compute_image_mae_exact(r1["path"], r2["path"])
                if full_mae is not None and full_mae < 0.001:
                    near_duplicates.append((r1["path"], r2["path"], full_mae))
                    r1["status"] = f"FAIL (NEAR-DUPLICATE of {r2['name']}, MAE={full_mae:.4f})"
                    r2["status"] = f"FAIL (NEAR-DUPLICATE of {r1['name']}, MAE={full_mae:.4f})"

    passed = (len(empty_files) == 0 and len(duplicates) == 0 and len(near_duplicates) == 0)

    # Build Markdown table
    md_lines: list[str] = [
        "| File | Size (bytes) | SHA-256 (first 16) | MD5 | Status |",
        "| :--- | :---: | :--- | :--- | :---: |",
    ]
    for r in file_records:
        short_sha = r["sha256"][:16] + "..." if len(r["sha256"]) > 16 else r["sha256"]
        short_md5 = r["md5"][:16] + "..." if len(r["md5"]) > 16 else r["md5"]
        md_lines.append(f"| `{r['name']}` | {r['size']:,} | `{short_sha}` | `{short_md5}` | {r['status']} |")

    summary_status = "PASS" if passed else "FAIL"
    md_lines.append("")
    md_lines.append(f"**Proof Uniqueness Overall:** {summary_status} ({len(file_records)} files checked, {len(duplicates)} hash collisions, {len(near_duplicates)} near-duplicates)")

    md_table = "\n".join(md_lines)

    messages.append(f"Evaluated {len(file_records)} proof media files.")
    if empty_files:
        messages.append(f"FAILED: Found {len(empty_files)} empty files:")
        for ef in empty_files:
            messages.append(f"  - {ef.name}")
    if duplicates:
        messages.append(f"FAILED: Found {len(duplicates)} duplicate hash collisions:")
        for f1, f2, h in duplicates:
            messages.append(f"  - {f1.name} == {f2.name} (SHA-256: {h})")
    if near_duplicates:
        messages.append(f"FAILED: Found {len(near_duplicates)} suspiciously identical frame pairs (MAE < 0.1%):")
        for f1, f2, diff in near_duplicates:
            messages.append(f"  - {f1.name} ~ {f2.name} (MAE: {diff:.6f})")
    if passed:
        messages.append(f"PASSED: All {len(file_records)} files are strictly non-empty, unique, and perceptually distinct.")

    return passed, md_table, messages


def check_proof_directory(target_dir: Path) -> tuple[bool, str, list[str]]:
    """Recursively collect media files from directory and run check_proof_files."""
    if not target_dir.exists() or not target_dir.is_dir():
        return False, "", [f"Error: Target directory does not exist: {target_dir}"]

    extensions = {".png", ".jpg", ".jpeg", ".webp", ".webm", ".mp4"}
    files = [p for p in target_dir.rglob("*") if p.is_file() and p.suffix.lower() in extensions]
    if not files:
        return False, "", [f"Error: No media files found in {target_dir}"]

    return check_proof_files(files)


def get_latest_qa_dir(root_dir: Path) -> Path | None:
    qa_out = root_dir / "qa" / "out"
    if not qa_out.exists():
        return None
    subdirs = [p for p in qa_out.iterdir() if p.is_dir()]
    if not subdirs:
        return None
    subdirs.sort(key=lambda p: p.name, reverse=True)
    return subdirs[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Simly Orbis Proof Uniqueness Checker")
    parser.add_argument("paths", nargs="*", help="Directories or files to check (defaults to latest qa/out)")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent.parent
    if args.paths:
        target_paths = [Path(p).resolve() for p in args.paths]
        if len(target_paths) == 1 and target_paths[0].is_dir():
            passed, md_table, msgs = check_proof_directory(target_paths[0])
        else:
            files: list[Path] = []
            extensions = {".png", ".jpg", ".jpeg", ".webp", ".webm", ".mp4"}
            for tp in target_paths:
                if tp.is_dir():
                    files.extend([p for p in tp.rglob("*") if p.is_file() and p.suffix.lower() in extensions])
                elif tp.is_file() and tp.suffix.lower() in extensions:
                    files.append(tp)
            passed, md_table, msgs = check_proof_files(files)
    else:
        latest = get_latest_qa_dir(root_dir)
        if not latest:
            print("Error: No qa/out directory found and no paths provided.")
            return 1
        print(f"[PROOF CHECK] Verifying uniqueness in latest QA directory: {latest}")
        passed, md_table, msgs = check_proof_directory(latest)

    print("\n" + md_table + "\n")
    for m in msgs:
        print(f"  {m}")

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
