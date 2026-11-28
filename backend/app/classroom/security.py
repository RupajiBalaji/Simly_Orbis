"""
Classroom security utilities (13.6):
- SHA-256 secret hashing and constant-time comparison
- Unambiguous join code & cryptographic token generation
- Nickname filter (profanity, PII/email/phone, length, sanitization)
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone

_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

_PROFANITY_TERMS = {
    "fuck", "shit", "bitch", "asshole", "bastard", "dick", "cock", "pussy",
    "cunt", "whore", "slut", "fag", "faggot", "nigger", "nigga", "retard",
    "motherfucker", "bullshit", "damn", "crap", "porn", "sex", "nazi",
}


def hash_secret(value: str) -> str:
    """Return lowercase SHA-256 hex digest of a secret/code/token."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def constant_time_equals(a: str, b: str) -> bool:
    """Constant-time string comparison for codes and tokens."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def normalize_join_code(code: str) -> str:
    """Normalize a class join code (strip whitespace/hyphens, uppercase)."""
    return re.sub(r"[\s-]+", "", (code or "").strip().upper())


def generate_join_code(length: int = 6) -> str:
    """Generate a random unambiguous uppercase join code."""
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))


def generate_token() -> str:
    """Generate a URL-safe cryptographic bearer token."""
    return secrets.token_urlsafe(32)


def expiry_iso(*, minutes: int = 0, hours: int = 0, days: int = 0) -> str:
    """Return UTC ISO-8601 expiration timestamp."""
    delta = timedelta(minutes=minutes, hours=hours, days=days)
    return (datetime.now(timezone.utc) + delta).isoformat()


def is_expired(iso_ts: str | None) -> bool:
    """Return True if an ISO-8601 timestamp is missing, invalid, or in the past."""
    if not iso_ts:
        return True
    try:
        dt = datetime.fromisoformat(iso_ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt <= datetime.now(timezone.utc)
    except ValueError:
        return True


def validate_nickname(raw: str) -> tuple[bool, str]:
    """
    Validate and normalize a student nickname (G10, 13.5).
    Rejects empty/short/long names, emails, phone numbers, URLs, HTML, and profanity.
    Returns (True, cleaned_nickname) or (False, error_message).
    """
    if not isinstance(raw, str):
        return False, "Nickname must be text."
    cleaned = re.sub(r"\s+", " ", raw.strip())
    if len(cleaned) < 2 or len(cleaned) > 24:
        return False, "Nickname must be between 2 and 24 characters."
    if "@" in cleaned:
        return False, "Do not use an email address as a nickname."
    if re.search(r"https?://|www\.", cleaned, re.IGNORECASE):
        return False, "URLs are not allowed in nicknames."
    if re.search(r"[<>\"'`]", cleaned):
        return False, "Nickname contains disallowed characters."
    digits_only = re.sub(r"\D", "", cleaned)
    if len(digits_only) >= 7:
        return False, "Do not include phone numbers or long ID numbers in nicknames."
    if not re.match(r"^[A-Za-z0-9 _.-]+$", cleaned):
        return False, "Nickname may only contain letters, numbers, spaces, '.', '_', and '-'."

    # Check whole-token profanity after splitting on separators and normalizing leetspeak per token.
    # We deliberately do NOT search the full collapsed string to avoid false positives
    # on names like "Essex" (contains "sex") or "Dickens" (contains "dick").
    lowered = cleaned.lower()
    leet_map = str.maketrans("013457", "oieast")
    tokens = re.split(r"[\s._-]+", lowered)
    for tok in tokens:
        if tok in _PROFANITY_TERMS or tok.translate(leet_map) in _PROFANITY_TERMS:
            return False, "Please choose a classroom-appropriate nickname."

    return True, cleaned
