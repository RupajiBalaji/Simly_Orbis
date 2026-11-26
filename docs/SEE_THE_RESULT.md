# Simly Orbis – Verification & Staging Guide (Branch: `phase-p5-space`)

This guide is written for the founder to run, verify, and deploy Simly Orbis on Windows and Render staging from the `phase-p5-space` branch.

---

## 1. Local Run on Windows (Clean-Clone Verified)

These exact commands have been executed and verified in a clean environment on Windows.

### Step-by-Step Commands

1. **Clone the repository and checkout `phase-p5-space`:**
   ```powershell
   git clone -b phase-p5-space https://github.com/RupajiBalaji/Simly_Orbis.git simly-orbis-verify
   cd simly-orbis-verify
   ```

2. **Create and activate a fresh virtual environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r backend/requirements.txt -r backend/requirements-dev.txt
   ```

4. **Configure Environment Variables (Safe Local Defaults):**
   ```powershell
   $env:ENVIRONMENT = "development"
   $env:PORT = "8000"
   $env:AI_ENABLED = "false"
   $env:ALLOWED_ORIGINS = "http://localhost:8000,http://127.0.0.1:8000"
   $env:TRUST_PROXY = "false"
   $env:MENTOR_DAILY_CAP = "300"
   ```
   *(Note: Leaving `MONGODB_URI` unset automatically defaults to in-memory store mode. Do not set `STORAGE_MODE = "in-memory"` as the app already automatically selects in-memory mode when `MONGODB_URI` is absent. AI is disabled by default unless `GEMINI_API_KEY` is provided and `$env:AI_ENABLED = "true"` is set).*

5. **Start the Server:**
   ```powershell
   python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
   ```

6. **Open in Browser:**
   - **Interactive Web Application:** [http://localhost:8000/](http://localhost:8000/)
   - **Service Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)
   - **Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
   - *(Note: When testing in Chrome/Edge, open DevTools (`F12`), check **Disable cache** on the Network tab, or use `Ctrl + Shift + R` to ensure the latest ES modules and styles are loaded fresh).*

### Verified Local Execution Output

```text
INFO:     Started server process [11972]
INFO:     Waiting for application startup.
2026-11-22 12:52:59,648  INFO      app.security – === ORBIS LAB CONFIGURATION VALIDATION ===
2026-11-22 12:52:59,648  INFO      app.security – App Version:       0.9.0-dev
2026-11-22 12:52:59,649  INFO      app.security – Git SHA:           [NOT SET]
2026-11-22 12:52:59,649  INFO      app.security – Database:          In-Memory Fallback
2026-11-22 12:52:59,649  INFO      app.security – Gemini Key:        [NOT SET]
2026-11-22 12:52:59,649  INFO      app.security – Active AI Mentor:  Rule-based fallback
2026-11-22 12:52:59,649  INFO      app.security – AI Enabled:        False
2026-11-22 12:52:59,649  INFO      app.security – Trust Proxy:       False
2026-11-22 12:52:59,649  INFO      app.security – Mentor Daily Cap:  300 calls/day
2026-11-22 12:52:59,649  INFO      app.security – Allowed Origins:   http://localhost:8000,http://127.0.0.1:8000
2026-11-22 12:52:59,649  INFO      app.security – ==========================================
2026-11-22 12:52:59,649  WARNING   app.db – MONGODB_URI not set – starting in memory-store mode.
2026-11-22 12:52:59,650  INFO      app.db – MongoDB indexes ensured (including 30-day session TTL).
2026-11-22 12:52:59,650  INFO      app.db – Seeded 11 sample leaderboard scores.
2026-11-22 12:52:59,650  INFO      app.core.registry – Registered simulation module: pharma.pk (pharma)
2026-11-22 12:52:59,650  INFO      app.core.registry – Registered simulation module: chem.titration (chemistry)
2026-11-22 12:52:59,650  INFO      app.core.registry – Registered simulation module: pharma.trial (pharma)
2026-11-22 12:52:59,650  INFO      app.core.registry – Registered simulation module: pharma.trial_v2 (pharma)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
2026-11-22 12:53:00,153  INFO      app.main – [91325ea1] GET /api/health -> 200 (1.1 ms)
```

---

## 2. Render Staging Setup (Second Web Service)

To test `phase-p5-space` in the cloud without impacting the production service (`simly-orbis`), create a **second, independent web service** on Render.

> [!IMPORTANT]
> **Do NOT edit or modify the existing production service (`simly-orbis`) on Render.**

### Web Service Settings
- **Name:** `simly-orbis-staging`
- **Environment / Runtime:** `Docker`
- **Region:** `Oregon` (or matching your database region)
- **Branch:** `phase-p5-space`
- **Plan:** `Free`
- **Health Check Path:** `/api/health`
- **Auto-Deploy:** `Yes` (or manual trigger)

### Environment Variables
Configure the following environment variables in the Render Dashboard under **Environment**:

| Variable | Recommended Staging Value | Purpose |
|---|---|---|
| `PORT` | `10000` | Port expected by Render router (matches Dockerfile) |
| `ENVIRONMENT` | `staging` | Identifies runtime mode |
| `DB_NAME` | `Simly_Orbis_Staging` | **Isolated staging database** (prevents mixing with production data) |
| `MONGODB_URI` | *(Your MongoDB connection string)* | Leave unset if using In-Memory storage |
| `TRUST_PROXY` | `true` | Required behind Render reverse proxy |
| `ALLOWED_ORIGINS` | `https://simly-orbis-staging.onrender.com,http://localhost:8000` | CORS whitelist for staging |
| `AI_ENABLED` | `true` (or `false`) | Toggles Gemini AI mentor assistance |
| `GEMINI_API_KEY` | *(Your Gemini API key)* | Optional; falls back to rule-based mentor if empty |
| `GEMINI_MODEL` | `gemini-flash-lite-latest` | Default model specification |
| `MENTOR_DAILY_CAP` | `300` | Daily rate cap for AI tutor calls |
| `GIT_SHA` | *(Leave empty)* | Render automatically injects `RENDER_GIT_COMMIT` |

### Expected `/api/health` Output on Staging

Visiting `https://simly-orbis-staging.onrender.com/api/health` should return:
```json
{
  "status": "ok",
  "storage_mode": "mongodb",
  "collections": {
    "players": 0,
    "scores": 0,
    "runs": 0,
    "lab_sessions": 0,
    "lab_reports": 0
  },
  "modules": [
    "pharma.pk",
    "chem.titration",
    "pharma.trial",
    "pharma.trial_v2"
  ],
  "app_version": "0.9.0-dev",
  "version": "0.9.0-dev",
  "git_sha": "4737630623b97779f1ea01e6db85915e3f79a916",
  "ai_status": {
    "enabled": true,
    "has_api_key": true,
    "model": "gemini-flash-lite-latest",
    "daily_cap": 300,
    "active_mode": "gemini"
  }
}
```

---

## 3. Founder Review Checklist

When opening the app in the browser, review the following key items:

### Console Warnings Explanation
When opening the **Launch & Orbit Bench** scenario with DevTools open (`F12` -> `Console`), you may observe 6 warnings:
```text
Unmapped apparatus: id='launch_pad', type='launch_pad' apparatus.js:256
Unmapped apparatus: id='rocket', type='rocket' apparatus.js:256
Unmapped apparatus: id='propellant_tanks', type='propellant_tanks' apparatus.js:256
Unmapped apparatus: id='range_control', type='range_control' apparatus.js:256
Unmapped apparatus: id='flight_computer', type='flight_computer' apparatus.js:256
Unmapped apparatus: id='tracking_station', type='tracking_station' apparatus.js:256
```
**Why this occurs and why it is completely harmless:**
- In `frontend/lab/world/scene.js`, the general chemistry apparatus builder `buildApparatus(apparatusList, this.scene)` runs first. It logs warnings for apparatus IDs that do not have tabletop glassware models in chemistry.
- Immediately after (`scene.js:392`), `this.spaceScene.activate()` initializes all 6 space facilities (`launch_pad`, `rocket`, `propellant_tanks`, `range_control`, `flight_computer`, `tracking_station`) and merges them into `apparatusLookup`.
- All 6 facilities are fully rendered in 3D, interactive, and functional on Pad 39A. These warnings are purely informational from the chemistry module.
- *(Note: If testing on the existing production Render URL `simly-orbis.onrender.com`, that service runs `main`, which predates the P5 space apparatus mapping. On `phase-p5-space`, the apparatuses are mapped and rendered).*

### Interactive Review Checklist
- [ ] **Persistent HUD Elements:**
  - Verify persistent HUD elements on screen (Target: at most 5 persistent elements, >70% screen area for 3D scene).
- [ ] **Next Action Discovery:**
  - Check that a new user understands the current step and primary action within 5 seconds without clutter.
- [ ] **Movement & Locomotion Direction:**
  - Press `W`: Avatar moves away from the camera along the horizontal ground plane.
  - Press `S`: Avatar moves toward the camera.
  - Press `D`: Avatar moves to the camera's right.
  - Press `A`: Avatar moves to the camera's left.
- [ ] **Camera Orbit & Follow Stability:**
  - While walking the avatar in a circle, verify that the camera yaw does not spin or self-rotate unexpectedly without user mouse drag or Q/E input.
- [ ] **Space District 3D Models:**
  - Verify the 3D models for the Launch Pad, Rocket, Propellant Tank Farm, Avionics Terminal, Range Safety Station, and Telemetry Dish render on Pad 39A.

---

## 4. Visual Proof Screenshots

The following verified screenshots demonstrate the clean 5-element HUD and 3D scene share across all viewports:

| Viewport | Direct File Link | Resolution | HUD Area | 3D Scene Share | Notes |
|---|---|---|---|---|---|
| Desktop Wide (PK Ward) | [`after_1920x1080.png`](file:///e:/Simly%20Orbis/docs/screenshots/ux-fix/after_1920x1080.png) | 1920x1080 | 5.6% | 94.4% | Clean 5-element HUD, zero modals |
| Standard Laptop (PK Ward) | [`after_1366x768.png`](file:///e:/Simly%20Orbis/docs/screenshots/ux-fix/after_1366x768.png) | 1366x768 | 11.5% | 88.5% | Single task card, 1-click action |
| Compact Laptop (Launch Bench) | [`after_1280x720.png`](file:///e:/Simly%20Orbis/docs/screenshots/ux-fix/after_1280x720.png) | 1280x720 | 10.0% | 90.0% | 3D rocket & pad, drawer collapsed |
| Tablet Portrait (PK Ward) | [`after_768x1024.png`](file:///e:/Simly%20Orbis/docs/screenshots/ux-fix/after_768x1024.png) | 768x1024 | 16.6% | 83.4% | Centered card, zero clipping |
| Mobile Portrait (PK Ward) | [`after_390x844.png`](file:///e:/Simly%20Orbis/docs/screenshots/ux-fix/after_390x844.png) | 390x844 | 33.7% | 66.3% | Ergonomic mobile bottom sheet |
| Desktop Wide (Launch Bench) | [`after_launch_bench_1920x1080.png`](file:///e:/Simly%20Orbis/docs/screenshots/ux-fix/after_launch_bench_1920x1080.png) | 1920x1080 | 4.7% | 95.3% | 3D space scene visibility |
| Standard Laptop (Launch Bench) | [`after_launch_bench_1366x768.png`](file:///e:/Simly%20Orbis/docs/screenshots/ux-fix/after_launch_bench_1366x768.png) | 1366x768 | 8.8% | 91.2% | Space telemetry in drawer |
| Baseline Defect (Before) | [`before_1920x1080.png`](file:///e:/Simly%20Orbis/docs/screenshots/ux-fix/before_1920x1080.png) | 1920x1080 | 42.5% | 57.5% | 9 cluttered competing panels |
| 4-Yaw Movement Proof | [`movement_proof_strip.png`](file:///e:/Simly%20Orbis/docs/screenshots/ux-fix/movement_proof_strip.png) | 1280x720 | N/A | N/A | Avatar moves away from camera at 0°, 90°, 180°, 270° |

---

## 5. Current Task Status Summary

| Task | Status | Commit Hash | Notes / Acceptance Tests |
|---|---|---|---|
| **Space Apparatus Mapping Fix** | **DONE** | `b3352fe` / `cce7f17` | Space apparatuses mapped to 3D facility models; harmless chemistry log explained. |
| **Problem B: Locomotion & Camera Rig** | **DONE** | `011b8cf` | Correct right-vector basis ($f \times \text{up}$), `movement_math.js`, user-only yaw follow camera, critically damped translation, $< 0.01^\circ$ model alignment. |
| **Problem A: Clean HUD Overhaul** | **DONE** | `cce7f17` | Exactly 5 persistent elements (`data-hud-persistent`), >88% 3D scene area at 1366x768, 1-click primary action task card, slide-over menu drawer. |
| **Lobby Banners, Modal & Counts (P2)** | **DONE** | `1e476d3` | Non-overlapping offline banner (`--offline-banner-height`), 2s threshold for waking modal, and synced district card counts. |
| **Real Proof & Sidecars (Q1, Q2, Q3)** | **DONE** | `4892efd` | Real HUD screenshots with sidecar metadata at all 5 viewports; Launch Bench drawer; real 4-yaw movement proof strip. |
| **Semantic Proof Gate (Q4)** | **DONE** | `d4c227f` | Semantic validation of sidecars, modals, and color bin overlay coverage in `check_proof_unique.py`; unit tests in `test_proof_gate.py`. |
| **Documentation & Honesty (Q5, Q6)** | **DONE** | Current HEAD | Exact sidecar metrics, console warning transparency, removed invalid env var, verified screenshot links. |
| **Clean-Clone Pytest Suite** | **DONE** | Current HEAD | Full backend test suite passing with 0 failures reproducing CI. |
| **Founder Review Sign-off** | **BLOCKED-HUMAN** | *Pending founder* | Awaiting founder physical feel test of movement, camera, and HUD on local or staging environment. |
