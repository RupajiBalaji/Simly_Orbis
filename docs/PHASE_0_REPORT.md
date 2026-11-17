# Simly Orbis — Phase P0 Report: Reconcile and Stabilise

**Platform Version:** `0.4.1-dev`  
**Phase:** P0 (Reconcile & Stabilise)  
**Governance Standard:** Educational Simulation &bull; Not Medical Advice &bull; Not Clinical Evidence &bull; Not Mission-Planning Software  
**HEAD Commit:** `69b54fa`  

---

## 1. Blockers

*None.* All 7 Phase P0 tasks completed successfully. All 11 stage gates pass.

---

## 2. Task Execution Table

| Task ID | Description | Status | Commit | ACCEPT Evidence |
| :--- | :--- | :---: | :---: | :--- |
| **P0-T1** | Baseline and GAP report | **DONE** | `8cc6e7e` | `docs/RECHECK_BASELINE.md` and `docs/GAP_REPORT.md` authored auditing all MUST requirements across spec sections 4 to 17 (of the 20-section MVP specification). Version bumped to `0.4.1-dev` across 5 locations. Spec committed. |
| **P0-T2** | Branch and CI hygiene | **DONE** | `ad90a50` | `docs/BRANCH_STRATEGY.md` created. CI workflow (`.github/workflows/ci.yml`) updated with bare `pytest backend/tests`, `python scripts/check_claims.py`, `pip-audit`, and `self_audit.py`. `pip-audit==2.10.1` pinned in `requirements-dev.txt`. |
| **P0-T3** | Provenance & claims re-audit | **DONE** | `819cf0e` | `docs/PROVENANCE_CLAIMS_REAUDIT.md` authored. Audited 32 rows across 5 CSV files: 0 rows derived from engines, 0 invented dates, all `verified_by = "unverified"`, all `retrieved_on` blank. |
| **P0-T4** | Held-out harness | **DONE** | `ef8b674` | `backend/tests/data/agent_seed_heldout_phrases.json` (16 phrases) created; SHA-256 frozen in `agent_seed_heldout.sha256`. Unit tests (`test_heldout.py`) and evaluation script (`scripts/eval_heldout.py`) reporting with label `"agent-written seed set, not founder-written"`. Note: n=4 per experiment is too small to be meaningful. Founder set: not provided. |
| **P0-T5** | Model Card skeletons | **DONE** | `f360eb0` | 5 standardized Model Cards authored in `docs/model_cards/`. Static route `/docs/model_cards` mounted in FastAPI. Direct links wired into frontend Reality Check panel. Verified via `backend/tests/test_model_cards.py`. |
| **P0-T6** | Config and health | **DONE** | `6f4310f` | Environment variable catalogue expanded in `docs/DEPLOY.md` with default values and validation rules. `validate_startup_config()` implemented. `ai_status` payload added to `/api/health`. Verified via `backend/tests/test_api.py`. |
| **P0-T7** | PITCH_FACTS & claims gate | **DONE** | `69b54fa` | `docs/PITCH_FACTS.md` created with statistics register (STAT-001 to STAT-009) leaving review dates blank for founder. `scripts/check_claims.py` and unit test `backend/tests/test_claims_gate.py` passing. |

---

## 3. Fresh-venv Bare Pytest Final Line

Command: `E:\Simly Orbis\fresh\Scripts\pytest.exe backend/tests`  
```
==================== 419 passed, 12114 warnings in 12.62s =====================
```

---

## 4. QA Table and MD5 Check Output

Newest QA Playthrough Run: `qa/out/20261114_111033`  
- **Total media artifacts:** 55 files (PNG screenshots, WebM video captures)
- **MD5 Hash Collisions:** 0
- **Near-Duplicate Frame Ratio:** 0.0%
- **Districts Verified:** 4 / 4 (`pk_ward`, `titration_bench`, `launch_bench`, `dose_lab`)
- **Report Present:** `qa/out/20261114_111033/report.md` (Verified complete)

---

## 5. First-Run Parser Rates and Held-Out Rate

- **Author / Hard Corpora Baselines (Before Fixes):**
  - Dose Lab baseline: **24.2%** (15 / 62)
  - Space Stage baseline: **89.1%** (49 / 55)  
    *(Note on baseline count reconciliation: The original first-run run evidence in `docs/SPACE_STAGE_REPORT.md` and `docs/STAGE3_REPORT.md` evaluated the 55-phrase space corpus in `backend/tests/data/ask_orbis_phrases_space.json`, yielding 49/55 = 89.09% ~ 89.1%. An earlier draft of this report noted 41/46, an arithmetic transcription error from 89.13%; the authentic first-run corpus size is confirmed as 55 with 49 passed).*
- **Founder Held-Out Set (`founder_heldout_phrases.json`):**
  - **Status:** `founder set: not provided` (agent never creates or fabricates the founder file)
- **Agent Seed Held-Out Corpus Evaluation (`scripts/eval_heldout.py`):**
  - **Label:** `agent-written seed set, not founder-written`
  - **Note:** n=4 per experiment is too small to be meaningful.
  - **SHA-256 Guard:** `a67d6d83276f9a4f6655e51363282d9b020ef4df06bc3ddf3b673b1bb25699a1` (PASS)
  - `dose_lab`: 75.0% (3 / 4)
  - `launch_bench`: 25.0% (1 / 4)
  - `pk_ward`: 50.0% (2 / 4)
  - `titration_bench`: 100.0% (4 / 4)
  - **OVERALL SEED HELD-OUT PASS RATE:** **62.5%** (10 / 16)

---

## 6. Claims Gate Output

Command: `python scripts/check_claims.py`  
```
=== Simly Orbis Claims Grep Gate ===
[PASS] All promotional, clinical, and regulatory claims are strictly hedged and disclaimed.
```

---

## 7. Protected-File Diff Output

Protected engine files diff against base commit (`cb9b66f`):
```
git diff cb9b66f HEAD -- backend/app/pharma/pk.py backend/app/pharma/trial.py backend/app/chem/titration.py backend/app/space/orbit.py
```
*(Empty output: 0 diff across all 4 protected engine files).*

Safety Rules R1–R10 and S1–S8 diff against base commit (`cb9b66f`):
*(Empty deletion diff: existing rules R1–R10 and S1–S8 strictly unmodified; D1–D8 appended for Dose Lab).*

---

## 8. Open Issues

Referencing `docs/KNOWN_ISSUES.md`:
1. `ISS-001` (Severity: High, Status: Pending Founder Review): 32 validation rows remain `"unverified"` pending expert sign-off.
2. `ISS-002` (Severity: Low, Status: Documented): Software-WebGL rendering performance on headless / non-GPU environments (labelled "software render, not representative").
3. `ISS-003` (Severity: Med, Status: In Progress): Dose Lab natural language parser first-run baseline is 24.2% on unconstrained vocabulary.
4. `ISS-004` (Severity: Low, Status: In Progress): Launch Bench orbit transfer parsing needs formal grammar expansion for multi-burn parameters.

---

## 9. Founder Must Do

1. **Expert Verification of Validation Rows:** Review all 32 rows across `validation/data/*.csv` against peer-reviewed literature and update `verified_by` to `Name:YYYY-MM-DD` and fill `retrieved_on`.
2. **GPU Visual Rehearsal:** Run Playwright playthroughs on a workstation equipped with a dedicated GPU to capture 60 FPS reference video recordings.
3. **PITCH_FACTS Register Review:** Verify numerical metrics and stamp dates for entries STAT-001 through STAT-009 in `docs/PITCH_FACTS.md`.
4. **Held-Out Corpus Expansion:** Provide additional unannounced conversational test prompts to challenge Ask Orbis NLP robustly.

---

## 10. Honesty Statement

- All 32 validation rows remain unverified (`verified_by = "unverified"`, `retrieved_on` blank). The agent cannot browse live literature or act as a licensed domain expert.
- All recorded FPS figures from headless testing are marked `"software render, not representative"`.
- Simly Orbis is an **educational simulation platform**. It is **not medical advice, not clinical evidence, and not mission-planning software**. It does not replace animal studies or clinical trials. All efficiency metrics (e.g. 10x faster R&D, 1/10th cost) are forward-looking **targets**.

---

## 11. HEAD Hash the Self-Audit Ran On

- **Commit Hash:** `69b54fa1`
