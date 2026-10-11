# Deployment Guide – Simly Orbis

This guide explains how to deploy **Simly Orbis** to production on Render, run locally with Docker, and configure necessary environment variables.

---

## 1. Deploy to Render via Blueprint (5 Clicks)

Simly Orbis includes a turnkey `render.yaml` Blueprint file configured for Render's free tier.

1. **Push your repository to GitHub** (public or private).
2. Go to the [Render Dashboard](https://dashboard.render.com/) and click **New +** > **Blueprint**.
3. Connect your GitHub repository (`Simly_Orbis`).
4. Click **Apply**: Render automatically discovers `render.yaml` and provisions the Docker web service.
5. In the service dashboard, configure the secret environment variables (`MONGODB_URI`, `ANTHROPIC_API_KEY`, etc.) as prompted under **Environment**.

Your service will build from `Dockerfile` and be live at `https://<service-name>.onrender.com`.

---

## 2. Environment Variables Reference

| Variable | Required? | Default | Description |
|---|---|---|---|
| `PORT` | Optional | `8000` (`10000` on Render) | Port on which Uvicorn listens. |
| `MONGODB_URI` | Optional | `""` | MongoDB Atlas connection string. If omitted, app falls back cleanly to in-memory storage. |
| `DB_NAME` | Optional | `Simly_Orbis` | Name of the database to use. |
| `GEMINI_API_KEY` | Optional | `""` | Primary key for Dr. Orbis (Mentor & Tutor). If omitted, falls back to Anthropic key. |
| `GEMINI_MODEL` | Optional | `gemini-flash-latest` | Google Gemini model identifier. |
| `ANTHROPIC_API_KEY` | Optional | `""` | Secondary key for Dr. Orbis (Mentor & Tutor). If omitted, falls back to rule-based hints. |
| `ANTHROPIC_MODEL` | Optional | `claude-haiku-4-5-20251001` | Anthropic Claude model identifier. |
| `TRUST_PROXY` | Optional | `false` (`true` on Render) | When `true`, rate limiter trusts proxy headers and uses the LAST hop of `X-Forwarded-For`. |
| `AI_ENABLED` | Optional | `true` | Set to `false` to immediately disable all external LLM calls. |
| `MENTOR_DAILY_CAP` | Optional | `300` | Maximum AI mentor calls allowed per UTC calendar day. |
| `ALLOWED_ORIGINS` | Optional | `*` | Comma-separated CORS allowed origins. |

> [!NOTE]
> **Unified AI Provider Precedence**: Both the in-game 3D lab **Mentor** and the 2D PK simulation **Tutor** use whichever API key exists (`GEMINI_API_KEY` first priority, `ANTHROPIC_API_KEY` second priority). If neither key is provided, both services seamlessly operate using educational rule-based fallback responses.

---

## 3. Local Deployment with Docker

### Prerequisites
- Docker Engine / Docker Desktop installed.

### Build the Image
```bash
docker build -t simly-orbis:latest .
```

### Run the Container
```bash
docker run -p 8000:8000 \
  -e MONGODB_URI="mongodb+srv://..." \
  -e ANTHROPIC_API_KEY="sk-ant-..." \
  -e GEMINI_API_KEY="..." \
  simly-orbis:latest
```

The application will be accessible at:
```
http://localhost:8000
```

---

## 4. Cold Start & Wake-Up Handling

Render's free tier spins down web services after 15 minutes of inactivity:
- **First-load latency**: Initial cold start can take 40–55 seconds.
- **Client wake-up overlay**: The game includes a built-in wake-up overlay that polls `/api/ping` with exponential backoff until the backend responds, displaying a live countdown and manual retry button.
- **Zero data loss**: All static and simulation endpoints are cached with defensive fallbacks.

---

## 5. Troubleshooting & FAQ

### MongoDB Connection Issues
- **Symptom**: Startup logs report fallback to in-memory storage.
- **Fix**: Check that your MongoDB Atlas IP Access List includes `0.0.0.0/0` (allow access from anywhere) so Render's dynamic IP addresses can connect.

### Anthropic API Quota / Rate Limiting
- **Symptom**: Mentor responses include `"source": "fallback"`.
- **Fix**: Verify your Anthropic credits and rate limits. If the global daily cap (`MENTOR_DAILY_CAP`) is exhausted, Dr. Orbis automatically switches to deterministic rule-based guidance without crashing.

### CORS Errors
- **Symptom**: Browser console logs `CORS policy` blockage.
- **Fix**: Update `ALLOWED_ORIGINS` in your environment settings with your specific domain or keep `*` for public access.
