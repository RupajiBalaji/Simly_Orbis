# Simly Orbis — Phase P2 Report: Spec Platform

**Platform Version:** `0.5.0-dev`  
**Phase:** P2 (Spec Platform & Authoring Ecosystem)  
**Governance Standard:** Educational Simulation &bull; Not Medical Advice &bull; Not Clinical Evidence &bull; Not Mission-Planning Software  
**HEAD Commit:** `baeb307`  

---

## 1. Executive Summary & Blockers

*None.* All six Phase P2 tasks (P2-T1 through P2-T6) have completed successfully in one uninterrupted run. Every task landed in its own isolated git commit. All four operational lab experiments (`titration_bench`, `pk_ward`, `launch_bench`, `dose_lab`) have been migrated from imperative code to declarative JSON experiment specifications schema-checked against strict Pydantic models. Golden-equivalence suites confirm bit-for-bit equivalence between imperative legacy flows and spec-driven execution (92/92 tests passing). The full test suite runs cleanly at 582 tests (0 failures), and the self-audit passes all 11 stage gates.

---

## 2. Task Execution Table

| Task ID | Description | Status | Commit | ACCEPT Evidence |
| :--- | :--- | :---: | :---: | :--- |
| **P2-T1** | Experiment Specification Schema & Validator (Spec 10.1, 10.2, 10.4) | **DONE** | `9480cc1` | Authored `backend/app/specs/models.py` defining `ExperimentSpec`, `ApparatusItem`, `ActionDef`, `RuleDef`, `RubricDef`, and `MentorHintDef`. Built validator `backend/app/specs/validator.py`, loader `backend/app/specs/loader.py`, and CLI tool `scripts/validate_specs.py`. Added unit tests in `backend/tests/test_specs.py`. |
| **P2-T2** | Titration Bench Declarative Migration & Golden Equivalence (Spec 10.6, 10.7) | **DONE** | `ef18cf4` | Extracted declarative specification `specs/titration_bench.json`. Implemented `backend/app/specs/runner.py` executing actions, evaluating safety rules, and computing rubric scores purely from spec definitions. Golden-equivalence suite `backend/tests/test_spec_equivalence_titration.py` verifies 23 golden test sequences with zero behavioral divergence. |
| **P2-T3** | Migration of PK Ward, Launch Bench, and Dose Response Lab (Spec 10.6, 10.7) | **DONE** | `84ff27b` | Authored `specs/pk_ward.json`, `specs/launch_bench.json`, and `specs/dose_lab.json`. Migrated backend lab router to dispatch through `SpecRunner` when specs are active. Authored golden-equivalence suites `test_spec_equivalence_pk_ward.py`, `test_spec_equivalence_launch_bench.py`, and `test_spec_equivalence_dose_lab.py` (69 test cases total, 100% pass). |
| **P2-T4** | Spec-Driven Mentor Hints & Ask Orbis Dynamic Vocabulary (Spec 12.1, 12.2) | **DONE** | `bbdad8b` | Updated Dr. Orbis mentor engine and Ask Orbis NLP planner to dynamically source apparatus targets, allowed actions, step synonyms, and context hints directly from the active experiment spec (`backend/app/routes/tutor.py`, `backend/app/lab/agent.py`). Verified dynamic prompt vocabulary and fallback handling in `backend/tests/test_spec_mentor.py`. |
| **P2-T5** | Authoring Documentation & Worked Example (Spec 10.3) | **DONE** | `8a015a2` | Comprehensive authoring guide authored at `docs/EXPERIMENT_SPEC_GUIDE.md`. Complete, schema-checked worked example fixture provided at `specs/fixtures/worked_example_neutralization.json` with 11 steps, safety rules, scoring rubric, visual directives, and i18n keys. Verified via `scripts/validate_specs.py`. |
| **P2-T6** | Authoring Form & Validation UI (Spec 10.3, 10.4) | **DONE** | `baeb307` | Interactive authoring interface created at `frontend/authoring.html` and styled with Design Tokens. Connected to `/api/specs/validate` endpoint in `backend/app/routes/specs.py`. Surfaces JSON editor, file upload/download, and real-time validation error alerts. Verified via `backend/tests/test_spec_authoring.py`. |

---

## 3. Golden-Equivalence Test Results

Golden-equivalence tests run both the legacy hardcoded logic and the new declarative spec runtime side-by-side on identical sequences of state actions, comparing final session state, completed steps, safety rule evaluations, visual directives, and rubric grades.

Command: `fresh\Scripts\pytest backend/tests/test_spec_equivalence_titration.py backend/tests/test_spec_equivalence_pk_ward.py backend/tests/test_spec_equivalence_launch_bench.py backend/tests/test_spec_equivalence_dose_lab.py`

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-8.3.3, pluggy-1.7.0
rootdir: E:\Simly Orbis\backend
configfile: pytest.ini
collected 92 items

backend\tests\test_spec_equivalence_titration.py ....................... [ 25%]
backend\tests\test_spec_equivalence_pk_ward.py .......................   [ 50%]
backend\tests\test_spec_equivalence_launch_bench.py .................... [ 71%]
...                                                                      [ 75%]
backend\tests\test_spec_equivalence_dose_lab.py .......................  [100%]

====================== 92 passed, 527 warnings in 2.34s =======================
```

**Equivalence Summary:**
- **Titration Bench:** 23 golden sequences verified (including perfect titration, indicator omitted, over-titration, burette overflow, unrinsed burette, and live API dispatch). 0 divergence.
- **PK Ward:** 23 golden sequences verified (including nominal paracetamol oral dosing, unwashed hands / no PPE, early blood draw, dose omission, centrifuge timing, and live API dispatch). 0 divergence.
- **Launch & Orbit Bench:** 23 golden sequences verified (including Orbis-1 nominal 200 km LEO insertion, payload overload, unverified clearance, dry ignition, staging delta-v, and live API dispatch). 0 divergence.
- **Dose Response Lab:** 23 golden sequences verified (including theophylline oral titration, vancomycin 2-compartment infusion, gentamicin renal impairment adjustment, toxic overdose alarm, and live API dispatch). 0 divergence.

---

## 4. Fresh-Venv Bare Pytest Final Line

Command: `E:\Simly Orbis\fresh\Scripts\pytest.exe backend/tests`

```
582 passed, 19162 warnings in 86.77s (0:01:26)
```

- **Total Tests Passed:** 582
- **Total Tests Failed:** 0
- **Total Tests Skipped:** 0
- **Pass Rate:** 100.0%

---

## 5. Specification Validation Summary

Command: `fresh\Scripts\python scripts/validate_specs.py`

```
Validating 4 experiment specification(s)...
============================================================
[PASS] specs\dose_lab.json (dose_lab v1.0.0)
[PASS] specs\launch_bench.json (launch_bench v1.0.0)
[PASS] specs\pk_ward.json (pk_ward v1.0.0)
[PASS] specs\titration_bench.json (titration_bench v1.0.0)
============================================================
Summary: 4/4 passed, 0 failed.
```

Worked example fixture validation:
`fresh\Scripts\python scripts/validate_specs.py specs/fixtures/worked_example_neutralization.json`
`[PASS] specs\fixtures\worked_example_neutralization.json (worked_example_neutralization v1.0.0)` — 1/1 passed.

---

## 6. QA Playthrough Proof Summary

- **Newest QA Run Directory:** `qa/out/20261118_085910`
- **Creation Timestamp:** `2026-11-18 08:59:10` (Completed: `09:10:44`)
- **Freshness vs Frontend Commits:** Strictly newer than last frontend commit `baeb307` (`2026-11-18 08:58:29`).
- **Total Media Artifacts:** 62 files (58 PNG checkpoints + 4 video streams).
- **MD5 Hash Collisions:** 0 across all 58 checkpoint screenshots.
- **Near-Duplicate Check:** Passed (0 duplicate frames).
- **Districts Covered (Success, Rule-Violation, and Failure runs):**
  1. Pharmacokinetics Ward (`pk_ward`): Success (Grade C), Rule-Violation R1 (`pk_ward_rule_violation.png`), Failure (`pk_ward_failure_report.png`).
  2. Titration Bench (`titration_bench`): Success (Grade A), Rule-Violation R3 (`titration_rule_violation.png`), Failure (`titration_failure_report.png`).
  3. Launch & Orbit Bench (`launch_bench`): Success (Grade A), Rule-Violation S1/S2 (`space_rule_violation.png`), Failure (`space_failure_report.png`).
  4. Dose Response Lab (`dose_lab`): Scenarios 1–4, Toxic Overdose alarm (`dose_scenario_4_overdose_alarm.png`), Failure (`dose_lab_failure_report.png`).
- **Software WebGL Render Disclaimer:** `FPS Stats: Current=1, Median=10, Min=10, Avg=13 (Samples: 1200) - software render, not representative`.

---

## 7. First-Run Parser Rates & Held-Out Status

- **Dose Response Lab Baseline:** 24.2% (15/62) recorded on first run.
- **Space Stage Baseline:** 89.1% (49/55) recorded on first run.
- **Founder Held-Out Set:** Not provided (`founder_heldout_phrases.json` absent from repo; runner reports `founder set: not provided`).
- **Agent-Written Seed Set:** 62.5% (10/16) on `agent_seed_heldout_phrases.json` (explicitly noted: $n=4$ per experiment is too small to be statistically meaningful; not founder-written).

---

## 8. Engine Immutability & Safety Rules Verification (Rules R1/R7)

Baseline calculation engines and safety rule math remain strictly untouched with 0 byte diff vs base commit `cb9b66f`:
- `backend/app/pharma/pk.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/pharma/trial.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/chem/titration.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/space/orbit.py`: 0 diff vs `cb9b66f` (PASS)
- Safety Rules R1–R10 and S1–S8 in `backend/app/lab/rules.py`: 0 modifications (PASS)
- Validation tolerances: 32 rows across 5 files strictly maintained as `verified_by: "unverified"` with empty `retrieved_on`.
