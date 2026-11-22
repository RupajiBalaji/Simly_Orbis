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
   $env:STORAGE_MODE = "in-memory"
   $env:ALLOWED_ORIGINS = "http://localhost:8000,http://127.0.0.1:8000"
   $env:TRUST_PROXY = "false"
   $env:MENTOR_DAILY_CAP = "300"
   ```
   *(Note: Leaving `MONGODB_URI` unset defaults safely to high-performance in-memory storage. AI is disabled by default unless `GEMINI_API_KEY` is provided and `$env:AI_ENABLED = "true"` is set).*

5. **Start the Server:**
   ```powershell
   python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
   ```

6. **Open in Browser:**
   - **Interactive Web Application:** [http://localhost:8000/](http://localhost:8000/)
   - **Service Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)
   - **Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

### Verified Local Execution Output

```text
INFO:     Started server process [11972]
INFO:     Waiting for application startup.
2026-11-22 12:52:59,648  INFO      app.security – === ORBIS LAB CONFIGURATION VALIDATION ===
2026-11-22 12:52:59,648  INFO      app.security – App Version:       0.8.0-dev
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
  "app_version": "0.8.0-dev",
  "version": "0.8.0-dev",
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

- [ ] **Launch & Orbit Bench Console Warnings:**
  - Open DevTools Console (`F12` -> `Console`).
  - Select the **Launch & Orbit Bench** scenario.
  - Verify that **zero** `Unmapped apparatus: id='...'` warnings appear for `launch_pad`, `rocket`, `propellant_tanks`, `range_control`, `flight_computer`, or `tracking_station`. (Resolved in commit `b3352fe`).
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

### How to Report a Problem
If any discrepancy, unexpected behavior, or regression is observed:
1. Capture a full-window screenshot (including HUD and 3D scene).
2. Open DevTools Console (`Ctrl + Shift + I` or `F12`) and copy any error or warning messages.
3. Note the active camera mode (Follow, Free, First-Person) and window resolution.
4. Report the issue with the screenshot and console text attached.

---

## 4. Current Task Status Summary

| Task | Status | Commit Hash | Notes / Acceptance Tests |
|---|---|---|---|
| **Space Apparatus Mapping Fix** | **DONE** | `b3352fe` | Space apparatuses mapped to 3D models; 0 unmapped warnings; verified by `test_space_apparatus_mapping_and_no_unmapped_warnings`. |
| **Clean-Clone Pytest Suite** | **DONE** | `4737630` | 801 passed, 2 skipped, 0 failed in clean-clone venv reproducing CI. |
| **Problem B: Controls & Camera Rig** | **IN PROGRESS (Diagnosed)** | *Pending commit* | Causes diagnosed (`controller.js:400` basis inversion, `controller.js:398` forward vector, `camera_rig.js:686` chase assist). |
| **Problem A: Clean HUD Overhaul** | **IN PROGRESS** | *Pending commit* | Progressive disclosure, 5 persistent elements, and coach-mark sequence being authored. |
| **Founder Review Sign-off** | **BLOCKED-HUMAN** | *Pending founder* | Awaiting founder visual inspection and approval on staging. |
