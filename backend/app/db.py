"""
Database layer.

Tries to connect to MongoDB Atlas via Motor.  If the URI is absent or the
ping fails the module falls back to a lightweight in-memory store that exposes
the same minimal interface used by the rest of the application.
"""

from __future__ import annotations

import logging
from typing import Any

from app.config import settings

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Storage mode flag – read by health endpoint and startup banner
# ---------------------------------------------------------------------------
STORAGE_MODE: str = "unknown"  # set to "mongodb" or "memory" during init


# ---------------------------------------------------------------------------
# In-memory fallback store
# ---------------------------------------------------------------------------
class _InMemoryCollection:
    """Minimal Motor-shaped collection stub backed by a plain Python list."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._docs: list[dict[str, Any]] = []

    async def count_documents(self, _filter: dict | None = None) -> int:
        if not _filter:
            return len(self._docs)
        return sum(
            1 for doc in self._docs
            if all(doc.get(k) == v for k, v in _filter.items())
        )

    async def insert_one(self, document: dict) -> None:
        self._docs.append(document)

    async def find_one(self, _filter: dict) -> dict | None:
        for doc in self._docs:
            if all(doc.get(k) == v for k, v in _filter.items()):
                return doc
        return None

    async def find(
        self,
        _filter: dict | None = None,
        sort: list[tuple[str, int]] | None = None,
        limit: int = 0,
    ) -> list[dict]:
        """Return matching docs, optionally sorted and limited."""
        if not _filter:
            results = list(self._docs)
        else:
            results = [
                doc for doc in self._docs
                if all(doc.get(k) == v for k, v in _filter.items())
            ]

        if sort:
            for field, direction in reversed(sort):
                results.sort(key=lambda d: d.get(field, 0), reverse=(direction == -1))

        if limit and limit > 0:
            results = results[:limit]

        return results

    async def update_one(
        self,
        _filter: dict,
        update: dict,
        upsert: bool = False,
    ) -> None:
        """Minimal $set / $setOnInsert upsert support."""
        for i, doc in enumerate(self._docs):
            if all(doc.get(k) == v for k, v in _filter.items()):
                set_data = update.get("$set", {})
                self._docs[i] = {**doc, **set_data}
                return
        # No match
        if upsert:
            new_doc = {**_filter}
            new_doc.update(update.get("$set", {}))
            new_doc.update(update.get("$setOnInsert", {}))
            self._docs.append(new_doc)

    async def create_index(self, keys: list[tuple[str, int]], **_kwargs: Any) -> None:
        """No-op for in-memory store (indexes not needed for correctness)."""


class _InMemoryDatabase:
    """Minimal Motor-shaped database stub."""

    def __init__(self) -> None:
        self._collections: dict[str, _InMemoryCollection] = {}

    def __getitem__(self, name: str) -> _InMemoryCollection:
        if name not in self._collections:
            self._collections[name] = _InMemoryCollection(name)
        return self._collections[name]

    def get_collection(self, name: str) -> _InMemoryCollection:  # Motor alias
        return self[name]


# ---------------------------------------------------------------------------
# Module-level handles – populated by init_db()
# ---------------------------------------------------------------------------
_mongo_client: Any = None  # motor.motor_asyncio.AsyncIOMotorClient | None
database: Any = None        # real DB or _InMemoryDatabase


async def create_indexes() -> None:
    """Create indexes required for efficient leaderboard and run queries."""
    import pymongo  # noqa: PLC0415 – available as Motor dependency

    scores = database["scores"]
    # Compound index: leaderboard query filters by level_id and sorts by score desc
    await scores.create_index(
        [("level_id", pymongo.ASCENDING), ("score", pymongo.DESCENDING)],
        name="level_score_idx",
    )

    runs = database["runs"]
    # Runs indexes: created_at desc, (module_id, created_at desc), run_id unique
    await runs.create_index([("created_at", pymongo.DESCENDING)], name="runs_created_idx")
    await runs.create_index(
        [("module_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
        name="runs_module_created_idx",
    )
    await runs.create_index([("run_id", pymongo.ASCENDING)], unique=True, name="runs_run_id_unique_idx")

    lab_sessions = database["lab_sessions"]
    await lab_sessions.create_index([("session_id", pymongo.ASCENDING)], unique=True, name="lab_sessions_id_idx")
    await lab_sessions.create_index(
        [("experiment_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
        name="lab_sessions_exp_created_idx",
    )

    lab_reports = database["lab_reports"]
    await lab_reports.create_index(
        [("experiment_id", pymongo.ASCENDING), ("score", pymongo.DESCENDING)],
        name="lab_reports_exp_score_idx",
    )
    log.info("MongoDB indexes ensured.")



async def init_db() -> None:
    """
    Called once at application startup.

    Attempts a Motor connection; falls back to in-memory on any failure.
    Sets the module-level ``database`` and ``STORAGE_MODE`` globals.
    """
    global _mongo_client, database, STORAGE_MODE

    uri = settings.mongodb_uri.strip()

    if not uri:
        log.warning("MONGODB_URI not set – starting in memory-store mode.")
        database = _InMemoryDatabase()
        STORAGE_MODE = "memory"
        await create_indexes()
        await seed_sample_data()
        return


    try:
        from motor.motor_asyncio import AsyncIOMotorClient  # noqa: PLC0415

        client = AsyncIOMotorClient(
            uri,
            serverSelectionTimeoutMS=5_000,
            connectTimeoutMS=5_000,
        )
        # Verify connectivity with a cheap admin ping.
        await client.admin.command("ping")

        _mongo_client = client
        database = client[settings.db_name]
        STORAGE_MODE = "mongodb"
        log.info("Connected to MongoDB Atlas (db=%s).", settings.db_name)
        await create_indexes()

    except Exception as exc:  # noqa: BLE001
        log.warning(
            "MongoDB connection failed (%s) – falling back to memory store.", exc
        )
        database = _InMemoryDatabase()
        STORAGE_MODE = "memory"
        await create_indexes()

    await seed_sample_data()


async def seed_sample_data() -> None:
    """
    Seed initial sample players and scores if scores collection is empty.
    Creates 8 realistic sample student/resident scores across levels.
    """
    scores_col = database["scores"]
    count = await scores_col.count_documents({})
    if count > 0:
        return

    import datetime  # noqa: PLC0415
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    sample_entries = [
        {"nickname": "DrPharm99", "level_id": "level-01", "score": 92, "stars": 3},
        {"nickname": "Alex_Med",   "level_id": "level-01", "score": 86, "stars": 3},
        {"nickname": "Curie_Rx",   "level_id": "level-01", "score": 78, "stars": 2},
        {"nickname": "BioHacker",  "level_id": "level-01", "score": 71, "stars": 2},
        {"nickname": "PharmD_Sam", "level_id": "level-01", "score": 64, "stars": 2},
        {"nickname": "DoseMaster", "level_id": "level-01", "score": 58, "stars": 2},
        {"nickname": "NightNurse", "level_id": "level-01", "score": 50, "stars": 2},
        {"nickname": "RookieRx",   "level_id": "level-01", "score": 38, "stars": 1},
        # Also seed a few for other levels so other filters aren't empty
        {"nickname": "DrPharm99", "level_id": "level-02", "score": 88, "stars": 3},
        {"nickname": "Curie_Rx",   "level_id": "level-02", "score": 81, "stars": 3},
        {"nickname": "NightNurse", "level_id": "level-04", "score": 85, "stars": 3},
    ]

    for item in sample_entries:
        doc = {**item, "is_sample": True, "saved_at": now}
        await scores_col.insert_one(doc)
        await database["players"].update_one(
            {"nickname": item["nickname"]},
            {
                "$set": {"last_seen": now, "is_sample": True},
                "$setOnInsert": {"nickname": item["nickname"], "joined_at": now},
            },
            upsert=True,
        )
    log.info("Seeded %d sample leaderboard scores.", len(sample_entries))



async def close_db() -> None:
    """Close the Motor client if one is open."""
    if _mongo_client is not None:
        _mongo_client.close()
        log.info("MongoDB connection closed.")


# ---------------------------------------------------------------------------
# Run log helpers (Motor + In-Memory unified interface)
# ---------------------------------------------------------------------------

async def insert_run(run_doc: dict[str, Any]) -> None:
    """Insert a simulation run record into the 'runs' collection."""
    await database["runs"].insert_one(run_doc)


async def list_runs(
    module_id: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """List recent simulation runs ordered by created_at descending."""
    filter_dict = {"module_id": module_id} if module_id else {}
    import pymongo  # noqa: PLC0415
    docs = await database["runs"].find(
        filter_dict,
        sort=[("created_at", pymongo.DESCENDING)],
        limit=min(limit, 100),
    )
    # Strip MongoDB internal _id if present
    for d in docs:
        d.pop("_id", None)
    return docs


async def get_run(run_id: str) -> dict[str, Any] | None:
    """Retrieve a single run record by its run_id string."""
    doc = await database["runs"].find_one({"run_id": run_id})
    if doc:
        doc.pop("_id", None)
    return doc


# ---------------------------------------------------------------------------
# Lab Session & Report helpers (Motor + In-Memory unified interface)
# ---------------------------------------------------------------------------

async def upsert_lab_session(session_doc: dict[str, Any]) -> None:
    """Upsert a lab session document by its session_id."""
    doc = dict(session_doc)
    doc.pop("_id", None)
    # Convert sets to lists if present for Mongo serialization
    if "ppe" in doc and isinstance(doc["ppe"], set):
        doc["ppe"] = list(doc["ppe"])
    session_id = doc["session_id"]
    await database["lab_sessions"].update_one(
        {"session_id": session_id},
        {"$set": doc},
        upsert=True,
    )


async def get_lab_session(session_id: str) -> dict[str, Any] | None:
    """Retrieve a lab session by its session_id."""
    doc = await database["lab_sessions"].find_one({"session_id": session_id})
    if doc:
        doc.pop("_id", None)
        if "ppe" in doc and isinstance(doc["ppe"], list):
            doc["ppe"] = set(doc["ppe"])
    return doc


async def save_lab_report(report_doc: dict[str, Any]) -> None:
    """Save a completed lab experiment report to the 'lab_reports' collection."""
    doc = dict(report_doc)
    doc.pop("_id", None)
    await database["lab_reports"].insert_one(doc)


async def list_lab_leaderboard(
    experiment_id: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return top scores for a laboratory experiment."""
    filter_dict = {"experiment_id": experiment_id} if experiment_id else {}
    import pymongo  # noqa: PLC0415
    res = database["lab_reports"].find(
        filter_dict,
        sort=[("score", pymongo.DESCENDING)],
        limit=min(limit, 100),
    )
    if hasattr(res, "to_list"):
        docs = await res.to_list(length=min(limit, 100))
    else:
        docs = await res
    for d in docs:
        d.pop("_id", None)
    return docs


