# Simly Orbis

> **A simulated world for testing before building.**

Simly Orbis is an interactive pharmacokinetics (PK) simulation playground built with **FastAPI** + **MongoDB Atlas (Motor)** on the backend and **vanilla modern JavaScript + Chart.js** on the frontend.

It showcases how complex physiological and biochemical dynamics can be modeled and explored interactively before building physical systems, prescribing treatments, or conducting clinical trials.

---

## 🌟 Features

- **Bateman PK Simulation Engine:** One-compartment oral absorption model with linear superposition for multi-dose regimens, handling clearance impairment, body weight scaling, and edge cases ($k_a = k_e$).
- **5 Progressive Puzzle Levels:** From standard healthy adults to paediatric dosing, impaired hepatic clearance, and night-shift caffeine maintenance.
- **⚡ Demo Mode:** One-click automated optimal run for live demonstrations.
- **🤖 Dr. Orbis AI Tutor:** Physiological explanations and actionable dosing feedback powered by Claude 3.5 (with automatic rule-based fallback).
- **⚙ Under the Hood Drawer:** Live inspects raw API request/response payloads, active database storage mode (MongoDB Atlas or in-memory fallback), document counts, and mathematical formulas.
- **Live Leaderboard:** Top rankings per level with seeded sample players labelled `(sample)`.

---

## 📂 Project Layout

```
simly-orbis/
├── backend/                   Python / FastAPI service
│   ├── app/
│   │   ├── main.py            Entry point – routes, CORS, static mount
│   │   ├── config.py          Pydantic-settings (reads .env)
│   │   ├── db.py              Motor connection with in-memory fallback + seeding
│   │   ├── routes/
│   │   │   ├── drugs.py       GET  /api/drugs
│   │   │   ├── levels.py      GET  /api/levels
│   │   │   ├── simulate.py    POST /api/simulate
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
│   │   └── test_pk_engine.py  PK engine unit tests
│   ├── requirements.txt
│   ├── pytest.ini
│   └── .env.example
│
└── frontend/                  Static web client (no build step required)
    ├── index.html             Single-page application (7 screens + drawer)
    ├── style.css              Dark theme design system & animations
    └── app.js                 State, Chart.js graphs, AI tutor typewriter & drawer
```

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
ANTHROPIC_MODEL=claude-3-5-haiku-20241022
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
   - Watch the sliders smoothly slide into position: **Paracetamol 800 mg × 5 doses every 4 hours**.
   - Point to the live Chart.js plot:
     - Purple line = plasma concentration.
     - Teal shaded region = therapeutic window (green zone).
     - Red dashed line = toxicity ceiling.
   - Explain how steady state is maintained without breaching the toxic threshold ($80\%$ time in green $\rightarrow 3$ stars!).
3. **Dr. Orbis AI Tutor:**
   - Point to the **Dr. Orbis** panel below the chart:
     - Highlight the real-time typewriter effect.
     - Note Dr. Orbis explaining absorption kinetics and offering physiological tips.

### **Minute 2: The "Under the Hood" Drawer (Architecture & Math)**
1. **Open the Drawer:** Click the floating `⚙` button in the bottom-right corner.
2. **Backend Status:**
   - Show the active **Storage mode** (`MongoDB Atlas` or `In-Memory fallback`) and document counts for `players` and `scores`.
3. **The Mathematical Model:**
   - Highlight the **Bateman equation** rendered right inside the drawer:
     $$C(t) = \frac{F \cdot D \cdot k_a}{V_d \cdot (k_a - k_e)} \cdot (e^{-k_et} - e^{-k_at})$$
   - Explain how oral bioavailability ($F$), absorption rate ($k_a$), clearance multiplier ($k_e$), and volume of distribution ($V_d$) drive the simulation.
4. **Live API Inspector:**
   - Point to **Last API Request** and **Last API Response** JSON blocks.
   - *"Every change communicates with our clean FastAPI backend, capturing the request and response in real time."*

### **Minute 3: Leaderboard, Progression & Database**
1. **Result Screen & Submitting Score:**
   - Click **✓ Submit Score** to view the score celebration with animated stars.
2. **Leaderboard:**
   - Navigate to **Leaderboard** in the top navigation.
   - Select Level 1 to show the seeded sample players (`(sample)`) alongside your newly achieved score.
   - Highlight that user scores persist in MongoDB Atlas (or in-memory store).
3. **About Screen:**
   - Click **About** to summarize the grand vision: expanding Simly Orbis from pharmacokinetics into multi-compartment disease modeling, surgical testing, and engineering simulations.

---

## ⚠️ Disclaimer

Parameters are approximate, game-balanced, and **strictly for educational and illustrative use**.
Not for clinical, diagnostic, or prescription use.
