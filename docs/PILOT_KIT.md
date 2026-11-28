# Simly Orbis — Pilot Kit (P10)

> [!IMPORTANT]
> **Legal & Compliance Notice:** This document is **not a legal compliance claim**. Any **pilot with minors requires legal review** (including India's DPDPA 2023 and applicable school/institutional policies) before students under 18 use the platform.

## 1. Teacher Quick-Start (10 Minutes)
1. **Receive invite token:** The pilot administrator runs `scripts/create_teacher.py` and sends you a single-use invite token.
2. **Sign in (`/teacher.html`):** Paste your invite token and click **Redeem Invite Token**.
3. **Create a class (2 min):** Enter a class name (e.g. `Pharm 201 — Section A`) and click **Create Class**. Copy the 6-character join code.
4. **Assign an experiment (2 min):** Choose an experiment ID (e.g. `pk_ward`, `titration_bench`, `launch_bench`, `dose_lab`, `kinetics_bench`, `buffer_bench`), enter a title, and click **Create Assignment**.
5. **Share with students (1 min):** Share the `/student.html` URL and the 6-character join code. Tell students to pick a **nickname** (no real name, email, or phone number).
6. **Review results & export (5 min):** Watch submissions appear in the **Submissions** table, check **Class Analytics**, and click **Export CSV** when done.

## 2. What to Tell a Teacher
- **No student accounts or passwords:** Students only enter the class join code and a classroom-appropriate nickname.
- **Server-verified scores:** Scores, grades, and rule violations are computed and verified on the server from the finished lab report — students cannot edit their scores.
- **Educational simulation only:** Simly Orbis is a teaching simulator, **not** medical, clinical, or aerospace advice.
- **Data deletion:** You can delete a class and all its linked student data anytime with **Delete Class & Data** on `/teacher.html`.

## 3. Pilot Consent Note (Template — Requires Legal Review)
- **Purpose:** Evaluate 3D interactive science labs (`pk_ward`, `titration_bench`, `launch_bench`, etc.) in an educational setting.
- **Data collected:** Anonymous session IDs, chosen nicknames, simulation scores, rule violations, and completion times. No student emails, passwords, phone numbers, or audio recordings are stored by Orbis.
- **Optional voice input:** If a student uses the microphone button, browser speech recognition may send audio to the browser vendor (e.g., Google in Chrome); typing is always available.
- **Reminder:** **Not a legal compliance claim; a pilot with minors requires legal review** by the institution's legal counsel before deployment.
