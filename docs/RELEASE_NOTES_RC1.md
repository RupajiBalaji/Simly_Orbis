# Simly Orbis — Release Candidate Notes (`1.0.0-rc.1`)

## Release Highlights
- **Classroom & RBAC (P6 + P6-FIX):**
  - Invite-only teacher accounts (`scripts/create_teacher.py`, `/teacher.html`), nickname-only student join (`/student.html`), assignments, opt-in leaderboards, analytics, and formula-safe CSV export.
  - **Server-verified submissions:** `POST /api/classroom/student/assignments/{id}/submit` accepts only `session_id` and reads score, grade, violations, and time from the server's `lab_reports` collection.
  - Case-insensitive per-class nickname uniqueness (`409 Conflict`), indexed `join_code_hash` lookup, and `404` cross-tenant teacher isolation.
- **AI Safety & Evaluation (P7):**
  - Dr. Orbis mentor & Ask Orbis with explicit `refused` flags, daily token/cost caps, rule-based fallbacks for all 34 rule IDs, and `scripts/eval_ai.py` (`docs/AI_EVAL_LATEST.md`).
  - Browser speech recognition disclosure in `docs/PRIVACY.md`, `frontend/privacy.html`, and the mic tooltip.
- **Evidence & Software Quality (P8–P9):**
  - `scripts/apply_verification.py` and read-only `/expert.html` for human expert reference sign-off (`docs/EVIDENCE_PACK.md`).
  - Concurrent load test (`scripts/load_test.py`, `docs/LOAD_TEST.md`), security checklist (`docs/SECURITY_CHECKLIST.md`), backup/restore procedure (`docs/BACKUP_RESTORE.md`), and WCAG accessibility improvements on `teacher.html` and `student.html`.
- **Pilot Kit (P10):**
  - `docs/PILOT_KIT.md`, `docs/USER_TEST_SCRIPT.md`, `docs/HELP_CENTRE_FAQ.md`.

## Known Items & BLOCKED-HUMAN
- **Version string (`app_version`):** `backend/app/config.py` remains at `0.9.0-dev` until founder/release sign-off (marked **BLOCKED-HUMAN** for `1.0.0-rc.1` tag/bump).
- **Literature verification:** 0 rows verified by a human expert (`docs/EVIDENCE_PACK.md`).
- **Real GPU/mobile rendering benchmarks:** Documented as **BLOCKED-HUMAN** in `docs/PERFORMANCE_PROCEDURE.md`.
- **Legal review for minors:** Required before any pilot with users under 18 (`docs/PRIVACY.md`, `docs/PILOT_KIT.md`).
