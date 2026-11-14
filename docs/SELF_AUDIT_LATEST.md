# Simly Orbis Stage Gate Self-Audit Report

**Status:** PASS  
**Platform Version:** 0.4.0-dev  
**Single Source of Truth:** Backend Simulators  
**Governance Standard:** Educational Simulation &bull; Not Medical Advice &bull; Not Clinical Evidence  

---

## Stage Gates Verification Summary

| Gate | Requirement | Status | Evidence / Metrics |
| :---: | :--- | :---: | :--- |
| 1 | Git Repository State | **PASS** | Clean/Expected: True, Ahead: 12, HEAD: f076e7e6 |
| 2 | App Version | **PASS** | Version `0.4.0-dev` declared in `backend/app/config.py` |
| 3 | Pytest Test Suite | **PASS** | [fresh venv] `==================== 411 passed, 11035 warnings in 15.56s =====================` |
| 4 | Validation Row Governance | **PASS** | Evaluated 32 rows across 5 files: 32 unverified (with blank retrieved_on), 0 verified. Violations: 0 |
| 5 | Frozen Tolerances Guard | **PASS** | 3/3 frozen tolerance files verified. |
| 6 | Engine Immutability (Rule R1/R7) | **PASS** | Protected files checked: 4 engines + R1-R10/S1-S8 rules. Violations: 0 |
| 7 | CI Workflow Configuration | **PASS** | `.github/workflows/ci.yml` invokes bare `pytest backend/tests`. |
| 8 | QA Playthrough Proof | **PASS** | Folder: `20261114_111033` | Media count: 55 | report.md: True | MD5 collisions: 0 | Districts: 4/4 verified |
| 9 | First-Run Parser Baselines | **PASS** | Recorded first-run rates: Dose Lab baseline: 24.2% (15/62), Space Stage baseline: 89.1% |
| 10 | Claims & Compliance Audit (Rule R4/R6) | **PASS** | Total occurrences: 3 (all explicitly hedged/disclaimed). Unhedged violations: 0 |
| 11 | Gitignore Coverage | **PASS** | Coverage confirmed: qa/out (True), __pycache__ (True) |

---

## Detailed Gate Findings

### Gate 1: Git Repository State

HEAD: `f076e7e6` | Clean: True (expected audit files: True) | Ahead: 12

**Last 15 Commits:**
```
f076e7e docs: Stage 3 report and self-audit
6ba1771 scripts: self-audit for stage gates
000416a docs: pkpd physics, claims audit, judge Q&A, roadmap
27eac57 qa: dose lab playthrough with real proof
d2cc725 feat(pharma): mentor context and Ask Orbis for dose lab
579ce49 feat(pharma): dose response UI and curves
1dab90e feat(pharma): Dose Response Lab experiment, rules, scoring, report
e2c2e0f feat(pharma): drug library v2 and hold-out calibration framework
d0afa45 test(pharma): analytic checks for PK/PD engine
bd8ce6d feat(pharma): two-compartment PK, IV route, PD, covariates
0ba6bb0 chore: neutral pad name, git_sha, known issues
72392c9 validation: fix space row provenance
cb9b66f docs: Space stage report
6e53063 chore: v0.3.0-dev space slice
bbca0ff docs: space slice docs and claims audit update
```

### Gate 3: Pytest Test Suite

Exit code: 0

Command: `E:\Simly Orbis\fresh\Scripts\pytest.exe backend/tests`

Final line: `==================== 411 passed, 11035 warnings in 15.56s =====================`

### Gate 4: Validation Row Governance

All rows strictly comply with Rule R2/R3.

### Gate 5: Frozen Tolerances Guard

- validation/tolerances.yaml: `5b5d857ed4862b51...` OK
- validation/space_tolerances.yaml: `fc4ba76cb3ee9d65...` OK
- validation/pkpd_tolerances.yaml: `443d18ab90e60b43...` OK

### Gate 6: Engine Immutability (Rule R1/R7)

- `backend/app/pharma/pk.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/pharma/trial.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/chem/titration.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/space/orbit.py`: 0 diff vs `cb9b66f` (PASS)
- Rules R1-R10 and S1-S8: Unmodified (PASS)

### Gate 10: Claims & Compliance Audit (Rule R4/R6)

All mentions are strictly negative/disclaimer statements.

---

## Non-Negotiable Rules Audit

1. **R1 (Single Source of Truth):** Frontend and 3D scenes act solely as visual rendering clients. Simulation results, differential equations, and safety assessments are evaluated strictly by backend engines.
2. **R2 (AI Proposes, Engine Decides):** Dr. Orbis and Ask Orbis NLP proposals are strictly routed through engine state machines and validation boundaries.
3. **R3 (Validation Integrity):** `verified_by` remains strictly `"unverified"` for all pending rows. Tolerances are guarded by immutable SHA-256 hashes.
4. **R4 (Real Proof Only):** 100% of reported QA frames are verified non-empty, unique, and perceptually distinct (0 hash collisions, 0 near-duplicates).
5. **R5 (No Fabricated Provenance):** Literature citations are accompanied by unverified flags and blank `retrieved_on` timestamps pending primary source human sign-off.
6. **R6 (Adult-Only Boundaries):** Dose Response Lab enforces strict adult ranges (Age 18–90, Weight 40–150 kg, CrCl 15–150 mL/min). Pediatric inquiries are rejected.
7. **R7 (Engine Immutability):** Baseline engines (`pharma.pk`, `pharma.trial`, `chem.titration`, `space.orbit`) and safety rules R1–R10 / S1–S8 maintain 0 diff vs baseline commits.
