"""
KisanMind — In-Memory Rate Limiter
====================================
Tracks per-user request counts across per-minute and per-day windows.
No Redis required — pure in-memory with TTL-based cleanup.

Limits (Gemini free tier safe margins):
  - 12 requests / minute  (Gemini free = 15/min)
  - 1400 requests / day   (Gemini free = 1500/day)
"""

import time
from collections import defaultdict

# ── Limits ──────────────────────────────────────────────────────────────────
MAX_PER_MINUTE = 12
MAX_PER_DAY    = 1400
WINDOW_MINUTE  = 60        # seconds
WINDOW_DAY     = 86400     # seconds (24h)

# ── Storage ─────────────────────────────────────────────────────────────────
# {user_id: [timestamp, timestamp, ...]}  — all timestamps within last 24h
_request_log: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(user_id: str) -> dict:
    """
    Check if the given user_id is within rate limits.
    Records the new request if allowed.

    Returns:
        {
            "allowed": True,
            "used_today": int,
            "used_minute": int,
            "limit_day": int,
            "limit_minute": int,
        }
        or
        {
            "allowed": False,
            "type": "minute" | "day",
            "reset_at": int,          # milliseconds epoch
            "used_today": int,
            "limit_day": int,
        }
    """
    now = time.time()
    minute_cutoff = now - WINDOW_MINUTE
    day_cutoff    = now - WINDOW_DAY

    # Prune old entries (older than 24h)
    _request_log[user_id] = [t for t in _request_log[user_id] if t > day_cutoff]

    all_today   = _request_log[user_id]
    last_minute = [t for t in all_today if t > minute_cutoff]

    used_today  = len(all_today)
    used_minute = len(last_minute)

    # Check per-minute limit
    if used_minute >= MAX_PER_MINUTE:
        # Reset time = oldest request in the minute window + 60s
        reset_at = int((last_minute[0] + WINDOW_MINUTE) * 1000)
        return {
            "allowed":    False,
            "type":       "minute",
            "reset_at":   reset_at,
            "used_today": used_today,
            "limit_day":  MAX_PER_DAY,
        }

    # Check per-day limit
    if used_today >= MAX_PER_DAY:
        reset_at = int((all_today[0] + WINDOW_DAY) * 1000)
        return {
            "allowed":    False,
            "type":       "day",
            "reset_at":   reset_at,
            "used_today": used_today,
            "limit_day":  MAX_PER_DAY,
        }

    # ✅ Allowed — record this request
    _request_log[user_id].append(now)
    return {
        "allowed":      True,
        "used_today":   used_today + 1,
        "used_minute":  used_minute + 1,
        "limit_day":    MAX_PER_DAY,
        "limit_minute": MAX_PER_MINUTE,
    }


def get_usage(user_id: str) -> dict:
    """Return current usage stats without recording a new request."""
    now = time.time()
    day_cutoff    = now - WINDOW_DAY
    minute_cutoff = now - WINDOW_MINUTE
    log = [t for t in _request_log.get(user_id, []) if t > day_cutoff]
    return {
        "used_today":   len(log),
        "used_minute":  len([t for t in log if t > minute_cutoff]),
        "limit_day":    MAX_PER_DAY,
        "limit_minute": MAX_PER_MINUTE,
    }
