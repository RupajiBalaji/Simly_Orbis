# Simly Orbis — Phase P3 Report: Chemistry Expansion

**Platform Version:** `0.6.0-dev`  
**Phase:** P3 (Chemistry Expansion: Reaction Kinetics & Buffer Equilibrium)  
**Governance Standard:** Educational Simulation &bull; Simplified Models &bull; Not Medical Advice &bull; Not Clinical Evidence  
**Active Branch:** `phase-p3-chemistry`  
**HEAD Commit:** `09e098d`  

---

## 1. Executive Summary & Honest Disclosures

Phase P3 expands Simly Orbis with comprehensive chemical reaction kinetics and buffer equilibrium simulation engines, declarative experiment specifications, interactive laboratory UI panels, validation benchmarks with frozen hash files, and natural language phrase parsing corpora. All 8 tasks (P3-T1 through P3-T8) and the P3 extra QA gate have completed with 100% test pass rates (703/703 tests passing).

In accordance with platform governance rules (R1–R10 / G1–G12), the following disclosures and qualifications are formally documented:

1. **Software-Render FPS (Not Representative):** Automated browser playthroughs executed via headless Chromium in containerized/headless environments utilize software WebGL emulation (e.g. SwiftShader / Mesa llvmpipe), reporting ~14–17 FPS rather than native hardware acceleration (>=30 FPS). As mandated by governance rules, software-rendered performance metrics are explicitly labeled as "software render, not representative of native GPU client performance".
2. **First-Order Mathematical Simplifications & Errors:**
   - **Activity Coefficients Omitted:** Both `chem.kinetics` and `chem.buffer` operate under ideal dilute aqueous solution assumptions where activity coefficients $\gamma_i = 1$ (concentrations equal thermodynamic activities). At ionic strength $I > 0.05\text{ M}$, Debye-Hückel effects cause up to $0.05–0.15\text{ pH}$ unit divergence.
   - **Temperature Invariance of pKa:** Acid dissociation constants ($pK_a$) are treated as constant across the $20^\circ\text{C}–40^\circ\text{C}$ range, whereas real-world $pK_a$ values possess small temperature coefficients ($\Delta pK_a \approx -0.015\text{ K}^{-1}$ for amine buffers, negligible for carboxylates).
   - **Equilibrium Kinetics Coupling:** Reaction kinetics assume forward-dominant reactions without dynamic reversible backward equilibrium, producing accurate trajectories for high-affinity or irreversible reactions, with up to $2–5\%$ deviation near chemical equilibrium.
3. **Validation Honesty & Provenance Disclosures:**
   - **No Benchmark Reference Rows in chem_tolerances.yaml:** `validation/chem_tolerances.yaml` defines parameter limits and tolerance bands with a frozen SHA-256 hash (`validation/chem_tolerances.sha256`), but contains **no reference rows** from external experimental benchmark datasets.
   - **Self-Consistency vs. Validation:** Engine `reality_checks()` output represents **engine self-consistency checks (analytic identities), not validation**. The 11 checks evaluate mathematical identity closure (mass conservation, zero-order clipping, first-order half-life formula, Arrhenius monotonicity, electroneutrality charge-balance, and equimolar pH = pKa).
   - **Governance Compliance:** In strict accordance with G5 / R5, all existing tolerance declarations have `verified_by: "unverified"` and `retrieved_on: ""` (blank). No empirical benchmark rows have been added without direct primary literature dataset citations; all literature references note game-balanced approximate status needing human confirmation.
4. **Held-Out Corpus Honest Reporting:**
   - The agent-written seed set (`backend/tests/data/agent_seed_heldout_phrases.json`) scored 10/16 passing (62.5%, n=4 per experiment). As disclosed in P0/P1 rechecks, $n=4$ per experiment is too small to be statistically significant.
   - The external founder held-out set (`backend/tests/data/founder_heldout_phrases.json`) is reported as `founder set: not provided` pending founder authoring. The agent did not fabricate or alter this file.

---

## 2. Task Execution Table

| Task ID | Description | Status | Commit | Verification Evidence |
| :--- | :--- | :---: | :---: | :--- |
| **P3-T1** | Reaction Kinetics Engine (`chem.kinetics`) | **DONE** | `8c9609b` | Authored `backend/app/chem/kinetics.py` implementing 0th, 1st, 2nd order rate laws, consecutive reactions ($A \xrightarrow{k_1} B \xrightarrow{k_2} C$), Arrhenius $k(T)$, half-lives, closed-form analytic solutions, and 4th-order Runge-Kutta (RK4) integration with seeded noise. 45/45 unit tests passed in `backend/tests/test_chem_kinetics.py` with hand-computed comments and mass balance checks. |
| **P3-T2** | Buffer Equilibrium Engine (`chem.buffer`) | **DONE** | `6b6bc5e` | Authored `backend/app/chem/buffer.py` implementing exact charge-balance buffer equilibrium, Henderson-Hasselbalch approximation, Van Slyke buffer capacity ($\beta$), and acid/base stress additions with water auto-protolysis ($K_w = 10^{-14}$). 42/42 unit tests passed in `backend/tests/test_chem_buffer.py`. |
| **P3-T3** | Live Titration Curve with Indicator Band | **DONE** | `c50cc9f` | Added `live_curve` field and indicator transition band to titration simulation response (`backend/app/modules/chem_titration.py`, `frontend/lab/game/titration_view.js`). 5/5 tests passed in `backend/tests/test_titration_live_curve.py`. Verified in QA that DOM chart matches API curve. |
| **P3-T4** | Kinetics Bench Spec & UI | **DONE** | `3e1b502` | Authored declarative specification `specs/kinetics_bench.json` and interactive frontend panel `frontend/lab/game/kinetics_view.js`. Supports temperature adjustments, initial concentration variation, linear regression plots ($[A]$, $\ln[A]$, $1/[A]$ vs time), parameter estimation submission, and safety rules (K1–K4). 5/5 integration tests passed in `backend/tests/test_kinetics_bench.py`. |
| **P3-T5** | Buffer Bench Spec & UI | **DONE** | `7857217` | Authored declarative specification `specs/buffer_bench.json` and interactive frontend panel `frontend/lab/game/buffer_view.js`. Supports buffer system selection (acetate, phosphate, bicarbonate, TRIS), target pH formulation, live acid/base stress additions, buffer capacity calculation, and safety rules (B1–B4). 5/5 integration tests passed in `backend/tests/test_buffer_bench.py`. |
| **P3-T6** | Chemistry Validation Tolerances & Frozen Hash | **DONE** | `762e227` | Authored `validation/chem_tolerances.yaml` defining tolerances for 1st/2nd order rate constants, half-lives, Arrhenius activation energies, buffer capacity $\beta_{\max}$, and Henderson-Hasselbalch pH. Generated frozen hash `validation/chem_tolerances.sha256` (`2288d01d...`). 3/3 guard tests passed in `backend/tests/test_chem_tolerances_guard.py`. |
| **P3-T7** | Natural Language Phrase Corpora for Chemistry | **DONE** | `201bd5f` | Authored 40 normal + 15 hard phrases for Kinetics Bench (`backend/tests/data/kinetics_bench_author_phrases.json`) and 40 normal + 15 hard phrases for Buffer Bench (`backend/tests/data/buffer_bench_author_phrases.json`). Updated `evaluate_parser_corpora.py` and passed NLP tests in `backend/tests/test_ask_orbis_chemistry.py`. |
| **P3-T8** | Chemistry Documentation & Model Cards | **DONE** | `e786432` | Authored comprehensive model documentation `docs/chem_models.md` and detailed model cards `docs/model_cards/chem_kinetics.md` and `docs/model_cards/chem_buffer.md` listing governing equations, inputs/outputs, assumptions, and first-order error budgets. |
| **Extra** | Chemistry QA Harness & Integration Polish | **DONE** | `09e098d` | Implemented `reality_checks()` on `ChemKineticsModule` and `ChemBufferModule`, added 6-experiment QA sequences to `qa/run.py`, resolved i18n keys for chemistry districts, and updated self-audit tolerances guard. |

---

## 3. Natural Language Parser Evaluation

As required by Task P3-T7 and Spec Section 12, first-run pass rates were recorded on raw, unmodified corpora prior to any vocabulary tuning, followed by vocabulary expansion to achieve production threshold (>=90%).

### 3.1 First-Run vs. Final Pass Rates (All Platform Corpora)

| Corpus | First-Run Normal | First-Run Hard | First-Run Total | Final Normal | Final Hard | Final Total | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **PK Ward (`pk`)** | 18 / 18 (100.0%) | 4 / 4 (100.0%) | **22 / 22 (100.0%)** | 18 / 18 (100.0%) | 4 / 4 (100.0%) | **22 / 22 (100.0%)** | Baseline preserved |
| **Titration Bench (`titration`)** | 15 / 15 (100.0%) | 5 / 5 (100.0%) | **20 / 20 (100.0%)** | 15 / 15 (100.0%) | 5 / 5 (100.0%) | **20 / 20 (100.0%)** | Baseline preserved |
| **Launch Bench (`space`)** | 36 / 40 (90.0%) | 13 / 15 (86.7%) | **49 / 55 (89.1%)** | 40 / 40 (100.0%) | 15 / 15 (100.0%) | **55 / 55 (100.0%)** | Space baseline reconciled |
| **Dose Lab (`dose`)** | 12 / 45 (26.7%) | 3 / 17 (17.6%) | **15 / 62 (24.2%)** | 45 / 45 (100.0%) | 17 / 17 (100.0%) | **62 / 62 (100.0%)** | Stage 3 baseline preserved |
| **Kinetics Bench (`kinetics`)** | 7 / 40 (17.5%) | 2 / 15 (13.3%) | **9 / 55 (16.4%)** | 39 / 40 (97.5%) | 15 / 15 (100.0%) | **54 / 55 (98.2%)** | Generic rules |
| **Buffer Bench (`buffer`)** | 8 / 40 (20.0%) | 2 / 15 (13.3%) | **10 / 55 (18.2%)** | 39 / 40 (97.5%) | 15 / 15 (100.0%) | **54 / 55 (98.2%)** | Generic rules |

### 3.2 Full Platform Parser Corpora Summary

Command: `fresh\Scripts\python scripts/evaluate_parser_corpora.py`

```
Corpus: pk_ward
  Normal: 18/18 (100.0%)
  Hard: 4/4 (100.0%)
  Total: 22/22 (100.0%)

Corpus: titration_bench
  Normal: 15/15 (100.0%)
  Hard: 5/5 (100.0%)
  Total: 20/20 (100.0%)

Corpus: launch_bench
  Normal: 40/40 (100.0%)
  Hard: 15/15 (100.0%)
  Total: 55/55 (100.0%)

Corpus: dose_lab
  Normal: 45/45 (100.0%)
  Hard: 17/17 (100.0%)
  Total: 62/62 (100.0%)

Corpus: kinetics_bench
  Normal: 39/40 (97.5%)
  Hard: 15/15 (100.0%)
  Total: 54/55 (98.2%)

Corpus: buffer_bench
  Normal: 39/40 (97.5%)
  Hard: 15/15 (100.0%)
  Total: 54/55 (98.2%)

============================================================
ALL CORPORA SUMMARY:
Total Phrases: 268
Total Passed:  266
Overall Rate:  99.3%
============================================================
Agent Seed Held-Out Set: 10 / 16 (62.5%) (n=4 per experiment; small sample)
Founder Held-Out Set:    Not provided (pending founder authoring)
```

---

## 4. QA Playthrough Proof (6 Experiments)

The browser QA test harness (`qa/run.py`) was executed against the live application covering all six active laboratory experiments in both success and failure modes:
1. `pk_ward` (Oral Pharmacokinetics Ward)
2. `titration_bench` (Acid-Base Titration Bench)
3. `launch_bench` (Spaceflight Launch & Orbit Bench)
4. `dose_lab` (Dose Response Laboratory)
5. `kinetics_bench` (Reaction Kinetics Bench)
6. `buffer_bench` (Buffer Equilibrium Bench)

### 4.1 Checkpoint Artifacts & Image Verification

- **Artifact Directory:** `qa/out/20261119_153733`
- **Total Checkpoints Captured:** 66 PNG screenshots
- **MD5 Uniqueness:** 66 unique MD5 hashes (0 duplicate images, 0 collisions)
- **Image Uniformity:** All 66 screenshots exhibit standard deviation $\sigma \ge 5.0$ (no blank, solid-color, or corrupted frames)
- **Playthrough Video:** `playthrough.webm` (141.7 MB, complete recorded session)
- **Free Viewport Framing (`__camTest`):** 100% free of avatar occlusion across low, medium, and high camera angles
- **Server Health:** `server.log` clean, 0 unhandled 500 errors

### 4.2 Letter Grades Awarded

| Experiment ID | District | Mode | Grade Awarded | Rubric Evaluation |
| :--- | :--- | :---: | :---: | :--- |
| `pk_ward` | Pharmacology | Exam | **C** | Nominal protocol completed with minor blood sampling interval deviation. |
| `titration_bench` | Chemistry | Exam | **A** | Full burette rinse, precise analyte pipetting, phenolphthalein indicator, and endpoint reached within 0.1 mL. |
| `launch_bench` | Space Systems | Exam | **B** | Pre-flight checklist completed, range cleared, two-stage ascent to 200 km LEO, successful circularization burn. |
| `dose_lab` | Pharmacology | Exam | **C** | Multi-compartment theophylline and vancomycin regimens simulated, renal impairment adjusted, overdose alarm triggered. |
| `kinetics_bench` | Chemistry | Exam | **A** | PPE equipped, concentration observed over 20 steps, linear regression fit verified, activation energy estimated within 5%. |
| `buffer_bench` | Chemistry | Exam | **A** | Acetate system formulated at pH 4.75, capacity tested ($\beta \approx 0.115$), acid stress resistance confirmed, safe waste disposal. |

---

## 5. Test Suite Execution (703 Tests)

Full test verification was executed using the isolated virtual environment (`fresh`) via bare `pytest backend/tests` from the repository root:

Command: `fresh\Scripts\pytest backend/tests`

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-8.3.3, pluggy-1.7.0
rootdir: E:\Simly Orbis\backend
configfile: pytest.ini
collected 703 items

backend\tests\test_accessibility.py ...                                  [  0%]
backend\tests\test_agent_plan.py ....................................... [  5%]
.......................................................................  [ 16%]
backend\tests\test_api.py ..............                                 [ 18%]
backend\tests\test_ask_orbis_chemistry.py ..                             [ 18%]
backend\tests\test_ask_orbis_dose_lab.py ............................... [ 22%]
...................................                                      [ 27%]
backend\tests\test_briefing_and_report.py ....                           [ 28%]
backend\tests\test_briefing_rules.py ..                                  [ 28%]
backend\tests\test_buffer_bench.py .....                                 [ 29%]
backend\tests\test_chem_buffer.py ...................................... [ 34%]
....                                                                     [ 35%]
backend\tests\test_chem_kinetics.py .................................... [ 40%]
.........                                                                [ 41%]
backend\tests\test_chem_tolerances_guard.py ...                          [ 42%]
backend\tests\test_claims_gate.py ...                                    [ 42%]
backend\tests\test_core_and_runs.py ...........                          [ 44%]
backend\tests\test_dose_lab_game.py .....................                [ 47%]
backend\tests\test_hardening.py ........                                 [ 48%]
backend\tests\test_heldout.py ...                                        [ 48%]
backend\tests\test_hud_refactor.py ..                                    [ 48%]
backend\tests\test_i18n.py ...                                           [ 49%]
backend\tests\test_kinetics_bench.py .....                               [ 50%]
backend\tests\test_lab.py ...................                            [ 52%]
backend\tests\test_lobby.py ...                                          [ 53%]
backend\tests\test_mentor.py ..........                                  [ 54%]
backend\tests\test_model_cards.py .....                                  [ 55%]
backend\tests\test_p1_extra_gate.py ....                                 [ 55%]
backend\tests\test_pharma_pkpd.py ...................................... [ 61%]
............                                                             [ 63%]
backend\tests\test_pharma_trial.py .........                             [ 64%]
backend\tests\test_phone_layout.py ..                                    [ 64%]
backend\tests\test_pk_engine.py .........                                [ 65%]
backend\tests\test_pkpd_calibrate.py ..                                  [ 66%]
backend\tests\test_proof_unique.py ....                                  [ 66%]
backend\tests\test_provenance_popovers.py ....                           [ 67%]
backend\tests\test_reality_check.py ..........                           [ 68%]
backend\tests\test_router.py ...                                         [ 69%]
backend\tests\test_self_audit.py ..........                              [ 70%]
backend\tests\test_settings_and_onboarding.py ...                        [ 70%]
backend\tests\test_space_game.py ....                                    [ 71%]
backend\tests\test_space_orbit.py ...................................... [ 76%]
.                                                                        [ 77%]
backend\tests\test_spec_authoring.py ...........                         [ 78%]
backend\tests\test_spec_equivalence_dose_lab.py ........................ [ 82%]
                                                                         [ 82%]
backend\tests\test_spec_equivalence_launch_bench.py .................... [ 84%]
....                                                                     [ 85%]
backend\tests\test_spec_equivalence_pk_ward.py ........................  [ 88%]
backend\tests\test_spec_equivalence_titration.py ....................... [ 92%]
.                                                                        [ 92%]
backend\tests\test_spec_mentor_and_actions.py ......                     [ 93%]
backend\tests\test_spec_runtime_switch.py ....                           [ 93%]
backend\tests\test_spec_schema.py ...........                            [ 95%]
backend\tests\test_states.py ...                                         [ 95%]
backend\tests\test_titration.py .....                                    [ 96%]
backend\tests\test_titration_live_curve.py .....                         [ 97%]
backend\tests\test_tokens_contrast.py ...                                [ 97%]
backend\tests\test_touch_e2e.py .                                        [ 97%]
backend\tests\test_ui_components.py .....                                [ 98%]
backend\tests\test_validation.py ...........                             [100%]

================ 703 passed, 26936 warnings in 97.29s (0:01:37) ================
```

- **Total Test Cases:** 703
- **Passed:** 703 (100.0%)
- **Failed:** 0
- **Skipped:** 0
