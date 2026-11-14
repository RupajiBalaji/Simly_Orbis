# Simly Orbis Git Branching & CI Governance Strategy

**Standard:** Section 18 (P0-T2) of *Simly Orbis MVP Build Specification and Agent Task Playbook*  
**Date:** 2026-11-14  

---

## 1. Branch Strategy

Simly Orbis adheres to a strict, audit-gated branch model designed to protect production demonstrations and release stability:

1. **`main` Branch (Rehearsed Demo Only):**
   - Represents the canonical, verified, demo-ready production state.
   - Live deployments (e.g. Render Web Service) track `main`.
   - Release tags (`v0.2.0-demo`, `v0.4.0-rc1`, etc.) are attached exclusively to verified `main` commits.
   - Pushing directly to `main` without passing phase gates is strictly forbidden.

2. **Phase Branches (`phase-p<N>-<name>`):**
   - Each phase of development branches from the previous phase branch (or from `main` for Phase P0).
   - Branch naming: `phase-p0-reconcile`, `phase-p1-ui-design`, `phase-p2-spec-platform`, `phase-p3-pharma-district`, etc.
   - All tasks in a phase are committed linearly with single-purpose atomic commits (`type(scope): summary`).
   - History rewriting (`git commit --amend`, rebase, reset) is strictly prohibited once `scripts/self_audit.py` has run on a commit.

3. **Phase Promotion & Merge Requirements:**
   - A phase branch may only be merged into `main` (or advanced to the next phase) when **all 11 Common Phase Gates** (Section 18.0) pass with zero blockers.
   - Gates include: 100% clean unit test suite, frozen tolerance SHA-256 validation, zero unauthorized diff on protected engines, 100% proof uniqueness (zero duplicate or near-duplicate frames), claims compliance, and clean self-audit.

---

## 2. Continuous Integration (CI) Workflow Pipeline

The GitHub Actions CI pipeline (`.github/workflows/ci.yml`) executes on every push and pull request across all branches. It enforces the four automated verification gates:

1. **Bare Pytest Gate (`pytest backend/tests`):**
   - Runs bare pytest from the repository root without `python -m` wrapping.
   - Ensures correct module resolution and catches missing import dependencies.
2. **Spec & Validation Integrity Gate:**
   - Evaluates reference row format rules (`verified_by` and blank `retrieved_on`).
   - Verifies SHA-256 frozen tolerance locks on `validation/*.yaml`.
3. **Claims & Regulatory Compliance Gate (`python scripts/check_claims.py`):**
   - Greps repository text and documentation for prohibited or unhedged claims (`validated`, `clinically proven`, `replaces animal testing`).
   - Ensures disclaimers ("educational simulation, not medical advice") are omnipresent.
4. **Dependency Security Audit (`pip-audit`):**
   - Audits installed Python packages against the PyPA Advisory Database to prevent supply-chain vulnerabilities.
