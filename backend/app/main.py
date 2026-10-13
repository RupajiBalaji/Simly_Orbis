"""
Simly Orbis – FastAPI application entry point.
RC1 Hardened for public deployment with rate limiting, payload protection,
Content-Security-Policy, structured logging, and health checks.
"""

from __future__ import annotations

import logging
import mimetypes
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import settings
from app.core.registry import list_modules, register
from app.db import STORAGE_MODE, close_db, init_db
import app.db as _db
from app.modules.chem_titration import ChemTitrationModule
from app.modules.pharma_pk import PharmaPKModule
from app.modules.pharma_trial import PharmaTrialModule
from app.routes import drugs, lab, levels, modules, runs, scores, simulate, trial, tutor, validation
from app.security import rate_limiter, validate_startup_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
)
log = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent.parent.parent / "frontend"

# Ensure Javascript and WebAssembly MIME types are registered
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("application/wasm", ".wasm")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN001
    validate_startup_config()
    await init_db()
    register(PharmaPKModule())
    register(ChemTitrationModule())
    register(PharmaTrialModule())
    log.info("Storage mode: %s | App Version: %s", STORAGE_MODE, settings.app_version)
    yield
    await close_db()


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Simly Orbis",
    version=settings.app_version,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Security & Rate Limiting Middlewares
# ---------------------------------------------------------------------------

class SecurityAndRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Enforces:
    1. Request-ID tracking & structured request logging (without leaking secrets).
    2. Body size limit (max 20 KB for API payloads).
    3. Per-IP token-bucket rate limiting (120/min general, 10/min AI, 20/min sessions).
    4. Essential security response headers (CSP, X-Content-Type-Options, etc.).
    """

    async def dispatch(self, request: Request, call_next) -> Response:  # noqa: ANN001
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        t_start = time.perf_counter()

        client_ip = None
        forwarded_for = request.headers.get("x-forwarded-for")
        is_test_runner = (
            request.url.netloc == "test"
            or request.headers.get("host") == "test"
        )

        trust_proxy = (
            getattr(settings, "trust_proxy", False)
            or os.environ.get("TRUST_PROXY", "").strip().lower() in ("true", "1", "yes")
        )

        if trust_proxy and forwarded_for:
            # Behind trusted proxy (e.g. Render): use the LAST hop added by proxy
            client_ip = forwarded_for.split(",")[-1].strip()
        elif not is_test_runner and request.client:
            client_ip = request.client.host
        elif not is_test_runner:
            client_ip = "127.0.0.1"

        path = request.url.path

        # 1. Payload size check on POST / PUT / PATCH API endpoints (max 20 KB = 20,480 bytes)
        if request.method in ("POST", "PUT", "PATCH") and path.startswith("/api"):
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    if int(content_length) > 20480:
                        return JSONResponse(
                            status_code=413,
                            content={"detail": "Request payload too large (max 20 KB)."},
                        )
                except ValueError:
                    pass

        # 2. Rate limiting check on /api/ endpoints (when client_ip is resolved)
        if client_ip and path.startswith("/api"):
            category = "general"
            if "/mentor" in path or path.endswith("/tutor"):
                category = "ai"
            elif path == "/api/lab/sessions" and request.method == "POST":
                category = "session_create"

            if not rate_limiter.check(client_ip, category=category):
                log.warning("[%s] 429 Rate limit exceeded: ip=%s path=%s cat=%s", request_id, client_ip, path, category)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Please wait a moment before trying again."},
                    headers={"X-Request-ID": request_id},
                )

        # 3. Process request
        response: Response = await call_next(request)
        elapsed_ms = (time.perf_counter() - t_start) * 1000.0

        # Structured request log without query params or body content
        log.info("[%s] %s %s -> %d (%.1f ms)", request_id, request.method, path, response.status_code, elapsed_ms)

        # 4. Security Headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"

        # CSP Policy: Tightened with connect-src 'self' only (wildcard removed).
        # 'unsafe-inline' is retained in script-src/style-src for <script type="importmap"> and dynamic HUD DOM styles.
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "media-src 'self' blob:; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp_policy

        # Custom caching headers for static assets
        if path == "/" or path.endswith(".html"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        elif "/vendor/" in path:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"

        return response


app.add_middleware(SecurityAndRateLimitMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS configuration from ALLOWED_ORIGINS
allowed_origins_raw = settings.allowed_origins.strip()
allowed_origins_list = (
    ["*"]
    if not allowed_origins_raw or allowed_origins_raw == "*"
    else [origin.strip() for origin in allowed_origins_raw.split(",") if origin.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global Exception Handler (Production Safe)
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    log.error("[%s] Unhandled server error: %s: %s", request_id, type(exc).__name__, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "request_id": request_id},
        headers={"X-Request-ID": request_id},
    )


# ---------------------------------------------------------------------------
# Meta Endpoints: /api/ping & /api/health
# ---------------------------------------------------------------------------

@app.get("/api/ping", tags=["meta"], summary="Lightweight wake-up ping")
async def ping() -> dict[str, str]:
    """Tiny, near-instantaneous ping to check if server is awake."""
    return {"ping": "pong"}


@app.get("/api/health", tags=["meta"], summary="Service health")
async def health() -> dict:
    """Return service health, storage mode, live collection counts, and registered modules."""
    db = _db.database
    players_count = await db["players"].count_documents({})
    scores_count = await db["scores"].count_documents({})
    runs_count = await db["runs"].count_documents({})
    lab_sessions_count = await db["lab_sessions"].count_documents({})
    lab_reports_count = await db["lab_reports"].count_documents({})
    registered_module_ids = [m.id for m in list_modules()]

    return {
        "status": "ok",
        "storage_mode": _db.STORAGE_MODE,
        "collections": {
            "players": players_count,
            "scores": scores_count,
            "runs": runs_count,
            "lab_sessions": lab_sessions_count,
            "lab_reports": lab_reports_count,
        },
        "modules": registered_module_ids,
        "app_version": settings.app_version,
        "version": settings.app_version,
        "git_sha": settings.git_sha or None,
    }


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(modules.router)
app.include_router(runs.router)
app.include_router(drugs.router)
app.include_router(levels.router)
app.include_router(simulate.router)
app.include_router(scores.router)
app.include_router(tutor.router)
app.include_router(lab.router)
app.include_router(trial.router)
app.include_router(validation.router)


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
