# Merge Checklist: `phase-p5-space` → `main`

> **Educational simulation platform. Not medical advice. Not clinical evidence.**

## 1. Pre-Merge Safety Tag (`BLOCKED-HUMAN` / Founder Action)
Before merging `phase-p5-space` into `main`, tag the current `main` HEAD so rollback is instantaneous:
```bash
git checkout main
git pull origin main
git tag -a pre-p5-main -m "Backup tag of main prior to merging phase-p5-space"
git push origin pre-p5-main
```

## 2. Automated Gate Verification (Clean Clone)
All gates must pass on the exact `phase-p5-space` commit being merged:
1. `pytest backend/tests` (0 failures)
2. `node --test frontend/tests/movement_math.test.mjs` (6/6 pass)
3. `python scripts/check_claims.py` (`[PASS]`)
4. `python scripts/self_audit.py` (all gates PASS)
5. `python qa/run.py` (all playthroughs + movement metrics PASS)
6. Protected engine & tolerance diff check against `cb9b66f`:
   - `git diff --stat cb9b66f -- backend/app/modules/pharma_pk.py backend/app/modules/pharma_trial.py backend/app/modules/chem_titration.py backend/app/space/orbit.py validation/*tolerances*` must be empty.

## 3. Staging Verification (Render)
Deploy `phase-p5-space` to a **separate** Render staging service (see [docs/STAGING_SETUP.md](STAGING_SETUP.md)) and verify:
- `/api/health` expectations:
  - HTTP `200`
  - `"status": "ok"`
  - `"app_version": "0.9.0-dev"`
  - `"storage_mode"` reports `"mongodb"` when `MONGODB_URI` is set (or `"in_memory"` locally)
- Run live smoke check against staging URL:
  ```bash
  python scripts/smoke_live.py --url https://<your-staging-service>.onrender.com
  ```

## 4. Pull Request & Merge Commit
1. Open a Pull Request on GitHub from `phase-p5-space` into `main` using [docs/PR_DESCRIPTION.md](PR_DESCRIPTION.md).
2. Confirm GitHub Actions `Backend Unit & Validation Tests` passes.
3. Merge using **Create a merge commit** (do NOT squash or rebase so phase commit history and `cb9b66f` diff lineage stay intact).

## 5. Post-Merge Production Verification & Rollback
1. Verify production `/api/health` returns `200` with `"status": "ok"` and run `python scripts/smoke_live.py --url https://<production-url>`.
2. **Rollback procedure** (if any regression is observed in production):
   ```bash
   git checkout main
   git reset --hard pre-p5-main
   git push --force-with-lease origin main
   ```
   (Or redeploy commit `pre-p5-main` directly from the Render Dashboard **Events / Deploys** tab.)
