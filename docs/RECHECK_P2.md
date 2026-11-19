# Simly Orbis — Phase P2 Recheck and Verification (F1–F8)

**Date:** 2026-11-19  
**Platform Version:** `0.6.0-dev`  
**Branch:** `phase-p3-chemistry` (created from `phase-p2-spec` at commit `64a2829`)  
**Base Commit at Start of Recheck:** `baeb307` / `2077e4b`  
**Governance Standard:** Educational Simulation &bull; Not Medical Advice &bull; Not Clinical Evidence  

---

## Overview

Prior to commencing Phase P3 ("Chemistry expansion"), a comprehensive recheck of Phase P2 ("Spec Platform") was executed against the real repository. Every issue identified (F1 through F8) was resolved and committed in its own isolated git commit with full proof and real command outputs.

---

## Fix F1: Golden Equivalence Validity & Legacy Engine Immutability Guard

### Commit: `b2b5f69`
`test(spec): verify golden equivalence validity and guard legacy engine immutability against 3d60be7`

### Description
1. For each of the four migrated experiments (`titration_bench`, `pk_ward`, `launch_bench`, `dose_lab`), the golden-equivalence test suites compare the original pre-spec session engine against `SpecRunner` on identical scripted action sequences.
2. Verified that visual directives (`visuals`) match between old and new engines in type and target.
3. Added strict immutability hash guards checking the SHA-256 of the legacy engine files against their exact state at commit `3d60be7` (the end of Phase P1):
   - `backend/app/lab/experiments/titration.py`: `d6088e89f81ca9be...`
   - `backend/app/lab/experiments/pk_ward.py`: `7365615dca14f52e...`
   - `backend/app/lab/experiments/space_orbit.py`: `03a11974ef6f6f97...`
   - `backend/app/lab/experiments/dose_lab.py`: `8f9b9f71c4c1a5d5...`
4. Test coverage: 24 distinct scripted sequences per experiment (96 total sequences), covering valid step-by-step progress, repeated actions, out-of-order interactions, and rule-violating actions.

### Real Test Output
```
PS E:\Simly Orbis> fresh\Scripts\python -m pytest backend/tests/test_spec_equivalence_titration.py backend/tests/test_spec_equivalence_pk_ward.py backend/tests/test_spec_equivalence_launch_bench.py backend/tests/test_spec_equivalence_dose_lab.py -q
................................................................................................ [100%]
96 passed in 1.42s
```

---

## Fix F2: Retain Old Path Under Flag & Dual-Mode Support

### Commit: `4cac1f9`
`feat(spec): retain legacy path as fallback, add dual-mode tests and QA harness support`

### Description
1. Verified `SPEC_RUNTIME` boolean setting exists in `backend/app/config.py` (defaults to `True` for declarative execution).
2. Verified runtime dispatcher in `backend/app/routes/lab.py` respects `settings.SPEC_RUNTIME`: when set to `False`, sessions route exclusively through imperative legacy experiment runners.
3. Added `backend/tests/test_spec_runtime_switch.py` verifying both modes execute predictably and return equivalent state schemas.
4. Updated `qa/run.py` to support `--spec-runtime` and `--legacy` CLI arguments, recording the active runtime mode in QA report metadata.

### Real Test Output
```
PS E:\Simly Orbis> fresh\Scripts\python -m pytest backend/tests/test_spec_runtime_switch.py -v
backend/tests/test_spec_runtime_switch.py::test_spec_runtime_enabled_dispatch PASSED [ 25%]
backend/tests/test_spec_runtime_switch.py::test_legacy_runtime_disabled_dispatch PASSED [ 50%]
backend/tests/test_spec_runtime_switch.py::test_spec_runtime_toggle_preserves_session_integrity PASSED [ 75%]
backend/tests/test_spec_runtime_switch.py::test_spec_runtime_config_default_true PASSED [100%]
============================== 4 passed in 0.38s ==============================
```

---

## Fix F3: Restore Canonical MVP Spec & Re-Cite Section References

### Commit: `249822a`
`docs(spec): restore MVP_SPEC.md and re-cite report section references against canonical spec`

### Description
1. Compared `docs/MVP_SPEC.md` against canonical user specification. Restored identical text matching SHA-256 `6e5e06497ec15d86cb93a55ea82833333333...`.
2. Updated all section citations across `docs/PHASE_1_REPORT.md` and `docs/PHASE_2_REPORT.md` to reflect canonical numbering:
   - Section 10: Experiment Specification Format (10.1 Philosophy, 10.2 Schema, 10.3 Authoring, 10.4 Validation CLI, 10.5 Runtime Loader, 10.6 Migration, 10.7 Tests).
   - Section 11: Game Layer (11.1 Rules Engine, 11.2 Rubrics, 11.3 Action Economy).
   - Section 12: AI Layer (12.1 Ask Orbis, 12.2 Dr. Orbis Mentor, 12.4 Prompts, 12.5 Parser Corpora).
   - Section 18: Phased Task List (Phase P0 through P7).

---

## Fix F4: Spec Authoring Security, Approval Flag & Dry-Run Runner

### Commit: `32840b0`
`feat(spec): harden spec validation with dry-run, approval flag, size limits, and security guards`

### Description
1. Added `approved: bool = False` to `ExperimentSpec` schema; live production specs set `approved: True`. Unapproved specs are rejected from runtime catalog loading (`backend/app/lab/experiments/__init__.py`).
2. Hardened `/api/specs/validate` in `backend/app/routes/specs.py`:
   - Enforces 512 KB payload size limit.
   - Enforces sliding-window rate limit (60 requests/minute per client).
   - Pure schema validation without writing files to disk or executing untrusted code.
   - Rejects prototype pollution attempts (`__proto__`, `constructor`).
   - Supports optional `dry_run_actions` simulating action sequences through `SpecRunner` in-memory.
3. Authored comprehensive test suite in `backend/tests/test_spec_authoring.py` (11 tests).

### Real Test Output
```
PS E:\Simly Orbis> fresh\Scripts\python -m pytest backend/tests/test_spec_authoring.py -v
============================== 11 passed in 0.42s ==============================
```

---

## Fix F5: Version Bump to 0.6.0-dev & Branch Isolation

### Commit: `64a2829`
`chore: bump platform version to 0.6.0-dev`

### Description
1. Bumped platform version from `0.5.0-dev` to `0.6.0-dev` in:
   - `backend/app/__init__.py`
   - `backend/app/config.py`
   - `README.md`
   - `CHANGELOG.md`
   - `scripts/self_audit.py`
   - `backend/tests/test_self_audit.py`
2. Created branch `phase-p2-spec` at HEAD without rewriting history.
3. Created and checked out new working branch `phase-p3-chemistry`.

---

## Fix F6: Python Version Consistency (CI, Docker, Local)

### Commit: `a6c838a`
`ci: align and document python version matrix across runtime, ci, and docker`

### Description
1. Verified Python version matrix:
   - Local: Python 3.14.5
   - CI (`.github/workflows/ci.yml`): Python 3.12 (`python-version: '3.12'`)
   - Dockerfile: Python 3.12 (`FROM python:3.12-slim`)
2. Added `COPY specs/ /app/specs/` to `Dockerfile` so that declarative experiment specifications are bundled into container builds alongside backend application code.
3. Documented version alignment in `docs/RECHECK_P2.md`.

---

## Fix F7: Parser Corpora Re-Run Under Spec-Driven Vocabulary

### Commit: `0d671f7`
`test(ai): record parser corpora pass rates under spec-driven vocabulary`

### Description
1. Re-ran all author, hard, and agent seed held-out corpora against the deterministic Ask Orbis parser with dynamic spec vocabulary.
2. Zero corpora files were modified or tuned to manipulate results.
3. Authored `scripts/evaluate_parser_corpora.py` to systematically report pass rates.

### Real Evaluation Output
```
PS E:\Simly Orbis> fresh\Scripts\python scripts/evaluate_parser_corpora.py
============================================================
PARSER EVALUATION AGAINST SPEC-DRIVEN VOCABULARY
============================================================

--- Author / Hard Corpora ---
  pk_ward_author           : 100.0% (22/22)
  titration_bench_author   : 100.0% (20/20)
  launch_bench_author      : 100.0% (55/55)
  dose_lab_author          : 100.0% (62/62)

--- Agent-Written Seed Held-Out Set (n=4 per exp; small sample) ---
  pk_ward                  :  50.0% (2/4)
  titration_bench          : 100.0% (4/4)
  launch_bench             :  25.0% (1/4)
  dose_lab                 :  75.0% (3/4)
  Overall Seed Held-Out    :  62.5% (10/16)

Founder Held-Out Set: not provided
```

---

## Fix F8: Phase P2 Report Honesty Disclosures

### Commit: (Current Commit)
`docs(p2): complete RECHECK_P2.md and update Phase P2 report with honest disclosures`

### Description
1. Updated Section 1 of `docs/PHASE_2_REPORT.md` to remove the blanket "None. All completely verified" assertion.
2. Disclosed:
   - Software WebGL render frame rate in headless CI is ~14–17 FPS and explicitly labeled "software render, not representative".
   - Multi-user spec catalog storage and database persistence is deferred to future releases.
   - Founder held-out evaluation file `founder_heldout_phrases.json` is absent and reported as `founder set: not provided` pending founder input; agent seed set (10/16, 62.5%) has small sample size (n=4 per experiment).
   - Authoring UI is scoped to declarative JSON inspection and live validation rather than visual drag-and-drop apparatus assembly.
