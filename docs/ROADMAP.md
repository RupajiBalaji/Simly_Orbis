# Product Roadmap – Simly Orbis

An honest technical overview of current capabilities in Release Candidate 1 (RC1) and our development trajectory for v0.2 and beyond.

---

## 1. What is Done Today (v0.1 / RC1)

- **Two Full 3D Interactive Experiments**:
  - `pk_ward`: Pharmacokinetics clinical dosing, analytical balance weighing, oral administration, blood sampling, and therapeutic window monitoring.
  - `titration_bench`: Acid-base neutralization titration with burette control, phenolphthalein indicator inflection, and pH electrode telemetry.
- **Large-Scale Virtual Clinical Trial**:
  - Vectorized Monte Carlo simulation testing up to 1,000 virtual patients in under 20 ms.
  - Interactive 3D crowd viewing gallery with dynamic color waves and population subgroup analysis (hepatic clearance impairment).
- **Dr. Orbis AI Lab Mentor**:
  - Contextual guidance powered by Anthropic Claude 3.5 with strict prompt-injection defenses and real-time latency readouts.
  - High-fidelity deterministic rule-based fallback when offline or when daily call caps are reached.
- **Reality Check Verification Board**:
  - In-game verification screens comparing simulation outputs against analytical textbook equations.
- **Audio & Game Feel**:
  - Synthesized WebAudio sound effects (beeps, liquid bursts, alarms, chimes) with volume and mute controls.
  - Action camera collision and framing system.
  - Director Mode for hands-free autonomous protocol demonstrations.
- **Production Hardening**:
  - Token-bucket rate limiting (120 req/min general, 10 req/min AI).
  - Security headers, CSP with `frame-ancestors 'none'`, and 20 KB payload protection.
  - Dockerfile, Render Blueprint (`render.yaml`), and 90+ green automated tests.

---

## 2. What is NOT Done Yet (Explicit Limitations)

- **Multi-Compartment Pharmacokinetics**: Currently limited to one-compartment oral absorption; two-compartment and IV infusion models are planned for v0.2.
- **User Authentication & Persistent Profiles**: Scores and sessions are currently keyed by nickname and session ID without OAuth/passwords.
- **Multiplayer Lab Collaborations**: Each session is single-player; collaborative partner benches are not yet implemented.
- **Full Touch Gestures on Small Mobile Screens**: While responsive, complex camera orbiting is optimized for mouse and trackpad devices.
- **Additional Science Districts**: Chemistry organic synthesis, PCR thermal cycling, and orbital mechanics remain conceptual placeholders.

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
