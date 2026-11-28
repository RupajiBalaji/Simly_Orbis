# Pull Request: `phase-p5-space` → `main`

## Summary
Brings Simly Orbis from `main` (`cb9b66f`) through Phases **P1–P5**, **UX & Controls Fixes (Problem A & B)**, **UI Rounds 2 & 3 (U1–U7, V1–V5)**, and **P5-HARDEN-ALL (T1–T10)**:

- **3D Interactive Districts**:
  - **Pharma**: `pk_ward` (Oral PK Ward) & `dose_lab` (Dose Response Lab with 1- and 2-compartment PK/PD, adult-only covariates, and 1,000-subject virtual clinical trial gallery).
  - **Chemistry**: `titration_bench`, `kinetics_bench`, and `buffer_bench`.
  - **Space**: `launch_bench` (Launch & Orbit Bench with Launch Pad A, rocket staging, Keplerian orbits, Hohmann GEO transfer, and 5 failure modes).
- **Clean 5-Element Progressive Disclosure HUD & Controls**:
  - Reduced persistent HUD to 5 elements (`top-left`, `top-right`, `task-card`, `ask-orbis`, `dr-orbis`) with >=70% 3D scene visibility on desktop.
  - Unified Current Task primary action button (`Go to <Station> and do this` walk-and-act, `❓ What do I do?` popover, 5-second post-walkthrough pulse).
  - Accurate starting `Score: 100` (sum of backend `score_parts`) and normalized `Safety 100/100` (green/neutral with 0 violations; missing PPE shown as a `📋 To-Do` chip).
  - Stacked mobile header at `390x844` (zero text clipping), Launch Bench PBR lighting + full-pad Pad View camera (`32.1m`), and pure `movement_math.js` locomotion basis.
- **Security & Hardening**:
  - Shared `resolve_client_ip(request)` in `app.security` with `TRUST_PROXY` gating and last-hop `X-Forwarded-For` handling used by `SecurityAndRateLimitMiddleware` and `routes/specs.py`.
  - Protected engines and frozen `*tolerances*` files remain untouched vs `cb9b66f`.

## Verification Gates
- `pytest backend/tests` (clean clone): **0 failures**
- `node --test frontend/tests/movement_math.test.mjs`: **6/6 pass**
- `python scripts/check_claims.py`: **PASS**
- `python scripts/self_audit.py`: **PASS**
- `python qa/run.py`: **PASS** (including `pk_ward` movement & camera yaw assertions)

## Known Limitations & `BLOCKED-HUMAN`
- **Educational simulation only** — not medical advice, not clinical evidence, not mission-planning software.
- Validation rows (`validation/data/*.csv`) remain `verified_by = "unverified"` pending founder/expert sign-off (`ISSUE-001`, `ISSUE-014`).
- India DPDP compliance review remains `BLOCKED-HUMAN` (`ISSUE-015`).
