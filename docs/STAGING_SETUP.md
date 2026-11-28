# Render Staging Setup Guide (`phase-p5-space`)

> **Important:** Create a **NEW, separate** Render Web Service for staging. Do **not** edit or re-point the existing production Render service.

## 1. Create the Staging Web Service (Click-by-Click)
1. Log in to the [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** → **Web Service**.
3. Connect the `RupajiBalaji/Simly_Orbis` GitHub repository.
4. Configure service settings:
   - **Name**: `simly-orbis-staging` (distinct from production)
   - **Region**: Same region as your MongoDB Atlas cluster
   - **Branch**: `phase-p5-space`
   - **Runtime**: `Docker` (uses root `Dockerfile`) or `Python 3`
     - If Python runtime:
       - **Build Command**: `pip install -r backend/requirements.txt`
       - **Start Command**: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/api/health`

## 2. Environment Variables
Set these exact variables in Render **Environment** tab:

| Variable | Value / Guidance |
|---|---|
| `ENVIRONMENT` | `production` |
| `MONGODB_URI` | Separate staging MongoDB URI using a **different database name** (e.g. `.../Simly_Orbis_Staging?...`) so staging test data never mixes with production. |
| `GEMINI_API_KEY` | Your Gemini API key (or leave blank to run deterministic rule-based fallback). |
| `GEMINI_MODEL` | `gemini-flash-lite-latest` |
| `TRUST_PROXY` | `true` (required behind Render's reverse proxy so `resolve_client_ip` reads the last-hop `X-Forwarded-For`). |
| `AI_ENABLED` | `true` (set `false` to disable LLM calls cleanly). |
| `MENTOR_DAILY_CAP` | `300` (daily global cap on AI mentor calls). |
| `ALLOWED_ORIGINS` | `https://simly-orbis-staging.onrender.com` (must match the exact staging URL). |

## 3. Post-Deploy Verification
1. Wait for Render deploy status **Live**.
2. Open `https://simly-orbis-staging.onrender.com/api/health` and confirm `"status": "ok"`.
3. Run the live smoke script locally against staging:
   ```bash
   python scripts/smoke_live.py --url https://simly-orbis-staging.onrender.com
   ```
