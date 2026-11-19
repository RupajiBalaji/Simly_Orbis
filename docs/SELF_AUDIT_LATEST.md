# Simly Orbis Stage Gate Self-Audit Report

**Status:** PASS  
**Platform Version:** 0.6.0-dev  
**Single Source of Truth:** Backend Simulators  
**Governance Standard:** Educational Simulation &bull; Not Medical Advice &bull; Not Clinical Evidence  

---

## Stage Gates Verification Summary

| Gate | Requirement | Status | Evidence / Metrics |
| :---: | :--- | :---: | :--- |
| 1 | Git Repository State | **PASS** | Clean/Expected: True, Ahead: 76, HEAD: 09e098d5 |
| 2 | App Version | **PASS** | Version `0.6.0-dev` declared in `backend/app/config.py` |
| 3 | Pytest Test Suite | **PASS** | [fresh venv] `=============== 703 passed, 26936 warnings in 91.46s (0:01:31) ================` |
| 4 | Validation Row Governance | **PASS** | Evaluated 32 rows across 5 files: 32 unverified (with blank retrieved_on), 0 verified. Violations: 0 |
| 5 | Frozen Tolerances Guard | **PASS** | 4/4 frozen tolerance files verified. |
| 6 | Engine Immutability (Rule R1/R7) | **PASS** | Protected files checked: 4 engines + R1-R10/S1-S8 rules. Violations: 0 |
| 7 | CI Workflow Configuration | **PASS** | `.github/workflows/ci.yml` invokes bare `pytest backend/tests`. |
| 8 | QA Playthrough Proof | **PASS** | Folder: `20261119_153733` (fresh (post-frontend commit)) | Media count: 70 | report.md: True | MD5 collisions: 0 | Districts: 4/4 verified |
| 9 | First-Run Parser Baselines & Held-Out Status | **PASS** | Recorded rates & held-out status: Dose Lab baseline: 24.2% (15/62); Space Stage baseline: 89.1%; founder set: not provided; agent-written seed set, not founder-written (n=4/exp too small to be meaningful) |
| 10 | Claims & Compliance Audit (Rule R4/R6) | **PASS** | Total occurrences: 19 (all explicitly hedged/disclaimed). Unhedged violations: 0 |
| 11 | Gitignore Coverage | **PASS** | Coverage confirmed: qa/out (True), __pycache__ (True) |

---

## Detailed Gate Findings

### Gate 1: Git Repository State

HEAD: `09e098d5` | Clean: False (expected audit files: True) | Ahead: 76

**Last 15 Commits:**
```
09e098d test(qa): add kinetics and buffer QA sequences, reality checks, and self-audit guard for chemistry tolerances
e786432 docs(chem): chemistry engines documentation and model cards
201bd5f test(ai): author and hard phrase corpora for Kinetics and Buffer Benches
762e227 feat(validation): chemistry kinetics and buffer validation tolerances and frozen hash
7857217 feat(spec): Buffer Bench declarative specification and interactive UI
3e1b502 feat(spec): Kinetics Bench declarative specification and interactive UI
c50cc9f feat(chem): live titration curve with indicator transition band
6b6bc5e feat(chem): buffer equilibrium and buffer capacity engine
8c9609b feat(chem): chemical reaction kinetics engine with analytic and RK4 solutions
360d908 docs(p2): complete RECHECK_P2.md and update Phase P2 report with honest disclosures
0d671f7 test(ai): record parser corpora pass rates under spec-driven vocabulary
a6c838a ci: align and document python version matrix across runtime, ci, and docker
64a2829 chore: bump platform version to 0.6.0-dev
32840b0 feat(spec): harden spec validation with dry-run, approval flag, size limits, and security guards
249822a docs(spec): restore MVP_SPEC.md and re-cite report section references against canonical spec
```

### Gate 3: Pytest Test Suite

Exit code: 0

Command: `E:\Simly Orbis\fresh\Scripts\pytest.exe backend/tests`

Final line: `=============== 703 passed, 26936 warnings in 91.46s (0:01:31) ================`

### Gate 4: Validation Row Governance

All rows strictly comply with Rule R2/R3.

### Gate 5: Frozen Tolerances Guard

- validation/tolerances.yaml: `5b5d857ed4862b51...` OK
- validation/space_tolerances.yaml: `fc4ba76cb3ee9d65...` OK
- validation/pkpd_tolerances.yaml: `443d18ab90e60b43...` OK
- validation/chem_tolerances.yaml: `2288d01d83e2a5fc...` OK

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
