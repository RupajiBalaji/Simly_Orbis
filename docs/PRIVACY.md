# Simly Orbis Privacy Notice

**Important Legal Notice:** **A pilot with minors requires legal review.** Before any pilot that includes users under 18, the founder must confirm the requirements of India's Digital Personal Data Protection Act, 2023 (DPDPA) and its rules with qualified legal counsel. Simly Orbis does **not** claim legal or regulatory compliance until that review is completed.

## 1. Plain-Language Summary
- **Minimal collection:** Students join classes with a class code and a nickname. We do **not** ask for or store student email addresses, passwords, phone numbers, or real names.
- **No ads or third-party trackers:** Simly Orbis has zero advertising and zero third-party analytics or tracking SDKs.
- **Educational simulation only:** Simly Orbis is a learning simulator, not medical, clinical, or aerospace advice.

## 2. Data Inventory
### What We Store
- **Session records:** Anonymous session IDs, experiment IDs, simulation state, timestamps.
- **Scores, grades, and rule violations:** Experiment scores, grades, rule violation IDs, and completion times.
- **Nicknames:** Student-chosen classroom or leaderboard nicknames (filtered to block emails, phone numbers, and profanity).
- **Class codes:** Stored as cryptographic SHA-256 hashes (never plaintext).
- **Teacher email:** Stored only for invite-only pilot teacher accounts created by the founder.
- **AI usage counts:** Daily/session request counts and token counts (cost accounting).
- **First-party analytics events:** Aggregated, non-PII in-app usage counts.

### What We Do NOT Store
- **Student email addresses** or student passwords.
- **Long-term IP addresses** (in-memory rate-limit counters expire automatically within minutes).
- **Browser speech recognition (optional mic button):** When you use the microphone, your browser's speech recognition engine processes audio. In Chrome, this is handled by Google's servers — Orbis never receives or stores your audio. Typing is always available as an alternative.
- **AI prompt content** (off by default; only enabled if the founder explicitly turns on debug content logging).

## 3. Retention Schedule (Configurable)
Every retention period is controlled by application configuration (`backend/app/config.py`):
- **Guest sessions (`GUEST_SESSION_RETENTION_DAYS`, default `90` days):** Automatically purged after 90 days via `scripts/run_retention.py` and MongoDB TTL indexes.
- **Class data:** Kept until the teacher deletes the class.
- **Invite & session tokens (`TEACHER_INVITE_TTL_MINUTES`, `TEACHER_SESSION_TTL_HOURS`, `STUDENT_SESSION_TTL_HOURS`):** Short-lived and automatically invalidated on expiry.

## 4. Deletion Procedure
- **Teacher self-service class deletion:** In the Teacher Dashboard (`frontend/teacher.html`) or via `DELETE /api/classroom/classes/{class_id}`, a teacher can permanently delete a class. This cascades immediately and deletes the class record, all memberships, all assignments, all submissions, and all student session tokens linked to that class.
- **Deletion requests:** Students, parents/guardians, teachers, or school administrators can request deletion of a teacher account or any remaining session/report data by contacting the pilot administrator with the class ID, teacher email, or session ID. Requests are fulfilled by running the cascade deletion / retention script and removing the matching database records within 7 days.
