"""
Simly Orbis – FastAPI application entry point.

Start from the project root (simly-orbis/) with:
    uvicorn app.main:app --reload --app-dir backend
Or from inside backend/:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.registry import list_modules, register
from app.db import STORAGE_MODE, close_db, init_db
import app.db as _db
from app.modules.chem_titration import ChemTitrationModule
from app.modules.pharma_pk import PharmaPKModule
from app.modules.pharma_trial import PharmaTrialModule
from app.routes import drugs, lab, levels, modules, runs, scores, simulate, trial, tutor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
)
log = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent.parent.parent / "frontend"


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN001
    await init_db()
    # Register core simulation modules
    register(PharmaPKModule())
    register(ChemTitrationModule())
    register(PharmaTrialModule())
    log.info("Storage mode: %s", STORAGE_MODE)
    yield
    await close_db()


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Simly Orbis",
    version="0.3.0",
    lifespan=lifespan,
)

# CORS – allow all origins in development; tighten for production by replacing
# allow_origins with a specific list.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# API routes  (registered BEFORE the static mount so "/" doesn't shadow them)
# ---------------------------------------------------------------------------

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
    }


app.include_router(modules.router)
app.include_router(runs.router)
app.include_router(drugs.router)
app.include_router(levels.router)
app.include_router(simulate.router)
app.include_router(scores.router)
app.include_router(tutor.router)
app.include_router(lab.router)
app.include_router(trial.router)


# ---------------------------------------------------------------------------
# Static files – mounted last so the catch-all "/" doesn't shadow any route
# ---------------------------------------------------------------------------
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
