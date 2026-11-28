# Simly Orbis — Teacher Guide

Welcome to the Simly Orbis Classroom Pilot! This guide covers everything you need to run a classroom session safely and without collecting student PII.

## 1. Getting Your Teacher Account (Invite-Only)
During the pilot, teacher accounts are provisioned by the Simly Orbis administrator using `scripts/create_teacher.py`:
1. You will receive a **single-use, expiring invite token** (default TTL: 60 minutes).
2. Open `/teacher.html` in your browser.
3. Paste your invite token and click **Redeem Invite Token**.
4. Once redeemed, your browser stores a short-lived teacher session token for the dashboard.

## 2. Creating a Class & Sharing the Join Code
1. In the **Create Class** panel, enter a class name (e.g. `Pharm 201 - Section A`) and click **Create Class**.
2. Copy the generated **6-character Join Code** and share it with your students in class.
3. Need to revoke an old code? Click **Reset Join Code** at any time—the old code stops working immediately.

## 3. How Students Join (Privacy-First)
1. Students open `/student.html`.
2. They enter the **Class Code** and a **Nickname** (2–24 characters).
   - **No student email or password** is ever requested or stored.
   - The nickname filter automatically blocks email addresses, phone numbers, URLs, and inappropriate language.
3. Students can optionally check **Opt in to class leaderboard** (off by default).

## 4. Creating Assignments
1. In **Assign Experiment**, choose an `Experiment ID` (e.g. `pk_oral_ward`, `launch_orbit_bench`, `chem_titration`, `pharma_trial`).
2. Add a title, optional **Parameter Presets** JSON (e.g. `{"dose_mg": 500}`), an optional ISO due date, and check **Graded assignment** (or leave unchecked for practice).
3. Students see the assignment immediately in `/student.html` and can submit their completed runs.

## 5. Reviewing Progress, Analytics & CSV Export
- **Roster:** Shows student nicknames and leaderboard opt-in status.
- **Submissions:** Shows each student's nickname, assignment, grade, score, rule violations, and completion time.
- **Class Analytics:** Highlights the most frequent rule violations, average score per experiment, and common mistakes.
- **Export CSV:** Downloads a nickname-only CSV of all submissions (no emails, no IP addresses).

## 6. Deleting a Class
Click **Delete Class & Data** on `/teacher.html`. This permanently deletes the class, all memberships, all assignments, all submissions, and all student session tokens linked to that class.

## 7. Privacy & Minors Notice
See `docs/PRIVACY.md` and `/privacy.html`. **A pilot with minors requires legal review.** Before running any pilot with users under 18, ensure school/guardian consent and legal review of applicable data-protection requirements.
