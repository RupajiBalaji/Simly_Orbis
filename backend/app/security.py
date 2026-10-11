"""
RC1 Hardening, Abuse Protection & Security Middleware Utilities.
Provides in-memory per-IP rate limiting, AI daily call caps, text sanitization,
and startup configuration validation without leaking secrets.
"""

from __future__ import annotations

import logging
import re
import time
from datetime import date
from typing import Dict, Tuple

from app.config import settings

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. In-Memory Per-IP Token Bucket Rate Limiter
# ---------------------------------------------------------------------------

class TokenBucket:
    """Token bucket for smooth rate limiting."""

    def __init__(self, capacity: float, refill_rate: float) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_update = time.time()

    def consume(self, cost: float = 1.0) -> bool:
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False


class RateLimiter:
    """
    In-memory rate limiter keeping buckets per (IP, category).
    - General: 120 req / min
    - AI (mentor/tutor): 10 req / min
    - Sessions (POST /api/lab/sessions): 20 req / min
    """

    LIMITS = {
        "general": (120.0, 120.0 / 60.0),   # (capacity, refill_per_sec)
        "ai": (10.0, 10.0 / 60.0),
        "session_create": (20.0, 20.0 / 60.0),
    }

    def __init__(self) -> None:
        self._buckets: Dict[Tuple[str, str], TokenBucket] = {}
        self._last_cleanup = time.time()

    def check(self, ip: str, category: str = "general") -> bool:
        self._maybe_cleanup()
        cap, rate = self.LIMITS.get(category, self.LIMITS["general"])
        key = (ip, category)
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(capacity=cap, refill_rate=rate)
        return self._buckets[key].consume(1.0)

    def _maybe_cleanup(self) -> None:
        now = time.time()
        # Clean up stale buckets every 5 minutes
        if now - self._last_cleanup > 300:
            self._last_cleanup = now
            stale_keys = [
                k for k, b in self._buckets.items()
                if (now - b.last_update) > 120
            ]
            for k in stale_keys:
                self._buckets.pop(k, None)


rate_limiter = RateLimiter()


# ---------------------------------------------------------------------------
# 2. AI Global Daily Cap Tracker & Switch
# ---------------------------------------------------------------------------

class AIDailyCapTracker:
    """
    Enforces global daily cap from MENTOR_DAILY_CAP (default 300).
    Also respects AI_ENABLED env flag.
    """

    def __init__(self) -> None:
        self._current_date = date.today().isoformat()
        self._call_count = 0

    def can_call_ai(self) -> Tuple[bool, str]:
        """
        Check if an AI call is permitted.
        Returns (is_allowed, reason_if_blocked).
        """
        if not settings.ai_enabled:
            return False, "ai_disabled"

        today = date.today().isoformat()
        if today != self._current_date:
            self._current_date = today
            self._call_count = 0

        if self._call_count >= settings.mentor_daily_cap:
            return False, "daily_cap_exceeded"

        return True, ""

    def record_call(self) -> None:
        self._call_count += 1

    def get_status(self) -> dict:
        today = date.today().isoformat()
        if today != self._current_date:
            self._current_date = today
            self._call_count = 0

        return {
            "ai_enabled": settings.ai_enabled,
            "calls_today": self._call_count,
            "daily_cap": settings.mentor_daily_cap,
            "remaining": max(0, settings.mentor_daily_cap - self._call_count),
        }

    def reset_for_test(self, count: int = 0) -> None:
        self._current_date = date.today().isoformat()
        self._call_count = count


ai_cap_tracker = AIDailyCapTracker()


# ---------------------------------------------------------------------------
# 3. Text Sanitization & Truncation
# ---------------------------------------------------------------------------

_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

def sanitize_text(text: str | None, max_length: int) -> str:
    """
    Strips control characters, normalizes whitespace, and truncates text.
    - Nicknames: max 24
    - Label text: max 60
    - Mentor question: max 200
    """
    if text is None:
        return ""
    # Strip dangerous ASCII control characters
    cleaned = _CONTROL_CHAR_RE.sub("", str(text))
    # Truncate to maximum permitted length
    return cleaned[:max_length].strip()


# ---------------------------------------------------------------------------
# 4. Startup Configuration Validation (Never Prints Secrets)
# ---------------------------------------------------------------------------

def validate_startup_config() -> None:
    """Logs startup configuration safely without printing secret values."""
    has_mongo = bool(settings.mongodb_uri.strip())
    has_anthropic = bool(settings.anthropic_api_key.strip())
    has_gemini = bool(settings.gemini_api_key.strip())

    log.info("=== ORBIS LAB CONFIGURATION VALIDATION ===")
    log.info("App Version:       %s", settings.app_version)
    log.info("Git SHA:           %s", settings.git_sha or "[NOT SET]")
    log.info("Database:          %s", "MongoDB URI configured" if has_mongo else "In-Memory Fallback")
    log.info("Gemini Key:        %s", f"[SET: {settings.gemini_model}]" if has_gemini else "[UNSET]")
    log.info("Anthropic Key:     %s", f"[SET: {settings.anthropic_model}]" if has_anthropic else "[UNSET]")
    active_ai = f"Gemini ({settings.gemini_model})" if has_gemini else (f"Anthropic ({settings.anthropic_model})" if has_anthropic else "Rule-based (No AI key configured)")
    log.info("Active AI Mentor:  %s", active_ai)
    log.info("AI Enabled:        %s", settings.ai_enabled)
    log.info("Trust Proxy:       %s", settings.trust_proxy)
    log.info("Mentor Daily Cap:  %d calls/day", settings.mentor_daily_cap)
    log.info("Allowed Origins:   %s", settings.allowed_origins)
    log.info("==========================================")
