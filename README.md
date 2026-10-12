# Simly Orbis

> **A science learning game where you play the scientist, not the spectator.**

[![CI](https://github.com/RupajiBalaji/Simly_Orbis/actions/workflows/ci.yml/badge.svg)](https://github.com/RupajiBalaji/Simly_Orbis/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-91%20passed-success.svg)](https://github.com/RupajiBalaji/Simly_Orbis)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Simly Orbis is an interactive 3D science laboratory simulation platform where actions carry physical consequences before students or researchers touch physical equipment or real patients. Built with a high-performance **FastAPI** backend executing exact deterministic equations (Bateman pharmacokinetics and charge-balance equilibrium acid-base solver) and a procedural **Three.js** frontend achieving 60 FPS on our test laptop (AMD Ryzen, integrated graphics) with zero external 3D model asset downloads (free demo server may take up to a minute to wake up). Features **Dr. Orbis**, an embedded pedagogical AI mentor powered by Google Gemini with strict prompt-injection defenses and deterministic rule-based fallback, plus a large-scale **Virtual Clinical Trial** engine simulating up to 1,000 patients in under 20 ms.

---

## 🚀 Quickstart & Demo

### Live Deployment
- **Live Demo:** [https://simly-orbis.onrender.com](https://simly-orbis.onrender.com) *(Hosted on Render Free Tier. Built-in wake-up overlay handles free tier cold starts)*
- **Deployment Guide:** See [docs/DEPLOY.md](docs/DEPLOY.md) for 5-click deployment via `render.yaml` Blueprint.

### Run with Docker
```bash
# Build production container image
docker build -t simly-orbis:latest .

# Run container locally on port 8000
docker run -p 8000:8000 simly-orbis:latest
```
Open `http://localhost:8000` in your web browser.

### Run with Python Locally
```bash
# Clone the repository
git clone https://github.com/RupajiBalaji/Simly_Orbis.git
cd Simly_Orbis

# Install pinned dependencies
pip install -r backend/requirements.txt

# Start FastAPI server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend
```
Visit `http://localhost:8000`.

---

## 📡 API Endpoints & Rate Limits

Simly Orbis includes built-in in-memory token-bucket rate limiting, 20 KB payload size protection, and security headers (CSP, `X-Content-Type-Options: nosniff`, `frame-ancestors 'none'`).

| Method | Endpoint | Description | Rate Limit |
|---|---|---|---|
| `GET` | `/api/health` | Service health status, storage mode, collections, and git SHA | 120 req / min |
| `GET` | `/api/ping` | Low-latency ping endpoint for wake-up polling (`{"ping": "pong"}`) | 120 req / min |
| `GET` | `/api/modules` | List registered simulation engines (`pharma.pk`, `chem.titration`, `pharma.trial`) | 120 req / min |
| `GET` | `/api/modules/{id}/reality-check` | Execute analytical invariant verification checks (checked against textbook equations and internal consistency; not clinical validation) | 120 req / min |
| `GET` | `/api/modules/{id}/model-card` | Retrieve scientific model card (assumptions, equations, boundaries) | 120 req / min |
| `POST` | `/api/run` | Execute any registered simulation module with parameter validation | 120 req / min |
| `GET` | `/api/lab/experiments` | List interactive laboratory experiments (`pk_ward`, `titration_bench`) | 120 req / min |
| `POST` | `/api/lab/sessions` | Create a new stateful laboratory session (`nickname`, `experiment_id`) | 20 req / min |
| `GET` | `/api/lab/sessions/{id}` | Retrieve current session state, clock, apparatus, and checklist | 120 req / min |
| `POST` | `/api/lab/sessions/{id}/actions` | Apply laboratory action (`weigh`, `dissolve`, `titrate`, etc.) | 120 req / min |
| `POST` | `/api/lab/sessions/{id}/mentor` | Consult Dr. Orbis AI mentor (`hint`, `explain`, `ask`, `debrief`) | 10 req / min |
| `POST` | `/api/lab/sessions/{id}/finish` | Complete experiment, score student performance, and issue report | 120 req / min |
| `POST` | `/api/trial/run` | Vectorized population clinical trial simulation (up to 1,000 patients) | 120 req / min |
| `POST` | `/api/trial/compare` | Compare tested dosing regimen against reference standard | 120 req / min |

---

## 🔬 Scientific Simulation Engines & Model Cards

Simulations in Simly Orbis are **deterministic and reproducible**. Outcomes are governed by physical equations, never hallucinated by an LLM.

```
Analytical Reality Checks: 11 / 11 Passed [PASS]
```

1. **`pharma.pk` (Pharmacokinetics)**:
   - **Equation**: One-compartment oral absorption Bateman function:
     $$C(t) = \frac{\text{Dose} \cdot k_a}{V_d \cdot (k_a - k_e)} \cdot \left(e^{-k_e t} - e^{-k_a t}\right)$$
     with linear superposition across multi-dose intervals.
   - **Reality Checks**: Single-dose $C_{max}$ analytical peak formula equivalence, steady-state clearance rate match, mass balance conservation.
2. **`chem.titration` (Volumetric Acid-Base Titration)**:
   - **Equation**: Exact aqueous charge-balance equilibrium solver with water auto-ionization ($K_w = 1.0 \times 10^{-14}$) and Henderson-Hasselbalch buffer calculations; phenolphthalein indicator spectral transition centered at $pK_{ind} = 9.3$.
   - **Reality Checks**: Neutral water pH at $V_b=0$, equivalence point stoichiometric pH, strong acid asymptotic limit, buffer half-equivalence $pH = pK_a$.
3. **`pharma.trial` (Virtual Clinical Trial)**:
   - **Engine**: Vectorized NumPy Monte Carlo engine with log-normal demographic distributions (body weight CV 18%, clearance CV 30%, $k_a$ CV 25%) and hepatic impairment subgroup (0.6x clearance).
   - **Reality Checks**: Zero-variance deterministic equivalence, median peak within 10% of individual baseline, RNG seed reproducibility, dose monotonicity.

---

## 🌟 Key Features & Visual Proofs

| Feature | Description | Proof Link |
|---|---|---|
| **Action Camera & Collisions** | Smooth camera easing framing upper body, hands, and active apparatus (~2m) with bench and wall collision safety. | [Action Cam Showcase](docs/screenshots/action_camera_showcase.gif) |
| **Realistic Weighing & Balance** | Spatula & dosing cup props; growing powder pile on balance pan with live LCD display rising to target weight. | [Weigh Proof](docs/screenshots/proof_action_weigh_100.png) |
| **Burette Drips & Endpoint Color** | Dynamic meniscus drainage, liquid droplets, and Henderson-Hasselbalch phenolphthalein color transition. | [Titration Proof](docs/screenshots/proof_step0_titration_drips_color.png) |
| **500-Patient Crowd Wave** | 3D instanced crowd arena displaying real-time color waves (green: in range, amber: subtherapeutic, red: toxic). | [Trial Crowd Wave](docs/screenshots/proof_step0_trial_after.png) |
| **Dr. Orbis AI Lab Mentor** | Contextual Google Gemini guidance with strict prompt-injection defense, latency tracking, and deterministic rule-based fallback. | [Mentor Inquiry](docs/screenshots/proof_mentor_ask.png) |
| **Synthesized WebAudio Engine** | Procedural WebAudio sound effects: balance tare beeps, pour bursts, error alarms, and success chimes. | [Audio Controls](docs/screenshots/proof_rc1_2_1_sound_controls.png) |
| **Production Hardening** | In-game About modal, rate limiting, and server wake-up flow with health metadata. | [Hardening Proof](docs/screenshots/proof_rc1_3_hardening_about.png) |
| **Port 10000 Deployment Run** | Verified deployment running smoothly on Render standard port 10000. | [Port 10000 Proof](docs/screenshots/proof_rc1_4_deploy_port10000.png) |

---

## 🏗️ System Architecture

```
Browser Client (Three.js 60 FPS, WebAudio Synth, Action Camera, Director)
       │
       ▼ REST / JSON (HTTP 1.1)
FastAPI Backend (Security Middleware, Token Bucket Rate Limiter, 20 KB Body Limit)
       ├── Core Registry (pharma.pk, chem.titration, pharma.trial)
       ├── Lab Engine (Stateful Sessions, Safety Rules R1-R10, Scoring)
       ├── AI Mentor (Google Gemini API + Deterministic Fallback)
       └── Database (MongoDB Atlas + In-Memory Fallback Adapter)
```
*For complete ASCII diagrams and end-to-end data flows, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).*

---

## 🧪 Testing & Quality Assurance

Simly Orbis maintains comprehensive test coverage across simulation equations, safety rules, rate limiting, and API contracts.

```bash
# Run the complete test suite
pytest backend/tests -v
```

```
============================== 91 passed in 4.8s ==============================
```

- **91 / 91 Tests Green** in CI on every push and pull request.
- **Analytical Invariants**: 11 dedicated analytical reality checks (checked against textbook equations and internal consistency; not clinical validation) covering all simulation engines.
- **Safety Rule Matrix**: Full coverage of PPE violations, chemical waste segregation, and acid-water dilution order.
- **Abuse Protection**: Automated test coverage for per-IP rate limits (429), body size limits (413), and daily AI caps.

---

## 📚 Documentation Index

- [docs/DEPLOY.md](docs/DEPLOY.md): 5-click deployment to Render via Blueprint, Docker setup, and troubleshooting.
- [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md): 3-minute hackathon presentation script, 60-second lightning talk, and contingency guide.
- [docs/JUDGE_QA.md](docs/JUDGE_QA.md): 15 honest questions and answers for hackathon judges and technical reviewers.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): Comprehensive system architecture and sequential data flows.
- [docs/ROADMAP.md](docs/ROADMAP.md): Transparent limitations and roadmap for v0.2.

---

## 📄 License & Disclaimer

Simly Orbis is licensed under the [MIT License](LICENSE).

> **Educational Disclaimer**: Simly Orbis is a simulated learning game designed for educational purposes only. It does not provide medical advice, clinical guidance, or diagnostic evidence.
