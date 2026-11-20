# Simly Orbis — Phase P4 Recheck and Verification (Addendum F10–F12)

**Date:** 2026-11-20  
**Platform Version:** `0.7.0-dev`  
**Branch:** `phase-p4-pharma`  
**Base Commit at Start of Recheck:** `b94392d`  
**Governance Standard:** Educational Simulation &bull; Not Medical Advice &bull; Not Clinical Evidence  

---

## Overview

As part of the Phase P4 Recheck Addendum, tasks F10 through F12 were executed first against the real repository:
1. **F10 Clean-Clone Test Run & Gate 3 Enforcement:** Reproducing what CI does: clean git clone into a temporary directory, new virtual environment, pip install requirements only (no playwright, no `qa/out`), bare `pytest backend/tests` execution, marking browser tests with marker `browser` (`--browser` flag / `RUN_BROWSER_TESTS=1`), using `importorskip("playwright")` inside tests, and providing a fixture directory for `qa/out` tests.
2. **F11 Gate 6 Real Protected Engine Paths & Rule ID Deletion Parser:** Replaced `PROTECTED_ENGINE_FILES` with the 8 real engine paths, enforcing disk existence, diff verification against baseline / introduction commits, parsing rule IDs (R1–R10, S1–S8, D1–D8) from deleted diff lines in `backend/app/lab/rules.py`, and adding negative tests for planted mutations and missing paths.
3. **F12 Rate-Limit Bypass Hardening:** Enforced `is_test_runner` to be true strictly when `ENVIRONMENT` is test/testing or `QA_MODE=true` AND `ENVIRONMENT` is not production (`RENDER=true` counts as production). Completely removed client-controlled `host == "test"` and `netloc == "test"` bypasses. Test suite configures `ENVIRONMENT=test` in `conftest.py`. Added unit tests verifying rate limits are enforced in production even when `QA_MODE=true` and `Host: test` are supplied.

---

## Fix F10: Clean-Clone Test Run, Browser Markers, and QA Fixture

### Commits
- `c90ef2c` (`feat(ci): add clean-clone test procedure, browser marker, and qa fixture (F10)`)
- `19892ee` (`fix(tests): cross-platform line ending normalization in tolerance checks and mock cat-file (F10)`)

### Implementation Details
1. **Registered `@pytest.mark.browser`:** Added marker definition to `backend/pytest.ini` and registered `--browser` command-line option in `backend/tests/conftest.py`.
2. **Custom Hook for Selective Browser Skipping:** In `conftest.py`'s `pytest_collection_modifyitems`, tests marked with `browser` are dynamically skipped unless `--browser` or `RUN_BROWSER_TESTS=1` is provided:
   ```python
   def pytest_collection_modifyitems(config, items):
       run_browser = config.getoption("--browser") or os.environ.get("RUN_BROWSER_TESTS", "").lower() in ("1", "true")
       if not run_browser:
           skip_browser = pytest.mark.skip(reason="requires --browser flag or RUN_BROWSER_TESTS=1")
           for item in items:
               if "browser" in item.keywords:
                   item.add_marker(skip_browser)
   ```
3. **Playwright Import Isolation:** Moved top-level `playwright` imports inside the actual test functions using `pytest.importorskip("playwright")` and `pytest.importorskip("playwright.sync_api")` in:
   - `backend/tests/test_trial_ui_equivalence.py`
   - `backend/tests/test_touch_e2e.py`
4. **Temporary Fixture Folder for QA Artifacts:** Created `qa_fixture_repo` in `backend/tests/test_self_audit.py` that populates a synthetic `qa/out/<timestamp>` folder with report and 20 distinct media files, eliminating tests' dependence on an untracked real `qa/out` directory.
5. **Cross-Platform CRLF Normalization:** Updated tolerance and held-out tests (`test_chem_tolerances_guard.py`, `test_validation.py`, `test_heldout.py`) to normalize `\r\n` to `\n` before computing SHA-256 hashes, ensuring byte-identical hashes across Windows and Linux clean clones.
6. **Gate 3 Clean-Clone Enforcement:** In `scripts/self_audit.py`, Gate 3 performs the complete clean-clone workflow (temp directory, new venv, `requirements.txt` + `requirements-dev.txt` install only, bare `pytest backend/tests`).

### Real Clean-Clone Test Execution Output
```
PS E:\Simly Orbis> fresh\Scripts\python -c "from pathlib import Path; from scripts.self_audit import check_pytest_run; res = check_pytest_run(Path('.')); print('Passed:', res.passed); print('Evidence:', res.evidence)"
Passed: True
Evidence: [clean-clone venv] `=============== 777 passed, 2 skipped, 30257 warnings in 22.11s ===============`
```

---

## Fix F11: Gate 6 Real Paths & Rule ID Deletion Parser

### Commits
- `c56da4a` (`fix(audit): update Gate 6 real protected engine paths and rule ID deletion parser (F11)`)
- `d041c64` (`test(audit): use pharma_pk for planted change and cat-file commit filter in test_self_audit (F11)`)

### Implementation Details
1. **Real Protected Paths:** Replaced placeholder paths with the 8 real engine paths:
   - `backend/app/modules/pharma_pk.py`
   - `backend/app/modules/pharma_trial.py`
   - `backend/app/modules/chem_titration.py`
   - `backend/app/modules/space_orbit.py`
   - `backend/app/space/orbit.py`
   - `backend/app/pharma/pkpd/engine.py`
   - `backend/app/chem/kinetics.py`
   - `backend/app/chem/buffer.py`
2. **Disk Existence Check:** Gate 6 verifies that all 8 files exist on disk (`is_file()`). If any path is missing, Gate 6 fails immediately.
3. **Introduction Commit Tracking:** For engines introduced after baseline commit `cb9b66f` (`pkpd/engine.py`, `kinetics.py`, `buffer.py`), Gate 6 resolves their introduction commit via `git log --diff-filter=A` and verifies 0 diff since introduction.
4. **Parsed Rule ID Protection for `backend/app/lab/rules.py`:** Replaced naive text-pattern matching with a rule ID regex parser:
   ```python
   rule_id_pattern = re.compile(r'rule_id\s*=\s*["\']([A-Za-z0-9_-]+)["\']')
   protected_id_re = re.compile(r'^(R(?:10|[1-9])(?:_[A-Z0-9_]+)?|S[1-8](?:_[A-Z0-9_]+)?|D[1-8](?:_[A-Z0-9_]+)?)$')
   ```
   Gate 6 flags unauthorized mutations if any deleted diff line matches a protected rule ID among R1–R10, S1–S8, or D1–D8.
5. **Negative Test Coverage:** Added unit tests in `backend/tests/test_self_audit.py`:
   - `test_audit_check_protected_files_fails_on_missing_path`: Fails when a protected path is missing.
   - `test_audit_check_protected_files_fails_on_planted_change`: Fails when diff contains unauthorized modification.
   - `test_audit_check_protected_files_fails_on_deleted_rule`: Fails when diff contains a deletion of rule `D1`.

### Real Gate 6 Verification Output
```
PS E:\Simly Orbis> fresh\Scripts\python -c "from pathlib import Path; from scripts.self_audit import check_protected_files; res = check_protected_files(Path('.')); print('Passed:', res.passed); print('Evidence:', res.evidence); print('Details:\n', res.details)"
Passed: True
Evidence: Protected files checked: 8 engines + R1-R10/S1-S8/D1-D8 rules. Violations: 0 files, 0 deleted rules.
Details:
 - `backend/app/modules/pharma_pk.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/modules/pharma_trial.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/modules/chem_titration.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/modules/space_orbit.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/space/orbit.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/pharma/pkpd/engine.py`: 0 diff vs `bd8ce6d` (PASS)
- `backend/app/chem/kinetics.py`: 0 diff vs `8c9609b` (PASS)
- `backend/app/chem/buffer.py`: 0 diff vs `6b6bc5e` (PASS)
- Rules R1-R10, S1-S8, and D1-D8: Unmodified (PASS)
```

---

## Fix F12: Rate-Limit Bypass Hardening

### Commit
- `d684a1f` (`fix(security): prevent rate limit bypass via Host header and enforce production checks (F12)`)

### Implementation Details
1. **Removed Client-Supplied Header Bypasses:** In `backend/app/main.py` (`SecurityAndRateLimitMiddleware`), removed:
   - `request.url.netloc == "test"`
   - `request.headers.get("host") == "test"`
2. **Production Immunity:** In production environments (`ENVIRONMENT=production` or `RENDER=true`), `is_test_runner` is strictly `False`. Neither `QA_MODE=true` nor client headers can bypass rate limiting.
3. **Explicit Test Client Environment:** Added `os.environ["ENVIRONMENT"] = "test"` in `backend/tests/conftest.py` so the test client operates in test mode without relying on `Host: test`.
4. **Hardening Tests Added in `backend/tests/test_hardening.py`:**
   - `test_production_mode_with_qa_mode_and_host_test_must_rate_limit`: Asserts that `ENVIRONMENT=production` with `QA_MODE=true` and `Host: test` triggers HTTP 429 when the limit (20 req/min) is exceeded.
   - `test_render_production_mode_must_rate_limit`: Asserts that `RENDER=true` enforces rate limits even if `ENVIRONMENT=test`.
   - `test_non_production_test_environment_bypasses_rate_limit`: Asserts that local test execution (`ENVIRONMENT=test`) bypasses rate-limiting for test runs.

### Real Test Output
```
PS E:\Simly Orbis> fresh\Scripts\python -m pytest backend/tests/test_hardening.py -q
...........                                                              [100%]
11 passed in 0.47s
```

---

## Commit Log for Addendum F10–F12

```
d041c64 test(audit): use pharma_pk for planted change and cat-file commit filter in test_self_audit (F11)
19892ee fix(tests): cross-platform line ending normalization in tolerance checks and mock cat-file (F10)
c90ef2c feat(ci): add clean-clone test procedure, browser marker, and qa fixture (F10)
c56da4a fix(audit): update Gate 6 real protected engine paths and rule ID deletion parser (F11)
d684a1f fix(security): prevent rate limit bypass via Host header and enforce production checks (F12)
261813a fix(security): pre-launch security audit hardening and dependency updates
```
