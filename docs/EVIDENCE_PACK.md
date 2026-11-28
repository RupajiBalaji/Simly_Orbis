# Simly Orbis — Evidence & Trust Pack (P8)

## 1. Literature Validation Status
- **Verified by human domain expert:** **0 rows verified** (`verified_by = unverified` across all rows in `validation/data/*.csv`).
- **Pending human verification:** All reference rows in:
  - `validation/data/pharma_pk_references.csv`
  - `validation/data/chem_titration_references.csv`
  - `validation/data/pkpd_references.csv`
  - `validation/data/space_orbit_references.csv`
  - `validation/data/pharma_trial_references.csv`
- **Workflow:** Experts inspect rows read-only via `frontend/expert.html` (`/api/validation/review`), export a worksheet, and the founder applies verified entries with `scripts/apply_verification.py --file <worksheet>`.

## 2. Protected Engine Immutability
All five protected simulation engines remain untouched relative to baseline `cb9b66f`:
- `backend/app/modules/pharma_pk.py`
- `backend/app/modules/pharma_trial.py`
- `backend/app/modules/chem_titration.py`
- `backend/app/modules/space_orbit.py`
- `backend/app/space/orbit.py`

## 3. Tolerance File SHA-256 Hashes
The tolerance specifications have not been modified:
- `validation/tolerances.yaml` (`5b5d857e...`)
- `validation/space_tolerances.yaml` (`fc4ba76c...`)
- `validation/pkpd_tolerances.yaml` (`443d18ab...`)
- `validation/chem_tolerances.yaml` (`2288d01d...`)

## 4. Automated Test Coverage
- Backend pytest suite (`backend/tests`) covers simulation engines, safety rules `R1`–`R10` and `S1`–`S8`, classroom RBAC/auth matrix, server-verified submissions, AI refusal red-team checks, and verification tooling.
- Note: Automated tests verify software behavior and numerical consistency against unverified reference tables; they do **not** substitute for human domain-expert sign-off.

## 5. Human Action Required (Sign-Off Fields)
| Item | Owner | Status | Date |
| --- | --- | --- | --- |
| Pharmacology reference verification (`pharma_pk`, `pkpd`) | | Pending | ____-__-__ |
| Chemistry reference verification (`chem_titration`) | | Pending | ____-__-__ |
| Space orbital reference verification (`space_orbit`) | | Pending | ____-__-__ |
| Legal review for pilot with minors (DPDPA 2023) | | Pending | ____-__-__ |
