# System Architecture – Simly Orbis

Simly Orbis is designed with a **deterministic-first, decoupled architecture** separating procedural 3D client rendering from mathematical simulation and AI mentoring microservices.

---

## 1. High-Level Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                               CLIENT BROWSER (SPA)                                |
|                                                                                   |
|  +---------------------------+  +--------------------------+  +----------------+  |
|  |     Procedural Three.js   |  |   DOM HUD & Action Bar   |  | WebAudio Synth |  |
|  |  - Custom Geometry (Ward) |  |  - Step Checklists       |  |  - Beeps &      |  |
|  |  - Dynamic Shader Drips   |  |  - Trial Crowd Gallery   |  |    Pour SFX    |  |
|  |  - Action Camera (Collis) |  |  - Reality Check Panel   |  |  - Alarm Sfx   |  |
|  +---------------------------+  +--------------------------+  +----------------+  |
|                                                                                   |
|  +---------------------------+  +--------------------------+                      |
|  |   Director Autoplay Mode  |  |   Client API Adapter     |                      |
|  |  - Step Sequence Autoplay |  |  - Wake-Up / Health Polling                      |
|  +---------------------------+  +--------------------------+                      |
+----------------------------------------+------------------------------------------+
                                         |
                                         | REST / JSON (HTTP 1.1)
                                         v
+-----------------------------------------------------------------------------------+
|                             FASTAPI BACKEND SERVICE                               |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                    Security & Rate Limiting Middleware                      |  |
|  |  - In-memory Token-Bucket Rate Limiter (120/min general, 10/min AI)          |  |
|  |  - 20 KB Payload Size Protection (413 Payload Too Large)                    |  |
|  |  - Security Headers (CSP, nosniff, frame-ancestors 'none', X-Request-ID)     |  |
|  |  - Structured Logging without Query Secrets                                  |  |
|  +-------------------------------------+---------------------------------------+  |
|                                        |                                          |
|        +-------------------------------+-------------------------------+          |
|        |                               |                               |          |
|        v                               v                               v          |
|  +--------------------+      +--------------------+      +--------------------+   |
|  |  Core Sim Registry |      |   Lab Engine Core  |      |   AI Mentor Engine |   |
|  |  - pharma.pk       |      |  - Session State   |      |  - Claude 3.5 API  |   |
|  |  - chem.titration  |      |  - Action Dispatch |      |  - Rule-Based Fall |   |
|  |  - pharma.trial    |      |  - Safety Violator |      |  - Daily Cap Guard |   |
|  +--------------------+      +--------------------+      +--------------------+   |
|                                        |                                          |
|                                        v                                          |
|  +-----------------------------------------------------------------------------+  |
|  |                         Persistence Layer (app.db)                          |  |
|  |  - MongoDB Atlas Driver (Motor async) with 30-day session TTL indexes       |  |
|  |  - Safe Thread-Safe In-Memory Fallback Adapter (for offline / demo runs)    |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 2. End-to-End Data Flows

### Flow A: Single Lab Action Execution (e.g., Weigh Dose)
```
User clicks "Weigh Dose"
   │
   ├──> Client: Triggers WebAudio tare/weigh beep; begins Action Camera ease.
   ├──> Client: Dispatches POST /api/lab/sessions/{id}/actions {action: "weigh", params: {weight_g: 0.5}}
   │
   ▼
FastAPI Middleware
   ├──> Verifies body size <= 20 KB; increments Token Bucket.
   │
   ▼
Lab Session Router (`lab.py`)
   ├──> Fetches session state from MongoDB (or in-memory cache).
   ├──> `apply_action(session, action)`:
   │       1. Evaluates protocol checklist rules (e.g., tared balance first?).
   │       2. Evaluates safety rules (e.g., lab coat worn?).
   │       3. Advances physical apparatus state (balance reading = 0.500 g).
   │       4. Deducts or awards score components (Safety, Accuracy, Technique).
   ├──> Persists updated session to database.
   │
   ▼
Client Response:
   └──> Avatar hands play spatula animation; LCD display updates; protocol checklist advances.
```

---

### Flow B: AI Mentor Query (Dr. Orbis)
```
User clicks "Step Hint" or types question
   │
   ├──> Client: Dispatches POST /api/lab/sessions/{id}/mentor {mode: "hint"}
   │
   ▼
FastAPI Middleware
   ├──> Checks AI rate limit (max 10 requests / min / IP).
   │
   ▼
Mentor Engine (`lab.py`):
   ├──> Checks in-memory 60-second TTL cache for identical session state.
   ├──> Checks session call cap (max 30 calls/session) & global daily cap (300 calls/day).
   ├──> If permitted & GEMINI_API_KEY present:
   │       Constructs XML-wrapped context prompt; calls Google Gemini API with 8s timeout.
   │    Else:
   │       Generates deterministic rule-based hint from current protocol step & score parts.
   │
   ▼
Client Response:
   └──> Displays Dr. Orbis bubble with [AI] or [Rule-Based] badge, latency, and calls left.
```

---

### Flow C: Vectorized Virtual Clinical Trial (500 Patients)
```
User clicks "Run Cohort"
   │
   ├──> Client: Dispatches POST /api/runs with module "pharma.trial" {n_patients: 500, dose_mg: 500}
   │
   ▼
PharmaTrialModule (`pharma_trial.py`):
   ├──> Seeds NumPy RNG with requested seed (default 42).
   ├──> Draws log-normal weight (CV 18%) and clearance (CV 30%) arrays for 500 patients.
   ├──> Vectorized one-compartment Bateman evaluation over 100 time points (50,000 evaluations in <20 ms).
   ├──> Calculates outcome percentiles (5th, 25th, 50th, 75th, 95th), Cmax histogram, and outcome codes.
   │
   ▼
Client Response:
   └──> Three.js crowd gallery triggers color wave across 500 avatar dots; updates summary charts.
```
