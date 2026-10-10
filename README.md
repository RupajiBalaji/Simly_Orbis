# Simly Orbis

> **A simulated world for testing before building.**

Simly Orbis is an interactive simulation platform built with **FastAPI** + **MongoDB Atlas (Motor)** on the backend and **vanilla modern JavaScript + Chart.js** on the frontend.

It turns complex domain dynamics into modular, verifiable simulations. The core engine is designed as a multi-district platform starting with pharmacokinetics (**pharma.pk**), expandable to Chemistry, Space, and Market districts without touching the core.

---

## 🌟 Features

- **Multi-District Simulation Core:** Pluggable `SimModule` architecture with unified parameter schemas, execution tracking, and built-in analytical reality checks.
- **Bateman PK Simulation Engine (`pharma.pk`):** One-compartment oral absorption model with linear superposition for multi-dose regimens, handling clearance impairment, body weight scaling, and edge cases ($k_a = k_e$).
- **5 Progressive Clinical Levels:** From standard healthy adults to paediatric dosing, impaired hepatic clearance, and night-shift caffeine maintenance.
- **⚡ Demo Mode:** One-click automated safe run for Level 1 (500 mg × 4 every 6h = 2 g/day, achieving 3 stars).
- **🤖 Dr. Orbis AI Tutor:** Physiological explanations and actionable dosing feedback powered by Claude (with automatic rule-based fallback).
- **⚙ Under the Hood Drawer:** Live inspects registered modules, run logs, raw API payloads, active database storage mode (MongoDB Atlas or in-memory fallback), document counts, and mathematical equations.
- **Live Leaderboard:** Top rankings per level with seeded sample players labelled `(sample)`.

---

## 🏗️ Architecture

Simly Orbis is organized into a modular simulation platform:

```
simly-orbis/
├── backend/                   Python / FastAPI service
│   ├── app/
│   │   ├── main.py            Entry point – routes, CORS, module registration, static mount
│   │   ├── config.py          Pydantic-settings (reads .env)
│   │   ├── db.py              Motor connection + in-memory fallback, runs & score collections
│   │   ├── core/              Core simulation engine interface
│   │   │   ├── version.py     ENGINE_VERSION ("0.1.0")
│   │   │   ├── base.py        SimModule abstract base, RunResult, RealityCheck
│   │   │   └── registry.py    Global module registry (register, get, list)
│   │   ├── modules/           Registered simulation domain modules
│   │   │   └── pharma_pk.py   Module #1: "pharma.pk" wrapping PK engine + 3 reality checks
│   │   ├── routes/
│   │   │   ├── modules.py     GET /api/modules, GET /api/modules/{id}, GET .../reality-check
│   │   │   ├── runs.py        POST /api/run, GET /api/runs, GET /api/runs/{run_id}
│   │   │   ├── drugs.py       GET /api/drugs
│   │   │   ├── levels.py      GET /api/levels
│   │   │   ├── simulate.py    POST /api/simulate (legacy / game wrapper)
│   │   │   ├── scores.py      POST /api/score · GET /api/leaderboard
│   │   │   └── tutor.py       POST /api/tutor (Dr. Orbis AI feedback)
│   │   └── sim/
│   │       ├── pk_engine.py   One-compartment Bateman PK engine
│   │       ├── models.py      Drug / Patient / SimulationResult dataclasses
│   │       ├── drugs.py       Catalogue loader
│   │       ├── drugs.json     Paracetamol · Ibuprofen · Caffeine
│   │       └── levels.json    Clinical mission scenarios
│   ├── tests/
│   │   ├── conftest.py        Async httpx client fixture
│   │   ├── test_api.py        API integration tests
│   │   ├── test_core_and_runs.py Core registry, schema, runs & reality checks tests
│   │   └── test_pk_engine.py  PK engine unit tests
│   ├── requirements.txt
│   ├── pytest.ini
│   └── .env.example
│
└── frontend/                  Static web client (no build step required)
    ├── index.html             Single-page application (7 screens + Under the Hood drawer)
    ├── style.css              Dark theme design system & animations
    └── app.js                 State, Chart.js graphs, AI tutor typewriter & drawer
```

### Run Log Collection
Every execution via `POST /api/run` (and in-game simulation) stores a persistent record in the `runs` collection:
- `run_id` (UUID4)
- `module_id`, `district`
- `params`, `summary`, `series` (omitted if > 5000 points)
- `warnings`, `nickname`, `parent_run_id`
- `engine_version`, `duration_ms`, `created_at`, `storage_mode`

Compound database indexes are maintained on `created_at desc`, `(module_id, created_at desc)`, and unique `run_id`.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check with storage mode, runs count, and registered module IDs |
| `GET` | `/api/modules` | List all registered simulation modules (`id`, `name`, `district`, `version`) |
| `GET` | `/api/modules/{id}` | Detailed module metadata including parameter JSON schema |
| `GET` | `/api/modules/{id}/reality-check` | Execute analytical verification tests for a module |
| `POST` | `/api/run` | Execute any registered module with params and log execution |
| `GET` | `/api/runs` | Query latest simulation runs (query params: `limit`, `module_id`) |
| `GET` | `/api/runs/{run_id}` | Retrieve details of a specific simulation run |
| `GET` | `/api/drugs` | List available drugs |
| `GET` | `/api/levels` | List gameplay puzzle levels |
| `POST` | `/api/simulate` | Pharmacokinetics simulation endpoint (gameplay) |
| `POST` | `/api/score` | Record player score |
| `GET` | `/api/leaderboard` | Get leaderboard standings |
| `POST` | `/api/tutor` | Request Dr. Orbis explanation (`source`: "ai" or "fallback") |

---

## 🧩 How to Add a New Module in 5 Steps

Adding a new simulation domain (e.g., Chemistry reaction kinetics, Orbital dynamics, Market order book) takes 5 straightforward steps without modifying core abstractions:

1. **Define Parameter Model:**
   Create a Pydantic model inheriting `BaseModel` specifying the input parameters with validation bounds:
   ```python
   from pydantic import BaseModel, Field

   class OrbitParams(BaseModel):
       altitude_km: float = Field(..., ge=100, le=50000)
       eccentricity: float = Field(default=0.0, ge=0.0, lt=1.0)
   ```

2. **Subclass `SimModule`:**
   In `backend/app/modules/<your_module>.py`, inherit from `SimModule`:
   ```python
   from app.core.base import SimModule, RunResult, RealityCheck

   class OrbitModule(SimModule):
       id = "space.orbit"
       name = "Keplerian Orbit Simulator"
       district = "space"  # "pharma" | "chemistry" | "space" | "market"
       description = "Computes two-body orbital trajectories."
       version = "0.1.0"
       params_model = OrbitParams
   ```

3. **Implement `run(params)`:**
   Implement pure computation logic returning a `RunResult`:
   ```python
   def run(self, params: OrbitParams) -> RunResult:
       # compute orbital period, velocity, trajectory points
       return RunResult(
           module_id=self.id,
           params=params.model_dump(),
           summary={"period_minutes": 92.5, "perigee_velocity_km_s": 7.7},
           series={"time_s": [...], "altitude_km": [...]},
           warnings=[],
       )
   ```

4. **Implement `reality_checks()`:**
   Provide analytical checks against known closed-form solutions or physical laws:
   ```python
   def reality_checks(self) -> list[RealityCheck]:
       # Verify Kepler's Third Law T^2 ~ a^3
       return [
           RealityCheck(
               name="Kepler's Third Law",
               description="Checks orbital period against analytical Keplerian law",
               expected=5550.0,
               actual=5551.2,
               tolerance=0.01,
               passed=True,
               source_note="Derived from T = 2*pi*sqrt(a^3/mu)",
           )
       ]
   ```

5. **Register Module at App Startup:**
   In `backend/app/main.py`:
   ```python
   from app.core.registry import register
   from app.modules.space_orbit import OrbitModule

   register(OrbitModule())
   ```
   Your module is now immediately available via `/api/modules`, `/api/modules/space.orbit`, and runnable via `POST /api/run`!

---

## 🚀 Quick Start (Clean Setup)

### 1. Create and Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Python Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Configure Environment (.env)
```bash
# Windows
copy backend\.env.example backend\.env

# macOS / Linux
cp backend/.env.example backend/.env
```

Edit `backend/.env`:
```env
# Optional: MongoDB Atlas URI (leave empty to use built-in in-memory store)
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
DB_NAME=simly_orbis

# Optional: Anthropic API Key (leave empty to use built-in rule-based tutor fallback)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
```

### 4. Run the Application
From the repository root:
```bash
uvicorn app.main:app --reload --app-dir backend
```
Open **<http://localhost:8000>** in your browser.

---

## 🍃 MongoDB Atlas Setup (Optional)

If you wish to connect a live MongoDB Atlas cluster instead of the in-memory fallback:

1. Create a free M0 cluster on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. Under **Database Access**, create a database user with read and write permissions.
3. Under **Network Access**, add `0.0.0.0/0` (allow access from anywhere) or your IP address.
4. Click **Connect** → **Drivers** (Python / Motor) and copy the connection string.
5. Paste into `backend/.env` as `MONGODB_URI`:
   ```env
   MONGODB_URI=mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
6. Restart the app. The app logs `Storage mode: mongodb` and the Under the Hood drawer shows `MongoDB Atlas`.

---

## 🧪 Running Tests

```bash
cd backend
pytest
```
All unit tests and integration tests will run using async httpx and in-memory storage.

---

## 🎬 3-Minute Live Demo Script

Use this script during a walkthrough or investor/academic presentation:

### **Minute 1: The Vision & Gameplay (Level 1)**
1. **Introduction:** Open `<http://localhost:8000>`.
   - *"Simly Orbis is an interactive simulation sandbox where students and engineers test hypotheses safely before building real systems. This first module simulates oral pharmacokinetics."*
2. **Demo Mode or Manual Play:**
   - Click **⚡ Demo Mode (Auto-play)** on the nickname screen.
   - Watch the sliders smoothly slide into position: **Paracetamol 500 mg × 4 doses every 6 hours** (2.0 g/day total, well within safe adult limits).
   - Point to the live Chart.js plot:
     - Purple line = plasma concentration.
     - Teal shaded region = therapeutic window (green zone).
     - Red dashed line = toxicity ceiling.
   - Explain how steady state is maintained without breaching the toxic threshold (80% time in green $\rightarrow$ 3 stars!).
3. **Dr. Orbis AI Tutor:**
   - Point to the **Dr. Orbis** panel below the chart:
     - Highlight the real-time typewriter effect.
     - Note Dr. Orbis explaining absorption kinetics and offering physiological tips.

### **Minute 2: The "Under the Hood" Drawer (Architecture & Math)**
1. **Open the Drawer:** Click the floating `⚙` button in the bottom-right corner.
2. **Backend Status & Registered Modules:**
   - Show the registered module chip (`pharma.pk`) and total runs logged.
   - Show the active **Storage mode** (`MongoDB Atlas` or `In-Memory fallback`) and document counts for `players`, `scores`, and `runs`.
   - Show the **Tutor source** status (`Tutor: AI (Claude)` or `Tutor: rule-based fallback`).
3. **The Mathematical Model:**
   - Highlight the **Bateman equation** rendered right inside the drawer:
     $$C(t) = \frac{F \cdot D \cdot k_a}{V_d \cdot (k_a - k_e)} \cdot (e^{-k_et} - e^{-k_at})$$
   - Explain how oral bioavailability ($F$), absorption rate ($k_a$), clearance multiplier ($k_e$), and volume of distribution ($V_d$) drive the simulation.
4. **Live API Inspector & Run History:**
   - Click **View last 10 runs** to display the recent runs logged in the database.
   - Point to **Last API Request** and **Last API Response** JSON blocks.

### **Minute 3: Leaderboard, Progression & Database**
1. **Result Screen & Submitting Score:**
   - Click **✓ Submit Score** to view the score celebration with animated stars.
2. **Leaderboard:**
   - Navigate to **Leaderboard** in the top navigation.
   - Select Level 1 to show the seeded sample players (`(sample)`) alongside your newly achieved score.
   - Highlight that user scores persist in MongoDB Atlas (or in-memory store).
3. **About Screen:**
   - Click **About** to summarize the grand vision: expanding Simly Orbis from pharmacokinetics into multi-compartment disease modeling, chemistry, orbital mechanics, and market microstructures.

---

## ⚠️ Educational Disclaimer

Parameters are approximate, game-balanced, and **strictly for educational and illustrative use**.
Do not use for clinical, diagnostic, or prescription purposes.
