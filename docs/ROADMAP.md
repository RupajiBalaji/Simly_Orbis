# Product Roadmap – Simly Orbis

An honest technical overview of current capabilities in Release Candidate 1 (RC1) and our development trajectory for v0.2 and beyond.

---

## 1. What is Done Today (v0.3 / v0.4-dev)

- **Four Full 3D Interactive Districts**:
  - `pk_ward`: Pharmacokinetics clinical dosing, analytical balance weighing, oral administration, blood sampling, and therapeutic window monitoring.
  - `titration_bench`: Acid-base neutralization titration with burette control, phenolphthalein indicator inflection, and pH electrode telemetry.
  - `launch_bench`: Orbital Mechanics launch bench with Launch Pad A rocket staging, preflight checklists, liftoff TWR evaluation, Keplerian orbits, and Hohmann GEO transfer.
  - `dose_lab`: Dose Response Lab exploring 1- and 2-compartment PK/PD dynamics, adult patient covariates (weight, age, CrCl), multiple-dose regimens, and comparative regimen overlays.
- **Deep Mathematical PK/PD Engine (`pharma.pkpd`)**:
  - Analytical and RK4 numerical differential equation solvers for 1-comp oral and 2-comp IV infusion/bolus models.
  - Sigmoidal Hill $E_{\max}$ pharmacodynamic response modeling.
  - Covariate allometry and Cockcroft-Gault renal clearance adjustment.
  - Adult-only guardrails (18–90 yr, 40–150 kg, CrCl 15–150 mL/min; no pediatric support).
- **Large-Scale Virtual Clinical Trial**:
  - Vectorized Monte Carlo simulation testing up to 1,000 virtual patients in under 20 ms.
  - Interactive 3D crowd viewing gallery with dynamic color waves and population subgroup analysis (hepatic clearance impairment).
- **Dr. Orbis AI Lab Mentor & Ask Orbis**:
  - Contextual guidance powered by Google Gemini with strict prompt-injection defenses and real-time latency readouts.
  - High-fidelity deterministic rule-based fallback when offline or when daily call caps are reached.
  - Deterministic refusals for personal medical diagnosis and pediatric requests.
- **Reality Check Verification Board**:
  - In-game verification screens comparing simulation outputs against analytical equations (checked against textbook equations and internal consistency; not clinical validation).
- **Audio & Game Feel**:
  - Synthesized WebAudio sound effects (beeps, liquid bursts, alarms, chimes) with volume and mute controls.
  - Action camera collision and framing system with verified 100% free viewport framing.
  - Director Mode for hands-free autonomous protocol demonstrations.
- **Production Hardening**:
  - Token-bucket rate limiting (120 req/min general, 10 req/min AI).
  - Security headers, CSP with `frame-ancestors 'none'`, and 20 KB payload protection.
  - Dockerfile, Render Blueprint (`render.yaml`), and 400+ green automated tests.

---

## 2. What is NOT Done Yet (Explicit Limitations)

- **Paediatric Pharmacokinetics**: Paediatric scaling is out of scope and explicitly rejected. Adult-only ranges strictly enforced.
- **User Authentication & Persistent Profiles**: Scores and sessions are currently keyed by nickname and session ID without OAuth/passwords.
- **Multiplayer Lab Collaborations**: Each session is single-player; collaborative partner benches are not yet implemented.
- **Full Touch Gestures on Small Mobile Screens**: While responsive, complex camera orbiting is optimized for mouse and trackpad devices.
- **Market Microstructure District**: Remains marked "🔒 Coming Soon" in lobby per Spec Section 4.
- **Molecular Biology District (Enzyme Kinetics)**: Curriculum expansion planned for future phases (Michaelis-Menten kinetics, active-site inhibition assays); excluded from MVP lobby scope per Spec Section 4.

---

## 3. The Vision for v0.2

### Quarter 1: Advanced Modeling & New Districts
- **Numerical ODE Solver (RK4)**: Support for two-compartment PK models and non-linear Michaelis-Menten elimination.
- **Molecular Biology Bench**: PCR thermal cycler and agarose gel electrophoresis with UV visualization.
- **Orbital Mechanics District**: Two-body Keplerian orbits, Hohmann transfer trajectory planning, and orbital rendezvous maneuvers.

### Quarter 2: Pedagogical & Classroom Integration
- **Teacher Dashboard & LMS Integration**: Export gradebook reports directly to Canvas and Google Classroom via LTI 1.3.
- **Custom Protocol Builder**: Instructors can author custom lab protocols, specify grading rubrics, and define safety rules via JSON schemas.
- **Peer Review & Shared Virtual Trials**: Students submit clinical trial dosing regimens to shared class-wide leaderboard competitions.
