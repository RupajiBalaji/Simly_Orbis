# Simly Orbis

> **A 3D science laboratory simulation where you play the scientist, not the spectator.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-simly--orbis.onrender.com-brightgreen.svg?style=for-the-badge&logo=render)](https://simly-orbis.onrender.com/)
[![CI](https://github.com/RupajiBalaji/Simly_Orbis/actions/workflows/ci.yml/badge.svg)](https://github.com/RupajiBalaji/Simly_Orbis/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-777%2B%20passed-success.svg)](https://github.com/RupajiBalaji/Simly_Orbis)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-0.8.0--dev-orange.svg)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**[🎮 Launch Live Simulation in Browser](https://simly-orbis.onrender.com/)** &nbsp;|&nbsp; **[📖 System Architecture](docs/ARCHITECTURE.md)** &nbsp;|&nbsp; **[🧪 Scientific Model Cards](#-scientific-simulation-engines--model-cards)** &nbsp;|&nbsp; **[🚀 Quickstart](#-quickstart)**

---

## 🌟 What is Simly Orbis?

**Simly Orbis** is an interactive, browser-based 3D laboratory game where laboratory actions carry **real physical, biochemical, and safety consequences**. 

Unlike conventional educational games that replay pre-baked canned animations or rely on unpredictable LLM hallucinations, Simly Orbis couples a procedural **60 FPS Three.js virtual lab** directly to **deterministic, textbook mathematical and physical engines**:

* 💊 **Real Pharmacokinetics & Pharmacodynamics:** Bateman oral absorption, 2-compartment IV kinetics, Hill $E_{\max}$ drug efficacy, and Cockcroft-Gault renal clearance adjustments.
* 🧪 **Aqueous Physical Chemistry:** Exact electroneutrality charge-balance equilibrium solvers, continuous indicator pH transitions, Arrhenius reaction kinetics, and Henderson-Hasselbalch buffer capacities.
* 🚀 **Orbital Mechanics & Astrodynamics:** Multi-stage Tsiolkovsky $\Delta v$, Keplerian orbital periods, Hohmann transfer orbits to GEO, and Runge-Kutta 4th-order (RK4) numerical state propagation.
* 👥 **Virtual Clinical Population Trials:** Vectorized Monte Carlo engine simulating up to 1,000 diverse patients in under 20 milliseconds, visualized as a live 3D instanced crowd wave.
* 🤖 **Dr. Orbis AI Lab Mentor:** Ephemeral pedagogical advisor powered by Google Gemini with strict prompt-injection defenses and an instant deterministic rule-based fallback.
* ⚡ **Zero 3D Asset Downloads:** Procedurally constructed 3D models and geometry load instantly, running smoothly at 60 FPS even on integrated graphics laptops with zero gigabyte asset downloads.

> 🌐 **Try it Live**: **[https://simly-orbis.onrender.com/](https://simly-orbis.onrender.com/)**  
> *(Hosted on Render. If the service is sleeping on the free tier, our built-in wake-up overlay automatically guides you through the ~45s cold start).*

---

## 🧪 Laboratory Districts & Active Experiments

Simly Orbis features 6 fully interactive laboratory benches across Pharmacology, Chemistry, and Spaceflight, plus a large-scale Clinical Trial arena:

```
                                  ┌─────────────────────────────┐
                                  │      SIMLY ORBIS LABS       │
                                  └──────────────┬──────────────┘
                ┌────────────────────────────────┼────────────────────────────────┐
                ▼                                ▼                                ▼
     PHARMACOLOGY DISTRICT               CHEMISTRY BENCHES                 SPACE DISTRICT
  ┌─────────────────────────┐       ┌─────────────────────────┐       ┌─────────────────────────┐
  │ • Pharmacokinetics Ward │       │ • Acid-Base Titration   │       │ • Launch & Orbit Bench  │
  │ • Dose Response Lab     │       │ • Reaction Kinetics     │       │   (Tsiolkovsky, Hohmann,│
  │ • Virtual Trial Arena   │       │ • Buffer Equilibrium    │       │    RK4 Orbital Propag.) │
  └─────────────────────────┘       └─────────────────────────┘       └─────────────────────────┘
```

### 1. 💊 Pharmacokinetics Ward (`pk_ward`)
* **Physical Workflow:** Students weigh dry drug compound on an analytical balance with tare stabilization, dissolve solute in calibrated solvent, administer an oral dose to a simulated patient, draw timed blood samples, centrifuge plasma, and read concentration via spectrophotometer.
* **Governing Math:** One-compartment open oral absorption model with Bateman function:
  $$C(t) = \frac{\text{Dose} \cdot k_a}{V_d \cdot (k_a - k_e)} \left(e^{-k_e t} - e^{-k_a t}\right)$$
* **Lab Hazards:** Dosing before dissolution, improper tare, missed blood-draw windows, or miscalculating clearance.

### 2. 🧪 Acid-Base Titration Bench (`titration_bench`)
* **Physical Workflow:** Prepare volumetric analyte, prime and zero the burette, dispense strong base into acid drop-by-drop, observe dynamic meniscus drainage and color shifts, and calculate exact unknown acid concentration.
* **Governing Math:** Exact aqueous electroneutrality charge-balance equation with auto-ionization of water ($K_w = 1.0 \times 10^{-14}$):
  $$[\text{H}^+] - \frac{K_w}{[\text{H}^+]} + \frac{C_b V_b}{V_a + V_b} - \frac{C_a V_a}{V_a + V_b} \cdot \frac{K_a}{[\text{H}^+] + K_a} = 0$$
* **Visual Realism:** Continuous color interpolation across the indicator's transition range (phenolphthalein colorless $\to$ vibrant magenta; methyl orange red $\to$ yellow).

### 3. 🚀 Launch & Orbital Mechanics Bench (`launch_bench`)
* **Physical Workflow:** Configure rocket staging, fuel fractions, and engine ISP; launch into suborbital ascent; circularize into Low Earth Orbit (LEO); and calculate Hohmann transfer $\Delta v$ burns to Geostationary Orbit (GEO).
* **Governing Math:** Multi-stage Tsiolkovsky rocket equation, vis-viva equation, Keplerian orbital period, and energy-conserving RK4 state propagation ($< 10^{-6}$ energy drift):
  $$\Delta v = I_{\text{sp}} g_0 \ln\left(\frac{m_0}{m_f}\right), \quad v^2 = \mu \left(\frac{2}{r} - \frac{1}{a}\right)$$

### 4. 💉 Dose Response & PK/PD Lab (`dose_lab`)
* **Physical Workflow:** Explore multi-compartment pharmacokinetics across oral, IV bolus, and continuous IV infusion routes. Tailor regimens to adult patients with varying body weight and renal function.
* **Governing Math:** Two-compartment disposition kinetics coupled to the Hill sigmoidal $E_{\max}$ pharmacodynamic response:
  $$E = E_0 + \frac{E_{\max} \cdot C^\gamma}{EC_{50}^\gamma + C^\gamma}$$
* **Covariate Allometry:** Real-time Cockcroft-Gault creatinine clearance (CrCl) calculation and allometric volume/clearance scaling for adults aged 18–90.

### 5. ⚗️ Reaction Kinetics Bench (`kinetics_bench`)
* **Physical Workflow:** Measure chemical reaction rates at varying reactant concentrations and temperatures. Determine reaction orders (zero, first, or second-order) and plot Arrhenius temperature dependence.
* **Governing Math:** Differential rate laws integrated via RK4 and the Arrhenius equation:
  $$k = A \exp\left(-\frac{E_a}{R T}\right), \quad \frac{d[A]}{dt} = -k [A]^n$$

### 6. 🧴 Buffer Equilibrium Bench (`buffer_bench`)
* **Physical Workflow:** Formulate biological and chemical buffers (acetate, phosphate, TRIS, and bicarbonate). Stress buffers by titrating strong acid or base, observing pH stabilization within the buffer capacity window.
* **Governing Math:** Henderson-Hasselbalch relation and Van Slyke buffer capacity ($\beta$):
  $$\beta = 2.303 \left( \frac{K_w}{[\text{H}^+]} + [\text{H}^+] + \frac{C_{\text{buf}} K_a [\text{H}^+]}{(K_a + [\text{H}^+])^2} \right)$$

### 7. 👥 Virtual Population Clinical Trial v2 (`pharma.trial`)
* **Scale:** Simulates 100 to 1,000 virtual human patients in $< 20\text{ ms}$ using vectorized NumPy Monte Carlo sampling.
* **Variability:** Log-normal inter-individual variability in clearance, volume of distribution, and absorption rate, with special impairment sub-cohorts (e.g., hepatic or renal impairment).
* **Visualization:** Instanced 3D stadium crowd where each avatar lights up dynamically based on therapeutic status: 🟢 In Therapeutic Window, 🟡 Subtherapeutic (Ineffective), 🔴 Toxic Concentration.

---

## 🎮 How to Play & Controls

| Input | Action | Description |
|---|---|---|
| <kbd>W</kbd> <kbd>A</kbd> <kbd>S</kbd> <kbd>D</kbd> | Move Character | Smooth walking locomotion through the 3D lab environment |
| <kbd>Shift</kbd> | Sprint | Accelerate to 4.0 m/s for rapid transit across districts |
| <kbd>E</kbd> | Interact / Radial Menu | Open contextual action wheel when standing near lab equipment |
| <kbd>V</kbd> | First-Person View | Switch camera to hands/apparatus inspection view |
| <kbd>Mouse Drag</kbd> | Orbit Camera | Freely pan and inspect experiments from any angle |
| <kbd>Touch Joystick</kbd> | Mobile Movement | Virtual on-screen joystick for mobile and tablet browsers |

---

## 🚀 Quickstart

### Option A: Open the Live Web App (Fastest)
Simply visit **[https://simly-orbis.onrender.com/](https://simly-orbis.onrender.com/)** in any modern web browser (Chrome, Edge, Firefox, Safari).

### Option B: Run via Docker (Recommended for Local Dev)
```bash
# 1. Clone the repository
git clone https://github.com/RupajiBalaji/Simly_Orbis.git
cd Simly_Orbis

# 2. Build the production Docker image
docker build -t simly-orbis .

# 3. Run the container
docker run -p 8000:8000 simly-orbis
```
Open **`http://localhost:8000`** in your browser.

### Option C: Run with Python Locally
```bash
# 1. Clone & enter repository
git clone https://github.com/RupajiBalaji/Simly_Orbis.git
cd Simly_Orbis

# 2. Create and activate a Python 3.12+ virtual environment
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Launch the application
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend
```
Open **`http://localhost:8000`**.

---

## 🏗️ System Architecture

Simly Orbis is engineered for deterministic reproducibility, security, and low-latency interactive execution:

```
                     ┌──────────────────────────────────────────────┐
                     │          Browser Client (Three.js)           │
                     │  • Procedural 3D Geometry (No downloads)    │
                     │  • WebAudio Synthesized Sound Generator      │
                     │  • Radial Proximity Action Wheel & HUD       │
                     └──────────────────────┬───────────────────────┘
                                            │ HTTP / JSON REST
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │            FastAPI Backend Engine            │
                     │  • Security Headers (CSP, Frame-Ancestors)   │
                     │  • In-Memory Token Bucket Rate Limiter       │
                     │  • 20 KB Payload Size Limit Enforcement      │
                     └──────┬──────────────────┬─────────────────┬──┘
                            │                  │                 │
             ┌──────────────┴────────┐         │       ┌─────────┴──────────────┐
             ▼                       ▼         │       ▼                        ▼
     ┌───────────────┐       ┌───────────────┐ │ ┌───────────────┐      ┌───────────────┐
     │  Pharma Math  │       │   Chem Math   │ │ │  Space Flight │      │   AI Mentor   │
     │ • pharma.pk   │       │ • chem.titr   │ │ │ • space.orbit │      │ • Gemini API  │
     │ • pharma.pkpd │       │ • kinetics    │ │ │ • Tsiolkovsky │      │ • Rules Engine│
     │ • pharma.trial│       │ • buffer      │ │ │ • RK4 Orbit   │      │   Fallback    │
     └───────────────┘       └───────────────┘ │ └───────────────┘      └───────────────┘
                                               ▼
                                    ┌──────────────────────┐
                                    │    Stateful Labs     │
                                    │ • Lab Safety Rules   │
                                    │ • Session Checklists │
                                    │ • Reality Invariants │
                                    └──────────────────────┘
```

For full sequence diagrams and detailed architectural specs, read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 📡 API Overview

The backend exposes a fully typed REST API with automatic OpenAPI interactive documentation at **`/docs`**:

| Method | Endpoint | Description | Rate Limit |
|---|---|---|---|
| `GET` | `/api/health` | Health status, storage mode, active collections, and git SHA | 120 / min |
| `GET` | `/api/ping` | Ultra-low latency ping endpoint for cold-start wakeups | 120 / min |
| `GET` | `/api/modules` | List registered simulation engines (`pharma.pk`, `chem.titration`, etc.) | 120 / min |
| `GET` | `/api/modules/{id}/model-card` | Get scientific documentation, governing equations, and boundaries | 120 / min |
| `GET` | `/api/modules/{id}/reality-check` | Execute analytical mathematical invariant verification checks | 120 / min |
| `POST` | `/api/run` | Execute parameter-checked simulation runs | 120 / min |
| `GET` | `/api/lab/experiments` | List active laboratory benches | 120 / min |
| `POST` | `/api/lab/sessions` | Create a new stateful laboratory session (`nickname`, `experiment_id`) | 20 / min |
| `GET` | `/api/lab/sessions/{id}` | Fetch live apparatus state, clock, inventory, and checklist | 120 / min |
| `POST` | `/api/lab/sessions/{id}/actions` | Submit physical lab action (`weigh`, `dissolve`, `titrate`, etc.) | 120 / min |
| `POST` | `/api/lab/sessions/{id}/mentor` | Ask Dr. Orbis for contextual guidance or post-experiment debrief | 10 / min |
| `POST` | `/api/lab/sessions/{id}/finish` | Complete session, compute accuracy score, and issue lab debrief | 120 / min |
| `POST` | `/api/trial/run` | Run 100–1,000 patient Monte Carlo population simulation | 120 / min |
| `POST` | `/api/trial/compare` | Compare dosing regimen vs reference standard with statistical p-values | 120 / min |

---

## 🧪 Rigorous Testing & Self-Audit

Simly Orbis enforces continuous quality assurance through automated unit tests, clean-clone tests, and self-auditing scripts:

```bash
# Run unit & integration tests
pytest backend/tests -v
```

```
========================= 777 passed, 2 skipped in 22.11s =========================
```

* **777+ Automated Tests**: Covering mathematical ODE solvers, electroneutrality roots, rocket trajectory invariants, session state machines, rate limiting, and input sanitization.
* **Clean-Clone CI Verification**: Automated test suite verified to clone into an isolated directory, install only core dependencies, and pass 100% without external assets or pre-cached state.
* **Analytical Invariant Reality Checks**: Every physics module provides programmatic `reality_checks()` verifying conservation of mass, energy conservation ($< 10^{-6}$ drift), and analytical limits.
* **10-Gate Self-Audit (`scripts/self_audit.py`)**: Checks git diffs of protected engine cores, ensures no silent deletions of safety rules, tests author corpus parsers, and verifies documentation integrity.

## 📚 Documentation Index

* 🛠️ **[docs/DEPLOY.md](docs/DEPLOY.md)**: 5-click deployment to Render via Blueprint, Docker setup, and troubleshooting.
* 🏗️ **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Comprehensive system architecture, end-to-end data flows, and state machines.
* 🔬 **[docs/pkpd_models.md](docs/pkpd_models.md)** & **[docs/space_physics.md](docs/space_physics.md)**: Scientific reference documentation and equations.
* 🔍 **[docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md)**: Transparent register of known limitations, unverified rows, and technical caveats.
* 🎙️ **[docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md)**: 3-minute presentation script and 60-second walkthrough.
* ⚖️ **[docs/JUDGE_QA.md](docs/JUDGE_QA.md)**: Transparent questions and answers for evaluators and technical reviewers.

---

## ⚖️ Scientific Integrity & Disclaimers

### 1. Educational Simulation Only
Simly Orbis is an educational learning simulation designed to teach physical principles, scientific curiosity, and experimental methodology. **It does not provide medical advice, diagnosis, or clinical guidance.** It must never be used for real-world patient dosing, clinical trial planning, or aerospace flight planning.

### 2. Analytical Reality Checks vs. Clinical Validation
The engine’s internal `reality_checks()` verify **mathematical self-consistency** (such as charge balance, mass conservation, and agreement with textbook analytical identities). They are not clinical in-vivo validations. All reference rows in `validation/data/*.csv` are labeled pending verification pursuant to the G5 data provenance protocol.

### 3. Adult-Only Population Boundaries
All physiological and pharmacokinetic models are strictly constrained to adult demographics (age 18–90, weight 40–150 kg, CrCl 15–150 mL/min). Pediatric dosing calculations are explicitly prohibited by safety rules.

---

## 📄 License & Contributing

Simly Orbis is released under the **[MIT License](LICENSE)**. Contributions, bug reports, and educational extensions are welcome!

* Developed with ❤️ for science students, educators, and curious minds.
* Live deployment: **[https://simly-orbis.onrender.com/](https://simly-orbis.onrender.com/)**
