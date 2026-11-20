"""
backend/tests/test_dependencies.py
Verification of pinned dependencies from security audit (Task H3).

Verifies:
1. Every package in backend/requirements.txt and backend/requirements-dev.txt is pinned with '=='.
2. The security audit updates from commit 261813a are present and pinned:
   - fastapi == 0.115.14
   - python-dotenv == 1.2.4
   - Pillow == 13.0.0
3. CI and Dockerfile install from the pinned requirements files.
"""

from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_requirements_strictly_pinned():
    """Every dependency requirement must be pinned to an exact version with '=='."""
    req_files = [
        REPO_ROOT / "backend" / "requirements.txt",
        REPO_ROOT / "backend" / "requirements-dev.txt",
    ]

    for req_file in req_files:
        assert req_file.exists(), f"Requirements file missing: {req_file}"
        for line in req_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            assert "==" in line, f"Requirement '{line}' in {req_file.name} is not strictly pinned with '=='"
            assert not any(op in line for op in [">=", "<=", "~=", ">", "<"]), (
                f"Loose bound found in requirement '{line}' in {req_file.name}"
            )


def test_audit_updated_dependencies_pinned():
    """Verify exact versions of dependencies updated in commit 261813a."""
    prod_req = (REPO_ROOT / "backend" / "requirements.txt").read_text(encoding="utf-8")
    dev_req = (REPO_ROOT / "backend" / "requirements-dev.txt").read_text(encoding="utf-8")

    assert "fastapi==0.115.14" in prod_req, "fastapi not pinned to 0.115.14"
    assert "python-dotenv==1.2.4" in prod_req, "python-dotenv not pinned to 1.2.4"
    assert "Pillow==13.0.0" in dev_req, "Pillow not pinned to 13.0.0"


def test_ci_and_dockerfile_use_pinned_requirements():
    """CI workflow and Dockerfile must install dependencies from the pinned requirements files."""
    ci_file = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    docker_file = REPO_ROOT / "Dockerfile"

    assert ci_file.exists(), ".github/workflows/ci.yml missing"
    assert docker_file.exists(), "Dockerfile missing"

    ci_content = ci_file.read_text(encoding="utf-8")
    docker_content = docker_file.read_text(encoding="utf-8")

    assert "pip install -r backend/requirements.txt -r backend/requirements-dev.txt" in ci_content, (
        "CI workflow does not install from backend/requirements.txt and backend/requirements-dev.txt"
    )
    assert "-r /app/backend/requirements.txt" in docker_content, (
        "Dockerfile does not install from /app/backend/requirements.txt"
    )
