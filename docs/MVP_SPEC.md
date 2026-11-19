# Simly Orbis: MVP Build Specification and Agent Task Playbook

Owner: Balaji Rupaji, Founder, Urvah Dynamics Pvt Ltd. Product: Simly Orbis (the app is called Orbis Lab). Document version 1.0, 14 Nov 2026. Audience: the AI coding agent (Antigravity) and the founder.

## 0. How to use this document

This is the single source of truth for what the finished MVP must contain, how it must look, how it must behave, and in what order to build it. You are the coding agent. Read the whole document before changing anything.

- The repository is the truth about what exists today. This document is the truth about what must exist. When they disagree, do not silently change either. Write the difference into docs/GAP\_REPORT.md and follow section 1.
- Work in phases (section 18). Phases are gated: do not start phase N+1 until phase N passes its gate.
- Every task has an ID (for example P3-T4), deliverables and acceptance criteria. A task is done only when its acceptance criteria are shown with real command output, real test results or real QA artifacts.
- Priority labels: MUST = required for MVP 1.0. SHOULD = build if the phase has room, otherwise move to docs/ROADMAP.md. LATER = outside the MVP, do not build.
- If this document conflicts with a governance rule (section 2), the rule wins. If unsure, stop and put the question at the top of the phase report instead of guessing.
- Naming note: lab safety rules are R1 to R10, space rules S1 to S8, dose rules D1 to D8. Governance rules in this document are G1 to G12 so the names never clash.

## 1. Operating protocol: the recheck loop

Run this loop for every phase, in this order.

1. SYNC. Run git status, git log -15, note the branch and the version in backend/app/config.py. Create branch phase-N-name from the previous phase branch (from main for P0). Never push. Never create or move tags. Never amend or rewrite history once a self-audit has run.
2. RECHECK THE PREVIOUS PHASE. For every task of the previous phase, re-verify its acceptance criteria against the real repository, not against earlier reports. Write docs/RECHECK\_P(N-1).md with one row per task: PASS, PARTIAL or FAIL, plus the command used and its real output. Fix every FAIL or PARTIAL first, one commit per fix, message prefix fix(recheck). For P0, recheck everything built so far against sections 5 to 17.
3. BUILD. Implement the current phase's tasks in order, one commit per task, message format type(scope): summary.
4. VERIFY. Fresh virtual environment and bare pytest backend/tests from the repo root. QA harness with real screenshots and video. MD5 and near-duplicate proof check. Spec validation. The founder-written held-out parser set. Performance and accessibility checks where the phase asks for them.
5. REPORT. Write docs/PHASE\_N\_REPORT.md using the template in Appendix A.
6. SELF-AUDIT AND GATE. Run scripts/self\_audit.py as the very last step and record the HEAD hash it ran on. Commit only the audit output and report afterwards. If any gate item fails, do not start the next phase: write the blockers at the top of the report and stop.

Stop immediately and report (do not work around) if: baseline tests fail; a task would change protected engine math, frozen tolerances or an existing safety rule; more than 3 existing tests would break; any validation row would need to be marked verified; a citation cannot be given from reliable knowledge; a task cannot be completed within the governance rules.

Commit hygiene: small commits, no secrets, no stray binaries, qa/out stays git-ignored, docs updated in the same phase as the feature they describe.

## 2. Governance rules (G1 to G12, non-negotiable)

- G1 Backend is the single source of truth. Clients render results and visual directives and never decide outcomes.
- G2 AI proposes, the engine decides. Dr. Orbis and Ask Orbis never invent results, numbers or citations. Every number on screen comes from an engine or from a data file with provenance.
- G3 Honesty. Orbis Lab is an educational simulation. It is not medical advice, not clinical evidence and not mission-planning software. Never claim clinical validation or regulatory approval. Never claim it replaces animal studies or trials; say it helps reduce, refine and prioritise experiments. Targets (up to 10x faster R&D cycles, up to one tenth of early-stage cost for work that can move into simulation) are always labelled target.
- G4 Real proof only. Evidence comes from the QA harness: real screenshots, video and numbers. No file may stand in for another. The md5 and near-duplicate checker must pass. Never fabricate numbers, citations, dates, timings or frame rates.
- G5 No fabricated provenance. You cannot browse. A literature citation may be attached only if you can name the exact work (authors, title or edition, chapter, table or DOI) from reliable knowledge and mark it for human confirmation. Otherwise label the value game-balanced approximate, human verification needed. retrieved\_on stays blank on unverified rows.
- G6 Validation integrity. verified\_by is the word unverified until the founder or a qualified expert enters name:YYYY-MM-DD. Frozen tolerance files and their SHA-256 guard tests are never edited to make something pass. Every new engine gets its own tolerance file and frozen hash.
- G7 Protected code. Existing engines (pharma.pk, pharma.trial, pharma.pkpd, chem.titration, space.orbit), existing safety rules and existing visual-contract fields are protected. New behaviour goes in new files or in ADDED fields. A change to a protected file needs a task that says so explicitly, a changelog entry and golden tests.
- G8 Never loosen thresholds, delete failing tests or phrases, or edit a test so it passes. Report failures honestly and record them in docs/KNOWN\_ISSUES.md.
- G9 Safety of people. Adult-only covariate ranges (age 18 to 90, weight 40 to 150 kg, creatinine clearance 15 to 150 mL/min). No personal dosing advice: a request such as 'how much should I take' is refused with an educational explanation. The educational disclaimer is always visible on medicine-related screens.
- G10 Privacy by design. Collect the minimum. Students join with a class code and a nickname, with no student email, no third-party trackers and no ad technology. Anything touching minors' data follows section 13.
- G11 Source labels. Engine values, game-balanced constants, literature values (human-confirmed) and AI-written text must be visibly distinguishable in the UI and in reports.
- G12 Dependencies and cost. Avoid new dependencies and list any added, with pinned versions. AI calls obey per-session and daily caps and a kill switch (AI\_ENABLED). Every AI feature has a rule-based fallback that works with AI switched off.

## 3. Product definition

### 3.1 One line

An AI-assisted, game-style virtual science lab whose backend simulates real physics, chemistry and pharmacology, so ideas can be tested, broken and learned from in software before anything is built, mixed, launched or tried on animals and people.

### 3.2 The realistic ambition

The founder's phrase is 'GTA for science'. The achievable version is a Kerbal-Space-Program-style experience: stylised graphics, real equations, a sandbox, visible failures, and a character that performs your choices with its hands while the world reacts truthfully and the lab rules are enforced.

### 3.3 Why it matters

The motivation figures live in the pitch source document with their sources: large R&D spend and late failures in drug development, harm to patients, animals and the environment, and students and small labs who cannot afford to fail. Regulators are moving toward simulation (FDA Modernization Act 2.0 in 2022, the FDA's April 2025 roadmap to reduce animal testing; the status of the Modernization Act 3.0 must be re-verified before any external use). Do not add statistics anywhere without a source, and re-verify the existing ones before they are shown publicly.

### 3.4 Users

- Student or learner: wants to try things safely, see consequences, get graded, and understand why.
- Teacher or lecturer: wants to assign an experiment, see who did it, see which rules were broken, and export results.
- Researcher or startup: wants to screen an idea quickly, compare two regimens or designs, and see what is uncertain.
- Judge, investor or partner: must understand the product in three minutes and trust its honesty.
- Expert verifier: checks numbers against primary sources and records the sign-off.
- Founder or admin: runs deployments, controls AI cost, reads usage and audit reports.

### 3.5 What Orbis Lab is not

Not a medical device, not a clinical decision tool, not a substitute for lab safety training, not a validated predictor of real patient outcomes, not flight software. Clinical use would be a regulated medical-device route (CDSCO, Medical Devices Rules 2017) and is out of scope.

## 4. MVP scope

| Capability | Priority |
| --- | --- |
| Pharma district: PK Ward (13 steps), Dose Response Lab, Virtual Trial Hall (PK/PD cohort) | MUST |
| Chemistry district: Titration Bench, Kinetics Bench, Buffer Bench | MUST |
| Space district: Launch and Orbit Bench | MUST |
| Five scripted space mission scenarios (campaign) | SHOULD |
| Market district | LATER (stays locked with an honest 'coming later' card) |
| Spec-driven experiments with validator CLI and documentation | MUST |
| In-app experiment authoring form with live preview | SHOULD |
| Character with IK hands, action wheel, first-person hands view, follow and free camera | MUST |
| Dr. Orbis mentor and Ask Orbis (text, optional voice) with rule-based fallback | MUST |
| Teacher accounts, class codes, assignments, class leaderboard, CSV export | MUST |
| Guest play with nickname, no email | MUST |
| Reality Check board, Model Cards, provenance viewer | MUST |
| Expert verification workflow (worksheet export plus apply script) | MUST |
| In-app expert review page | SHOULD |
| Calibration with user-supplied concentration-time data and hold-out report | SHOULD |
| Session report (screen and printable PDF), leaderboard | MUST |
| Learning paths and badges | SHOULD |
| English UI with i18n structure | MUST |
| Hindi translation of the UI | SHOULD |
| WCAG 2.1 AA for 2D UI and a keyboard path for every 3D action | MUST |
| Phone-playable layout with touch controls | MUST |
| Privacy note, terms, disclaimers, cookie-free first-party analytics | MUST |
| Paid-tier hosting, staging environment, backups, uptime monitoring | MUST for the pilot |
| Multiplayer, user-uploaded 3D assets, marketplace, native apps, regulated clinical use | LATER |

## 5. Baseline (verify in P0, do not trust)

Last known state from the handoff and the latest reports: FastAPI with Motor (in-memory fallback), Three.js r160 vendored with no build step, Google Gemini for AI, Docker, Render hosting. Engines: pharma.pk, pharma.trial, pharma.pkpd (one- and two-compartment, IV and oral, Emax, covariates, calibration framework), chem.titration, space.orbit. Experiments: PK Ward, Acid-Base Titration Bench, Launch and Orbit Bench, Dose Response Lab. Rules R1 to R10, S1 to S8, D1 to D8. Around 411 automated tests at version 0.4.0-dev on a local, unpushed branch. 32 validation rows, all unverified. Public demo on a free Render instance that sleeps when idle. Self-audit script, QA harness (Playwright), proof-uniqueness checker, claims audit, known-issues register.

## 6. Architecture and technical constraints

- Layers: engines (pure, deterministic, unit-tested) then game layer (session engine, rules, scoring) then API (FastAPI routes, validation, rate limits) then clients (Three.js scene plus 2D HUD). The AI layer sits beside the game layer and is always behind engines.
- Folder conventions: backend/app/DOMAIN/ENGINE, specs/ for experiment specs, validation/data for reference rows, docs/, qa/, scripts/.
- API: JSON only. Add a versioned prefix /api/v1 and keep the old routes working as aliases. One error envelope everywhere: error with code, message, field and hint. Every response carries a request id. Session actions are idempotent where possible. Rate limits by route class. Pagination on every list route.
- Determinism: the same input gives the same output. Random cohorts use a seeded generator and return the seed.
- Engine registry: each engine exposes id, version, parameter bounds, units and a model-card reference. Every outcome object carries the engine id and version.
- Visual contract: engine outcomes become directives (liquid, effect, readout, vitals, label, highlight, rocket, flame, orbit\_path, stage\_sep, failure, curve, effect\_curve, window, covariate\_card). New directives are only ever ADDED. Each directive has a JSON schema and a client renderer test.
- Config: every environment variable is documented in docs/DEPLOY.md with a safe default. Feature flags live in config. AI\_ENABLED is a kill switch.
- Storage: MongoDB Atlas through Motor, with the in-memory fallback for development. Create indexes explicitly. Guest sessions are purged after a configurable retention period (target default 90 days). Provide migration scripts and a documented backup and restore procedure.
- Frontend: ES modules, vendored libraries, no build step, no inline scripts, strict CSP, self-hosted fonts.

## 7. Design system and global UI

### 7.1 Visual identity

Stylised toon-shaded 3D, a clean lab look, friendly but not childish. Calm dark UI chrome around bright, readable 3D scenes. Every district has its own accent colour, and the colour is never the only signal: pair it with an icon and text.

### 7.2 Tokens (define once in frontend/styles/tokens.css, use everywhere)

- Colour: --bg #0B1220, --surface #121B2E, --surface-2 #1A2540, --text #E8EEF9, --text-muted #9AA8C4, --accent #19C3B1 (pharma), --accent-chem #F5A524, --accent-space #7C5CFF, --ok #2EBD6B, --warn #F5A524, --danger #F0524F, --info #3B82F6. Verify every text and background pair for at least 4.5:1 contrast and fix the values if any pair fails.
- Spacing scale (px): 4, 8, 12, 16, 24, 32, 48. Radii: 8, 12, 20. Three elevation levels.
- Type: self-hosted sans and mono fonts under an open licence. Scale 12, 14, 16, 20, 24, 32, 44. Body 16, line height 1.5.
- Provide a light theme as SHOULD; dark is the default and the only MUST.

### 7.3 Components (one shared library, no one-off styling)

Button (primary, secondary, ghost, danger; minimum touch target 44 px; visible 3 px focus ring), Card, docked Panel, Modal, Toast, Tooltip, Tabs, Slider paired with a numeric input and units, Stepper for experiment steps, Gauge and Readout, Badge, Progress, Banner (disclaimer), Skeleton loader, Empty state, Error state, Command bar (the / key focuses Ask Orbis). Charts (canvas or SVG) always show axis titles with units, a legend, optional target-window band, keyboard focus, and a 'view as table' fallback for screen readers.

### 7.4 Motion and sound

Transitions 120 to 240 ms with ease-out. Respect prefers-reduced-motion by removing camera sweeps and particles. Nothing flashes more than 3 times per second, including launch effects. Sound is procedural, off until the first user interaction, has a master volume and a mute, and every important cue is also written in the on-screen log.

### 7.5 Accessibility (MUST)

WCAG 2.1 AA for all 2D UI. Every 3D action is also reachable from an Actions list panel with keyboard only. Visible focus, logical tab order, ARIA labels, a live region for the lab or mission log, text size setting from 100 to 150 percent, colour-blind-safe pairs, no information by colour alone.

### 7.6 Responsive behaviour

Desktop (1200 px and up): 3D view with docked side panels. Tablet (768 to 1199): panels collapse into tabs. Phone (under 768): full-screen 3D, bottom sheet for the action wheel and panels, on-screen joystick and tap-to-interact, landscape and portrait both usable.

### 7.7 Quality tiers

Low, Medium and High with automatic selection from a short frame-time test, a manual override in Settings, and a persisted choice. Everything must be playable on Low. Never quote frame rates from software rendering; label them 'software render, not representative'.

### 7.8 Internationalisation

All strings live in locale files, none hard-coded. Numbers and units are formatted by locale. English first; Hindi is SHOULD. The structure must make adding a language a data-only change.

### 7.9 Honesty patterns in the UI

Source chips on every number that matters: Engine, Game-balanced, Literature (unverified), AI. An always-visible 'Educational simulation, not medical advice' strip on all pharma screens. An 'Unverified' badge on validation numbers until a human signs them off. Targets always carry the word target.

## 8. Screens and flows

Every screen below must define four states: loading, empty, error and normal. Section 8.16 gives the shared rules.

### 8.1 Lobby (home)

Purpose: pick a district and an experiment in under 10 seconds and see the honesty rules at a glance.

```
+--------------------------------------------------------------+
| ORBIS LAB        [Search]      [Class code] [Settings] [Help] |
+--------------------------------------------------------------+
| Educational simulation. Not medical advice.   (always shown)  |
+--------------------------------------------------------------+
|  [PHARMA]       [CHEMISTRY]      [SPACE]        [MARKET]      |
|  3 experiments  3 experiments    1 bench +      locked,       |
|  best grade     best grade       5 missions     coming later  |
|  [Start]        [Start]          [Start]        [Why?]        |
+--------------------------------------------------------------+
| Continue last session      | Learning path progress           |
| Leaderboard (top 5)        | Reality Check summary            |
+--------------------------------------------------------------+
| Privacy | Terms | Model Cards | Docs | Version               |
+--------------------------------------------------------------+
```

Behaviour: a district card expands into experiment tiles. Each tile shows title, one-line learning goal, difficulty, time estimate, number of rules, best grade and a status chip. The locked Market card opens a short honest explanation. If the free host is asleep, show 'Waking the lab server, usually under a minute' with a progress indicator and automatic retry. Never show a blank page.

### 8.2 First-run onboarding (under 90 seconds, skippable, replayable from Settings)

Steps: welcome; nickname or class code; four-step control tutorial (move, interact, first-person view, camera); one acknowledgement of the educational disclaimer before the first pharma experiment; done. The tutorial uses a real, safe mini-scene, not a video.

### 8.3 Experiment briefing

Shown before every experiment: goal, what you will learn, equipment, the rules that will be enforced (icon plus text), how scoring works, estimated time, link to the Model Card, and two buttons: Start and Practice (no score, free hints).

### 8.4 Lab HUD (in session)

```
+--------------------------------------------------------------+
| [Menu] Experiment title   Step 4/13 [=====>   ]  Score  Timer |
+-----------------+--------------------------------+-----------+
| LEFT PANEL      |                                | RIGHT     |
| Steps checklist |          3D WORLD              | Readouts  |
| (current step   |   character, bench, apparatus, | from the  |
|  highlighted)   |   liquids, effects             | engine,   |
| Rules panel     |                                | each with |
| R1 ok  R2 ok    |   [tags: N]   [E: use object]  | a source  |
| R6 warn ...     |                                | chip      |
+-----------------+--------------------------------+-----------+
| LOG (live region)              | Ask Orbis  [ / to type ] [mic] |
| Camera: Follow | Free | Recenter   V hands  Quality  Sound  ?  |
+--------------------------------------------------------------+
```

Behaviour: panels collapse and re-dock; the log is a live region for screen readers; readouts update only from backend responses; the rules panel shows each rule as ok, warning or violated with a plain-language reason; a blocked action is explained, never silently ignored. Consequences are visible in the 3D scene. Menu holds Pause, Director Mode (Shift+D), Mistake Demo, Settings, Help and Exit. Shortcuts: WASD move, E use, V first-person hands, Shift+D Director, N tags, F3 debug, / focus Ask Orbis.

### 8.5 Action wheel

Pressing E (or tap and hold on phone) opens a radial menu of actions for the nearest object. Each action shows name, icon and key hint. A disallowed action is greyed out with the reason, for example 'Put on goggles first (R1)'. Choosing an action sends it to the backend. The engine decides whether it is allowed, allowed with a penalty, or blocked, and the character performs the hand animation that matches the engine's answer. Keyboard: arrow keys and Enter. The same actions are always listed in the Actions panel.

### 8.6 Ask Orbis panel

Text box plus microphone. It shows a plan preview as an ordered list of proposed allowed actions, then the dry-run result with predicted rule violations highlighted. Buttons: Run plan, Edit, Cancel. Parts of the request that were not understood are listed explicitly. A chip shows whether the plan came from AI or from the rule-based parser. Nothing runs before the dry run. A plan that would break a blocking rule cannot be run.

### 8.7 Dr. Orbis mentor

A docked chat panel. Replies are at most 70 words and refer to live session values. A chip shows AI or Offline hint. It shows how many questions are left in the session. A quick button 'Why did I lose points?' explains the last violations from engine data. It refuses personal medical advice with an educational explanation.

### 8.8 Session report

Contents: grade and score with the breakdown; timeline of actions; rule violations with reasons; engine results as charts with source chips; 'What you learned' sentences generated by code from engine values; comparison with your best run; Try again and Next experiment buttons; a Print or Save as PDF button; disclaimer footer. A read-only share link is SHOULD.

### 8.9 Leaderboard

Tabs: This experiment, This class, All players. Columns: rank, nickname, grade, score, time, rule-clean flag. Scores come only from backend sessions. Nicknames pass a profanity filter. Submissions are rate limited.

### 8.10 Reality Check and Model Cards

Reality Check board: for each engine, the validation rows with reference value, model value, fold error, tolerance, pass or fail, and a badge reading 'Awaiting human verification' or 'Verified by name:date'. While rows are unverified the board shows no headline accuracy figure, only 'N/A, awaiting human verification'. Model Card page per engine: purpose, equations, assumptions, valid ranges, known error, simplifications, provenance table, validation status, version and changelog. Each experiment briefing and report links to its Model Card.

### 8.11 Teacher dashboard

Create a class and get a join code. Roster by nickname. Assign an experiment with optional parameter presets, a due date and a practice or graded flag. Submissions table with grade, score, violations and time. Class analytics: the most frequent rule violations, average score per experiment, common mistakes. CSV export. Reset code. Delete class with all its data.

### 8.12 Student class view

Join with code and nickname. List of assignments. My results. Class leaderboard (opt-in).

### 8.13 Settings

Quality tier, sound and volume, text size, reduced motion, language, camera sensitivity, controls help, replay tutorial, clear local data, and an AI on or off switch for the session.

### 8.14 Experiment library and authoring (SHOULD)

Library: browse and filter by district and difficulty. Authoring form: edit spec fields with validation messages that point at the exact field, a dry run with scripted actions, a preview using the existing 3D scenes, and export of the spec file. Spec changes reach other users only after admin approval.

### 8.15 Expert review (SHOULD)

A token-gated page showing one validation row at a time with source citation, locator, reference value and model value. Buttons: confirm the reference value matches the source, or disagree with a comment. It produces a downloadable verification submission (JSON or CSV) with the reviewer's name and date. It never changes data itself. The founder applies the file with scripts/apply\_verification.py, which checks the name:YYYY-MM-DD format and writes verified\_by. Reality Check updates on the next deploy.

### 8.16 Loading, empty, error, offline

Every screen defines: loading (skeleton, not spinner-only); empty (helpful text plus a next action); error (message from the error envelope, Retry, and 'Copy diagnostics' with the request id); server asleep; WebGL not supported (explain and offer 2D charts and report); AI unavailable (rule-based fallback chip).

### 8.17 Phone specifics

Left on-screen joystick, drag on the right to look, tap objects, long-press for the action wheel. Bottom-sheet panels. 44 px minimum targets. Orientation hint. Reduced particle counts. Haptics are SHOULD.

## 9. Feature specifications by district

### 9.1 Pharma district

**PK Ward (exists, 13 steps).** One-compartment oral PK with first-order absorption. Green and red zones are game-balanced, not clinical. Keep behaviour exactly. Add Model Card link and source chips. Later migrate to a spec with golden tests.

**Dose Response Lab (exists, rules D1 to D8).** One- and two-compartment models, IV bolus, IV infusion and oral routes, Emax pharmacodynamics, covariates for weight, age and renal function, predict-then-run flow, two-regimen overlay, visible consequences (below the target window means weak effect, above the game limit means a warning effect). No real dosing advice anywhere.

**Virtual Trial Hall (exists as pharma.trial, upgrade in P4).** Cohort of 20 to 1,000 virtual adults generated from a seeded generator with documented log-normal variability in clearance, volume and absorption and documented covariate distributions inside the adult ranges. Compare two regimens. Outputs: distributions of Cmax and AUC, percent inside the game target window, percent above the game limit, and a 3D crowd gallery where each virtual patient is shown with colour and an icon. One insight sentence is produced by code, not AI. Always labelled 'virtual population, not a clinical trial'. The seed is shown and the run is repeatable. CSV export.

**Drug library (frozen in P4).** 10 to 15 drugs, every parameter with a provenance field under G5, a 'what this drug teaches' line, route list, game target window and game maximum dose. The validator rejects a drug without provenance fields.

**Calibration (SHOULD).** The user uploads a concentration-time CSV (limit rows and size, for example 5 MB). The server fits parameters and returns a hold-out report with train and test error. The screen says 'fit to your data, not validation'. Calibration is never run against the unverified reference rows.

### 9.2 Chemistry district

**Titration Bench (exists).** Exact charge-balance solver for strong and weak acids and bases with indicators, endpoint and overshoot. Henderson-Hasselbalch is used only for the half-equivalence check. MUST add: a live titration curve (pH against volume) drawn from backend points, with the indicator colour range shown. Polyprotic acids stay LATER.

**Kinetics Bench (new, P3).** Zeroth, first and second order integrated rate laws, half-life, Arrhenius k(T), and a consecutive first-order A to B to C case. The student picks temperature, initial concentration and sampling times, then tries to find the order and rate constant from the data using linearised plots (c, ln c and 1/c against time). The engine produces data with optional seeded measurement noise. The student submits an estimate and is scored on accuracy and rule compliance.

**Buffer Bench (new, P3).** Exact charge-balance buffer pH, buffer capacity, and the effect of adding strong acid or base. The student designs a buffer for a target pH and tests its capacity. Output: pH against amount added.

Constants (pKa values and others) follow G5: cite the exact work or label game-balanced approximate, human verification needed.

### 9.3 Space district

**Launch and Orbit Bench (exists, rules S1 to S8).** Rocket presets or edits within safe bounds; Tsiolkovsky delta-v with staging; thrust-to-weight gate at liftoff; ascent losses as a named game-balanced constant (default 1,500 m/s); Hohmann transfer; failure outcomes (no liftoff, suborbital fall, eccentric orbit, transfer failed); orbit view with the path from backend points.

**Mission scenarios (SHOULD, P5).** Five specs: first orbit; fuel-limited orbit; transfer to a higher orbit; abort when thrust-to-weight is too low; design to a mass budget in game units. Each has a par score and a three-step hint ladder.

Physics limits to state everywhere: 2D two-body model, spherical Earth, lumped ascent loss instead of an atmosphere model, no J2 and no third-body effects. Never describe it as mission-planning accurate.

### 9.4 Market district (LATER)

Stays locked. Card text: market simulations need data and models that will not be claimed until they can be validated. Do not build in the MVP.

## 10. Experiment spec format (how the platform scales)

An experiment is a JSON or YAML file in specs/, checked against a schema. Fields: id (slug), version, district, title, learning\_goal, difficulty, est\_minutes, engine (id, minimum version, parameter bounds), equipment, steps (id, title, allowed actions, preconditions, effects), rules (id, text, severity, condition or a reference to a built-in rule), scoring (weights and grade thresholds), visual directive mapping, mentor (hints per step and common mistakes), ask\_orbis (allowed actions and synonyms), model\_card reference, provenance block, and i18n keys.

The validator must reject: unknown fields, duplicate rule ids, actions with no handler, directives not in the schema, parameter bounds outside engine limits, constants without provenance, hard-coded strings, and pharma specs outside the adult ranges. Errors name the exact field path.

Tooling: python scripts/validate\_specs.py exits non-zero on any error and runs in CI. For each migrated experiment, golden-equivalence tests prove that scripted action sequences give identical outcomes, scores and violations in the old and new paths. Documentation: docs/experiment\_spec.md with a worked example that a teacher can follow without writing code.

## 11. Game layer

- Sessions are created by the backend and follow a state machine: briefing, running, paused, finished, abandoned. Timers run on the server. Actions are idempotent. Sessions expire.
- Rules are enforced by the engine. Each has an id, text, severity (info, penalty, block, fail) and a plain-language reason shown in the UI. New experiments use their own id prefix.
- Scoring is deterministic with a visible breakdown: correctness against the goal, rule compliance, efficiency, and prediction accuracy where the experiment has a prediction step. Weights and grade thresholds (A to D, plus F) come from the spec.
- Practice mode gives free hints and no score. A teacher can force an assignment to be graded.
- Learning paths (SHOULD): three levels per district (Guided, Open, Challenge). Badges are computed on the server: first clean run, perfect rule compliance, accurate prediction, learning from a failure.
- Director Mode and Mistake Demo are scripted runs that make real engine calls. They are never canned video.

## 12. AI layer

- Provider: Google Gemini called only from the server, key never in the client, behind a provider interface so it can be swapped. AI\_ENABLED is the kill switch.
- Dr. Orbis: server-built context (experiment, step, parameters, engine outputs, violations), last 12 turns stored server-side, at most 70 words per reply, 30 calls per session, daily cap MENTOR\_DAILY\_CAP, per-IP rate limit, injection-safe data blocks (user text is never mixed into instructions), rule-based fallback hints that use engine values, refuses personal medical advice and off-topic requests, labelled AI or Offline hint.
- Ask Orbis: the AI or the rule-based parser produces a plan from the allowed action list only. The plan is validated against a schema, dry-run before execution, and any part not understood is reported. Voice input through the browser speech API is SHOULD, with typed input always available. No audio is stored.
- Evaluation (MUST): per experiment, an author corpus (regression suite), a hard corpus (typos, vague, contradictory, unit confusion, unsafe requests) and a founder-written held-out set that the agent may not edit or tune against. Report first-run pass rates before any fix. Report the held-out rate separately with the label 'founder-written, not tuned'. Maintain a red-team set (prompt injection, dosing-advice requests, requests to invent citations, jailbreaks) where every case must be refused or neutralised.
- Cost and privacy: per-session and daily caps, token counts logged without content, content logging off by default, nicknames and class codes never sent to the model.

## 13. Accounts, classroom and privacy

### 13.1 Identities

- Guest: no sign-in, anonymous random id kept in local storage, can play every public experiment, scores appear under a nickname.
- Student: joins a class with a class code and a nickname. No email, no password. The session token is scoped to that class.
- Teacher: invite-only accounts created by the founder through an admin script for the pilot (MUST). Email magic-link sign-in is SHOULD and needs an email service, so treat it as a listed dependency and cost.
- Expert: token-gated access to the review page or worksheet only.
- Admin: the founder, token-protected admin area, never exposed in the public navigation.

### 13.2 Permissions

| Role | Play | See own results | See class data | Create classes | Verify rows | Admin |
| --- | --- | --- | --- | --- | --- | --- |
| Guest | yes | local only | no | no | no | no |
| Student | yes | yes | leaderboard only | no | no | no |
| Teacher | yes | yes | own classes | yes | no | no |
| Expert | no | no | no | no | submit only | no |
| Admin | yes | yes | all | yes | apply files | yes |

### 13.3 Data inventory

Stored: session records, scores, grades, rule violations, nicknames, class codes, teacher email, AI usage counts, first-party analytics events. Not stored: student email, long-term IP addresses (rate-limit counters expire quickly), audio, AI prompt content (unless the founder switches content logging on for debugging, which is off by default and documented).

### 13.4 Retention and deletion

Target defaults: guest sessions purged after 90 days; class data kept until the teacher deletes the class. A teacher can delete a class and everything linked to it. A documented deletion-request procedure exists in docs/PRIVACY.md. Every retention value is a config setting.

### 13.5 Minors and legal

Many users will be under 18. Collect only a nickname. School pilots need teacher or school consent. No advertising and no third-party trackers. Write a plain-language privacy note (docs/PRIVACY.md and an in-app page) and a terms page. The founder must confirm the requirements of India's Digital Personal Data Protection Act, 2023 and its rules with qualified counsel before any pilot that includes under-18 users. Until that confirmation exists, the product must not claim legal compliance.

### 13.6 Account security

Hashed secrets, short-lived tokens, rate limits on every sign-in and join route, secure headers, no tokens or class codes in URLs that get logged, and constant-time comparison for codes and tokens.

## 14. Evidence and trust system

### 14.1 Four kinds of number

Every number the user sees belongs to one of: Engine (computed by a backend engine), Game-balanced (a constant chosen for gameplay), Literature (a published value, shown as unverified until a human signs it), AI (text from the model, never numeric truth). The UI shows the matching source chip (G11).

### 14.2 Validation data

Reference rows keep the existing CSV schema: id, quantity, value, unit, population or condition, dose or regimen, source citation, source URL or DOI, retrieved\_on, verified\_by, notes. Rules: verified\_by is unverified until name:YYYY-MM-DD; retrieved\_on is blank while unverified; every row's stated conditions must agree with its value (recompute with the stated radius, dose or population); never derive a reference value from our own engine. Tolerances live in frozen files with SHA-256 guard tests, one file per engine family.

### 14.3 Verification workflow

1. scripts/make\_verification\_worksheet.py writes a worksheet (Markdown and CSV) for every row.
2. The expert reads the primary source, fills confirm or disagree, a comment, and name:date.
3. The founder runs scripts/apply\_verification.py on the returned file. The script validates the format, refuses to touch tolerances, writes verified\_by and retrieved\_on, and appends a line to validation/verification\_log.csv (append-only: row id, action, reviewer, date, tool version).
4. The Reality Check board updates on the next deploy. Disagreements become issues in docs/KNOWN\_ISSUES.md.

### 14.4 Model Cards

One per engine, generated from a template and kept in docs/model\_cards/. Fields: purpose, intended use, out-of-scope use, equations, assumptions, valid parameter ranges, known error sources, validation status, provenance table, engine version, changelog. A change to an engine version requires a changelog line and a refreshed card.

### 14.5 Calibration protocol

Fit on some data, test on held-out data, report both errors. Parameter-recovery tests use synthetic data with known truth. Never fit to the unverified reference rows. Never present a fit as validation. The first honest numbers on the early validation rows (paracetamol Cmax under-predicted by about 1.8-fold and the rest within about 2.3-fold) were produced before any human verification and must never be quoted as validated.

### 14.6 Claims governance

- docs/CLAIMS\_AUDIT.md lists every quantitative or strong claim with file, line, type (fact with source, target, feature description, risk), source, and action.
- docs/PITCH\_FACTS.md holds each public statistic with its source, and the date a human last checked it.
- A CI grep gate flags the words validated, clinically proven, replaces animal testing, FDA-approved, accurate and similar unless the line also contains a disclaimer or negation. The gate output is listed in each phase report.

### 14.7 Provenance viewer

Clicking a source chip opens a small popover: where the value came from (engine and version, constant and its note, citation and its verification status). It must work with the keyboard.

## 15. Non-functional requirements

All numbers in this section are targets to be measured, not results. Measure on hardware rendering. A software-rendered run does not count.

- Performance: lobby usable within 5 seconds on broadband once the server is awake; lobby transfer under 2 MB; lobby plus one scene under 15 MB; engine API calls at p95 under 300 ms; a 1,000-patient virtual trial in under 3 seconds; at least 30 frames per second on a mid-range Android phone at Medium, 60 on a mid-range laptop at High; no memory growth across three consecutive sessions (leak test).
- Reliability: 99% uptime during the pilot; daily database backups and a restore drill before each release; retries with backoff on the client; a crashed session can be resumed or cleanly abandoned without losing earlier results.
- Scale for the pilot: 200 concurrent students on a paid instance. Prove it with a scripted load test and record the result honestly.
- Security: OWASP ASVS Level 1 checklist completed and stored in docs/SECURITY.md. Strict CSP, security headers, CORS allow-list, input validation on every route, rate limits, secrets only in environment variables, pip-audit in CI, prompt-injection defences, no personal data in logs, admin routes behind a token with their own rate limit.
- Accessibility: automated axe checks in the QA harness plus a documented manual keyboard walk and one screen-reader pass per release.
- Browsers: latest two versions of Chrome, Edge, Firefox and Safari on desktop, Chrome on Android, Safari on iOS. WebGL2 required; a clear fallback message and 2D report view when it is missing.
- Observability: structured JSON logs with request id; a metrics route with counts and latency; /api/health extended with version, git\_sha, storage\_mode and AI status; an external uptime monitor; an alert email to the founder.
- Analytics (first-party only, no personal data, opt-out in Settings): session\_start, experiment\_start, step\_complete, rule\_violation (rule id only), session\_end (grade), error (code), tutorial\_complete.
- Cost: keep a monthly cost estimate in docs/COSTS.md covering hosting, database, AI and email, with the AI caps that bound the worst case.

## 16. QA strategy

- Test layers: unit (engines, analytic checks with hand-computed values in comments); contract (API schemas, visual-directive schemas); game (rules and scoring, deterministic, golden tests); AI (corpora and red-team); end-to-end (Playwright); visual proof; accessibility (axe); performance budgets; security (pip-audit and header checks); load; live smoke (scripts/smoke\_live.py).
- QA harness: for every experiment, one successful run, one rule-violation run and one failure run, with real screenshots at each phase, a real video, assertions that DOM values equal API values within a stated tolerance, then the md5 and near-duplicate check. Label software-render frame rates as not representative.
- CI on every push: lint, bare pytest backend/tests in a fresh environment, spec validation, claims grep gate, pip-audit, API-level playthroughs that need no WebGL. The browser QA run is triggered locally by the founder.
- Self-audit gates (scripts/self\_audit.py), each PASS or FAIL with evidence: clean tree and HEAD hash; version; fresh-venv bare pytest final line; validation governance; frozen tolerance hashes; protected files unchanged against the base hash; CI uses bare pytest; newest QA folder and md5 result; first-run parser rates; held-out rate; spec validation; claims grep; gitignore coverage; audit ran on the final HEAD.
- Regression rule: any row that was PASS in a previous recheck and fails now is a release blocker.
- User testing: a written script, a target of 30 real users, measures of task completion, time to first completed experiment, a System Usability Scale score and a short rule-comprehension check. A small comparison of practising in Orbis against not practising can be reported only with its sample size and limits stated. Do not call it proof of learning gains.

## 17. Deployment and operations

- Environments: local, staging (a branch deploy with its own database) and production.
- Config: every variable (MONGODB\_URI, GEMINI\_API\_KEY, GEMINI\_MODEL, TRUST\_PROXY, AI\_ENABLED, MENTOR\_DAILY\_CAP, ALLOWED\_ORIGINS, GIT\_SHA, retention settings and others) is documented in docs/DEPLOY.md with defaults and a startup check that fails loudly on a missing required value.
- Release process: bump the version, update CHANGELOG.md, run self-audit to PASS, deploy to staging, run smoke\_live.py, get the founder's approval, then the founder tags vX.Y.Z and pushes. Rollback means redeploying the previous tag. The agent never pushes or tags.
- Hosting for the pilot: a paid always-on instance (the free instance sleeps), the Docker image, a health check, a custom domain with TLS and HSTS. In production the in-memory fallback must be disabled: if the database is down, show a maintenance page.
- Backups: database provider backups plus a weekly dump script. Restore is rehearsed and written down.
- docs/RUNBOOK.md covers: AI cost spike (flip AI\_ENABLED), database outage, leaked key rotation, bad deploy rollback, and how to read logs by request id.
- A public status or uptime page is SHOULD.

## 18. Phased task list

This list supersedes earlier stage numbering. Version targets: P0 0.4.1-dev, P1 0.5.0-dev, P2 0.6.0-dev, P3 0.7.0-dev, P4 0.8.0-dev, P5 0.9.0-dev, P6 0.10.0-dev, P7 0.11.0-dev, P8 0.12.0-dev, P9 0.13.0-dev, P10 1.0.0-rc.1. Each task lists deliverables and ACCEPT criteria. Evidence for every ACCEPT is pasted real output in the phase report.

### 18.0 Common phase gate (every item must be PASS before the next phase starts)

- Gate 1: the previous phase's recheck file has no FAIL or PARTIAL left.
- Gate 2: a fresh virtual environment and bare pytest backend/tests pass; the count is recorded; no test was removed or weakened.
- Gate 3: protected files show zero diff against the base hash, except where a task explicitly allows a change.
- Gate 4: all validation rows are unverified or in the name:YYYY-MM-DD format; retrieved\_on is blank on unverified rows; frozen tolerance hashes match.
- Gate 5: the spec validator passes (from P2 onward).
- Gate 6: the QA harness ran with real proof; md5 and near-duplicate checks pass; DOM-versus-API assertions pass.
- Gate 7: first-run parser rates for every corpus are recorded, and the founder-written held-out rate is reported separately.
- Gate 8: the claims grep gate passes and CLAIMS\_AUDIT.md is updated.
- Gate 9: docs, KNOWN\_ISSUES.md and CHANGELOG.md are updated and honest.
- Gate 10: the phase report exists and the self-audit ran on the final HEAD.
- Gate 11: where the phase says so, accessibility and performance checks are done.

### P0 Reconcile and stabilise

- **P0-T1 Baseline and GAP report.** Clone state, fresh venv, bare pytest. Compare the repository with sections 4 to 17 and write docs/GAP\_REPORT.md: requirement, status (done, partial, missing), evidence, and the task that closes it. ACCEPT: every MUST item has a status with evidence.
- **P0-T2 Branch and CI hygiene.** Document the branch strategy (main is the rehearsed demo; one branch per phase). CI runs bare pytest, spec and claims gates, and pip-audit. ACCEPT: workflow file plus a local run of each step with output.
- **P0-T3 Provenance and claims re-audit.** Recheck all validation rows for conditions that contradict values, invented retrieval dates and derived reference values. Recheck all docs and UI text for overclaiming. ACCEPT: a table of findings and zero unexplained rows.
- **P0-T4 Held-out harness.** Load backend/tests/data/heldout\_phrases.json (founder-written, the agent never edits it) and report pass rates per experiment, separate from the agent's corpora. A guard test fails if the file's hash changes without the founder updating tests/data/heldout.sha256. ACCEPT: command output and the guard test.
- **P0-T5 Model Card skeletons** for pharma.pk, pharma.trial, pharma.pkpd, chem.titration and space.orbit under docs/model\_cards/, linked from the Reality Check board. ACCEPT: five cards, links work.
- **P0-T6 Config and health.** Startup validation of required environment variables, the full variable catalogue in docs/DEPLOY.md, /api/health with version, git\_sha, storage\_mode and AI status. ACCEPT: tests plus a documented catalogue.
- **P0-T7 PITCH\_FACTS and claims gate.** Create docs/PITCH\_FACTS.md (statistic, source, date a human last checked, left blank for the founder) and the CI grep gate from 14.6. ACCEPT: the gate fails on a planted bad phrase in a test and passes on the repository.

### P1 UI foundation and design system

Extra gate: axe has no serious or critical issues on 2D screens; screenshots at 1366x768, 768x1024 and 390x844; a keyboard-only test passes from lobby to report.

- **P1-T1 Tokens and fonts.** frontend/styles/tokens.css per 7.2, self-hosted fonts, and a script that computes contrast ratios for every text and background token pair and fails under 4.5:1. ACCEPT: script output.
- **P1-T2 Component library** per 7.3 in frontend/ui/ with a development-only page showing every component in every state. ACCEPT: DOM tests for each component; the page exists.
- **P1-T3 App shell and router.** Routes for lobby, briefing, lab, report, leaderboard, settings, Model Cards and Reality Check. Deep links and the back button work; there is a 404 page. ACCEPT: end-to-end test of each route.
- **P1-T4 Lobby** per 8.1, including the server-asleep waking state and the Market modal. ACCEPT: screenshots plus a test that simulates a slow wake.
- **P1-T5 Onboarding and Settings** per 8.2 and 8.13. ACCEPT: tutorial completes with keyboard only; settings persist across reload.
- **P1-T6 HUD refactor** per 8.4 and 8.5: panels, rules panel with plain reasons, readouts with source chips, live-region log, Actions panel, action wheel with disabled-reason text. Frontend only; engines and rules untouched. ACCEPT: all existing experiments still pass their existing QA; every 3D action is reachable from the Actions panel.
- **P1-T7 Phone layout** per 7.6 and 8.17. ACCEPT: screenshots and a touch-driven end-to-end run at 390x844.
- **P1-T8 i18n scaffolding.** locales/en.json, a t() helper, a lint script that fails on hard-coded user-facing strings in new code, and migration of lobby, HUD and report strings. ACCEPT: lint output; a test that switches to a test locale and shows every string changing.
- **P1-T9 Accessibility baseline** per 7.5. ACCEPT: axe report, keyboard walk test, focus trap tests for modals, reduced-motion test.
- **P1-T10 States.** Loading, empty, error, offline and WebGL-unsupported per 8.16. ACCEPT: tests that force an API 500, offline mode and a sleeping server.
- **P1-T11 Briefing and Report screens** per 8.3 and 8.8 for every existing experiment, with a print stylesheet. ACCEPT: screenshots; print-to-PDF check.
- **P1-T12 Source chips, provenance popover, Reality Check and Model Card pages** per 8.10, 14.1 and 14.7. ACCEPT: popover works by keyboard; board shows N/A while rows are unverified.

### P2 Spec platform

- **P2-T1 Spec schema, loader, validator and CLI** per section 10, run in CI. ACCEPT: tests for every rejection rule in section 10; CLI output on valid and invalid examples.
- **P2-T2 Titration Bench as a spec.** Build golden-equivalence tests first; the old path stays untouched. Switch routes behind a SPEC\_RUNTIME flag only after equivalence passes, and keep the old path as a fallback for one release. ACCEPT: identical outcomes, scores and violations across at least 20 scripted sequences. If any differ, report the exact differences and stop.
- **P2-T3 Migrate PK Ward, Dose Response Lab and Launch and Orbit Bench** one at a time, each with its own golden tests. ACCEPT: same as P2-T2 per experiment.
- **P2-T4 Spec-driven mentor hints and Ask Orbis actions and synonyms.** ACCEPT: every rule id has a hint; corpora regenerated from spec synonyms still pass.
- **P2-T5 docs/experiment\_spec.md** with a worked example a teacher can follow, plus fixtures. ACCEPT: a new example experiment built from the doc alone validates and runs.
- **P2-T6 Authoring form (SHOULD)** per 8.14 with an approval flag. ACCEPT: field-level errors, dry run, exported spec validates.

### P3 Chemistry expansion

- **P3-T1 chem.kinetics** (new files only): orders 0, 1, 2, half-life, Arrhenius k(T), consecutive A to B to C, analytic solutions with an RK4 cross-check. ACCEPT: at least 40 analytic tests with hand-computed values in comments; mass-balance and limiting-case tests.
- **P3-T2 chem.buffer** (new files only): exact charge-balance buffer pH, capacity, acid or base additions. ACCEPT: at least 40 tests including limiting cases and agreement with the existing equilibrium approach.
- **P3-T3 Titration live curve** with indicator band, from backend points through an ADDED field. ACCEPT: DOM chart summary equals the API outcome in QA.
- **P3-T4 Kinetics Bench spec and UI** with linearised plots, seeded noise, estimate submission and scoring. ACCEPT: three QA runs (success, rule violation, failure).
- **P3-T5 Buffer Bench spec and UI** per 9.2. ACCEPT: same.
- **P3-T6 Chemistry validation rows** only where a citation can be given under G5; own tolerance file and frozen hash; worksheet updated. ACCEPT: rows unverified, retrieved\_on blank, hash test passes.
- **P3-T7 Corpora** of 40 normal plus 15 hard phrases per new experiment; first-run rate recorded before fixes; held-out rate reported. ACCEPT: numbers in the report; at most 8 fixes per corpus.
- **P3-T8 Docs and model cards** (docs/chem\_models.md and two new cards). ACCEPT: every equation and simplification listed with its first-order error.

### P4 Pharma completion

- **P4-T1 Virtual Trial v2** in a new module on the pkpd engine per 9.1 (the old pharma.trial stays untouched). ACCEPT: a cohort of one equals the single-patient engine result; seeded reruns are identical; a 1,000-patient run time is recorded.
- **P4-T2 Trial UI.** Crowd gallery, distribution charts, code-written insight sentence, CSV export, the 'virtual population, not a clinical trial' label. ACCEPT: DOM values equal API values.
- **P4-T3 Drug library freeze.** 10 to 15 drugs, provenance on every parameter, 'what this teaches' lines, and the validator rule that rejects missing provenance. ACCEPT: validator tests; no dosing advice text anywhere.
- **P4-T4 Dose Lab polish.** Sampling schedule UI, regimen overlay, covariate sliders with live backend re-runs, renal check D4, consequences. ACCEPT: three QA runs including a renal-impairment run and an over-limit warning.
- **P4-T5 Calibration (SHOULD).** CSV upload with limits, fit, hold-out report, the honest label. ACCEPT: synthetic parameter-recovery and a misspecified-model test showing worse test error.
- **P4-T6 Dosing-advice red team.** At least 20 cases across Ask Orbis and Dr. Orbis, all refused with an educational explanation. ACCEPT: test output.
- **P4-T7 Docs and cards.** docs/pkpd\_models.md and updated cards. ACCEPT: equations, simplifications and caveats listed.

### P5 Space completion

- **P5-T1 Mission scenarios (SHOULD).** Five specs with par scores and a three-step hint ladder. ACCEPT: each runs through the spec runtime and scores deterministically.
- **P5-T2 Launch Bench polish.** Parameter sliders within bounds, delta-v budget bar, orbit view controls, a 'why it failed' panel written from engine values. ACCEPT: QA proves each failure outcome shows the matching panel.
- **P5-T3 Reference-row recheck.** Every space row's stated conditions agree with its value; the engine radius and its effect are stated in the notes. ACCEPT: a recomputation table in the report.
- **P5-T4 Performance pass** with particle budgets per quality tier and a phone test. ACCEPT: budgets in config; the scene works on Low.
- **P5-T5 QA and corpora** as in P3-T7.

### P6 Classroom and accounts

- **P6-T1 Data model and migrations** for classes, memberships, assignments and submissions, with indexes. ACCEPT: migration tests.
- **P6-T2 Student join** by code and nickname, with a nickname filter. ACCEPT: tests including invalid and expired codes.
- **P6-T3 Teacher accounts** created by an admin script with expiring tokens (magic link is SHOULD). ACCEPT: tests for expiry and reuse.
- **P6-T4 Teacher dashboard** per 8.11 with analytics, CSV export and class deletion. ACCEPT: deletion removes every linked record (tested).
- **P6-T5 Assignments** with parameter presets, due date, graded flag and class leaderboard. ACCEPT: an end-to-end teacher and student run.
- **P6-T6 Privacy.** docs/PRIVACY.md, in-app privacy and terms pages, retention job, deletion procedure, and a test that the stored fields match the data inventory in 13.3. ACCEPT: tests plus the pages.
- **P6-T7 Authorisation tests** generated from the permission table in 13.2 for every route, plus rate-limit and token-expiry tests. ACCEPT: zero unauthorised access in the matrix.
- **P6-T8 Teacher guide** (docs/TEACHER\_GUIDE.md) and a role-based QA playthrough.

### P7 AI hardening

- **P7-T1 Provider interface, kill switch and caps** tested with a fake provider. ACCEPT: AI\_ENABLED off means every feature still works through fallbacks.
- **P7-T2 Context builders from specs and injection tests** (at least 30 injection cases). ACCEPT: none changes instructions or leaks other sessions' data.
- **P7-T3 Voice input (SHOULD)** with feature detection and typed fallback. ACCEPT: tests for unsupported browsers.
- **P7-T4 Evaluation harness** scripts/eval\_ai.py writing docs/AI\_EVAL\_LATEST.md with the author, hard, red-team and held-out results, first run and after fixes. ACCEPT: the report shows all four, with the held-out one labelled founder-written, not tuned.
- **P7-T5 Fallback quality.** Every rule id has a rule-based hint that uses engine values. ACCEPT: a test iterating over all rule ids.
- **P7-T6 Cost accounting.** Token counts, an admin view and alert thresholds. ACCEPT: tests with a fake provider.

### P8 Evidence and trust

- **P8-T1 apply\_verification.py and verification\_log.csv.** ACCEPT: bad formats rejected, tolerances never touched, the log is append-only (tests).
- **P8-T2 Expert review page (SHOULD)** per 8.15. ACCEPT: it never writes data; the submission file validates with the apply script.
- **P8-T3 Reality Check final.** N/A rule while unverified, links to cards. ACCEPT: tests with unverified and verified fixtures.
- **P8-T4 Model Cards final** for all seven engines. ACCEPT: every field from 14.4 filled.
- **P8-T5 Claims gate final** and PITCH\_FACTS with human-check dates left blank. ACCEPT: the gate passes; the blanks are listed as founder tasks.
- **P8-T6 Evidence pack script** that assembles model cards, validation status, known issues, test results and the QA summary into one folder. ACCEPT: the script runs and the output contains no invented numbers.

### P9 Quality hardening

- **P9-T1 Performance budgets.** Measurement scripts and a founder checklist for hardware runs. If the environment has no GPU, mark frame-rate results 'not measured' rather than guess. ACCEPT: transfer sizes measured; API latencies measured.
- **P9-T2 Accessibility audit.** Full axe run, keyboard and screen-reader notes, contrast report, text-size check; fix findings. ACCEPT: no serious or critical issues remain.
- **P9-T3 Security.** docs/SECURITY.md with the ASVS Level 1 checklist, pip-audit output, header tests, authorisation matrix. ACCEPT: every checklist line has evidence or an open issue.
- **P9-T4 Load test** of 200 simulated concurrent sessions at API level with honest results. ACCEPT: report with p50, p95, errors.
- **P9-T5 Resilience.** In production mode a database outage shows a maintenance page; retries with backoff; session resume. ACCEPT: tests that kill the database connection.
- **P9-T6 Browser matrix.** Playwright on Chromium, Firefox and WebKit where available and a manual phone checklist. ACCEPT: matrix recorded with real results.
- **P9-T7 Backup and restore** scripts and a rehearsed runbook. ACCEPT: restore into a scratch database proven by output.
- **P9-T8 Memory-leak test** across three consecutive sessions. ACCEPT: recorded heap values, labelled with the environment.

### P10 Pilot kit and release candidate

- **P10-T1 User-test kit** in docs/user\_test/: script, consent text, SUS form, rule-comprehension quiz, results spreadsheet template.
- **P10-T2 Demo materials.** The 3-minute and 90-second demo scripts, backup-video checklist and final JUDGE\_QA.
- **P10-T3 Help.** FAQ, in-app help centre, teacher quick start.
- **P10-T4 Release candidate 1.0.0-rc.1.** Changelog, full self-audit, evidence pack, and a founder release checklist (tag, push, deploy, smoke, rollback). The agent does not tag or push.
- **P10-T5 Final recheck.** docs/FINAL\_RECHECK.md with PASS, PARTIAL or FAIL for every section of this document, with evidence.

## 19. MVP definition of done

The MVP is done only when all of these are true and evidenced:

1. The three districts and nine experiments in section 4 run end to end on desktop and phone.
2. Every experiment has a briefing, enforced rules with plain reasons, scoring, a report and a Model Card.
3. Teachers can create a class, assign an experiment, see results and export them; students join with a code and a nickname.
4. Ask Orbis and Dr. Orbis work with AI on and with AI off, pass the red-team set, and the held-out rate is reported honestly.
5. Reality Check shows N/A for every unverified row, and the verification workflow works end to end on at least one real expert sign-off.
6. The self-audit passes on the release-candidate HEAD, CI is green, and the QA proof folder is real and unique.
7. Accessibility, security and load reports exist with honest results and open issues listed.
8. Privacy note, terms, disclaimers and the evidence pack exist, and no unsourced statistic appears anywhere.
9. A staging deploy has passed scripts/smoke\_live.py and a rollback has been rehearsed.
10. At least 10 real users, and ideally 30, have completed the user test.

## 20. Human-dependent items (report only, never attempt)

Some work needs a human: expert verification of reference rows, legal and privacy sign-off, company, hosting and AI accounts, secrets and spend, pushing, tagging and deploying, real user testing, and the held-out phrase file. Do not attempt, simulate or fake any of these. Prepare everything the human will need (worksheets, scripts, checklists, templates), list each pending item under 'Human-dependent items' in the phase report, and continue with the remaining tasks. A gate item that depends on a human is reported as BLOCKED-HUMAN, not FAIL, and does not stop work on unrelated tasks or the next phase unless that task's own ACCEPT line says so. Never mark a human-dependent item as done.

## Appendix A. Phase report template (docs/PHASE\_N\_REPORT.md)

1. Blockers (empty if none). 2. Task table: ID, status (done, partial, blocked), commit hash, ACCEPT evidence pasted. 3. Fresh-venv bare pytest final line. 4. QA table and md5 check output. 5. First-run parser rates per corpus before fixes, and the held-out rate. 6. Claims gate output. 7. Protected-file diff output. 8. Open issues. 9. Founder must do. 10. Honesty statement: what was not verified and why. 11. HEAD hash the self-audit ran on.

## Appendix B. Recheck table template (docs/RECHECK\_P(N).md)

Columns: task ID, acceptance criterion, command run, real output (trimmed), status (PASS, PARTIAL, FAIL), fix commit if any.

## Appendix C. Kickoff message for the agent

Paste this with the document attached: Read the attached Simly Orbis MVP Build Specification completely. Start with P0 and follow section 1 exactly. Do not push or tag. Obey G1 to G12. Stop at the first failed gate and report. At the end give: git log of new commits, git status, the full self-audit output, the task table, the newest QA folder path, first-run parser rates, and anything not done with the reason.
