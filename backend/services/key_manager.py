"""
KisanMind — Multi-Account API Key Manager
==========================================
Automatically rotates between Account 1 (sowryansamalla) and Account 2
(jayaprakashsamalla) when rate limits are hit on any service.

Priority:
  - Account 1 is always preferred (primary).
  - Falls back to Account 2 when Account 1 is cooling down.
  - Auto-resets back to Account 1 once its cooldown expires.
  - Returns (None, None) / (None, None, None) if both are cooling down,
    which callers convert to a user-facing "service busy" message.

Cooldown: 60 seconds after a rate-limit is reported.
"""

import os
import time
import logging
from collections import defaultdict
from typing import Optional

logger = logging.getLogger("uvicorn.error")

# ── Config ─────────────────────────────────────────────────────────────────
RATE_LIMIT_COOLDOWN_SECS = 60   # seconds before retrying a rate-limited account

ACCOUNT_NAMES = {
    1: "Account 1 (sowryansamalla)",
    2: "Account 2 (jayaprakashsamalla)",
}


class KeyManager:
    """
    Thread-safe (GIL-protected reads/writes on dicts are atomic in CPython)
    singleton that manages per-service, per-account key rotation.
    """

    def __init__(self):
        # Load both accounts' credentials from environment
        self.accounts: dict[int, dict[str, str]] = {
            1: {
                "gemini_key":          os.getenv("ACC1_GEMINI_API_KEY", ""),
                "groq_key":            os.getenv("ACC1_GROQ_API_KEY", ""),
                "google_search_key":   os.getenv("ACC1_GOOGLE_SEARCH_API_KEY", ""),
                "google_cse_id":       os.getenv("ACC1_GOOGLE_CSE_ID", ""),
                "weather_key":         os.getenv("ACC1_OPENWEATHER_API_KEY", ""),
                "supabase_url":        os.getenv("ACC1_SUPABASE_URL", ""),
                "supabase_anon_key":   os.getenv("ACC1_SUPABASE_ANON_KEY", ""),
                "supabase_service_key": os.getenv("ACC1_SUPABASE_SERVICE_KEY", ""),
            },
            2: {
                "gemini_key":          os.getenv("ACC2_GEMINI_API_KEY", ""),
                "groq_key":            os.getenv("ACC2_GROQ_API_KEY", ""),
                "google_search_key":   os.getenv("ACC2_GOOGLE_SEARCH_API_KEY", ""),
                "google_cse_id":       os.getenv("ACC2_GOOGLE_CSE_ID", ""),
                "weather_key":         os.getenv("ACC2_OPENWEATHER_API_KEY", ""),
                "supabase_url":        os.getenv("ACC2_SUPABASE_URL", ""),
                "supabase_anon_key":   os.getenv("ACC2_SUPABASE_ANON_KEY", ""),
                "supabase_service_key": os.getenv("ACC2_SUPABASE_SERVICE_KEY", ""),
            },
        }

        # {account_num: {service_name: monotonic_timestamp_when_rate_limited}}
        self._rate_limited_at: dict[int, dict[str, float]] = {1: {}, 2: {}}

        logger.info(
            "🔑 KeyManager ready | Primary: %s | Fallback: %s",
            ACCOUNT_NAMES[1], ACCOUNT_NAMES[2],
        )

    # ──────────────────────────────── Internals ────────────────────────────

    def _is_cooling_down(self, account: int, service: str) -> bool:
        """True while the account is within its rate-limit cooldown window."""
        ts = self._rate_limited_at[account].get(service)
        if ts is None:
            return False
        return (time.monotonic() - ts) < RATE_LIMIT_COOLDOWN_SECS

    def _resolve_account(self, service: str) -> Optional[int]:
        """
        Pick the best available account for a service:
          1. Prefer Account 1 (and auto-reset back to it when its cooldown expires).
          2. Fall back to Account 2 while Account 1 is cooling.
          3. Return None if both are cooling (both rate-limited).
        """
        acc1_cooling = self._is_cooling_down(1, service)
        acc2_cooling = self._is_cooling_down(2, service)

        if not acc1_cooling:
            # Account 1 available — log a switch-back if we were on Account 2
            if self._rate_limited_at[1].get(service) is not None:
                # We were previously rate-limited but cooldown expired
                logger.info(
                    "🔄 [%s] Account 1 cooldown expired — reverting to primary (%s).",
                    service, ACCOUNT_NAMES[1],
                )
            return 1

        if not acc2_cooling:
            logger.info(
                "🟡 [%s] Account 1 rate-limited, using fallback (%s).",
                service, ACCOUNT_NAMES[2],
            )
            return 2

        logger.error(
            "🔴 [%s] BOTH accounts rate-limited! Service temporarily unavailable.",
            service,
        )
        return None  # caller must show "service busy" message

    # ──────────────────────────────── Public API ───────────────────────────

    def report_rate_limit(self, service: str, account: int):
        """
        Call this immediately after a 429 / quota-exhausted error.
        Marks the account as cooling-down for RATE_LIMIT_COOLDOWN_SECS.
        """
        self._rate_limited_at[account][service] = time.monotonic()
        logger.warning(
            "⚠️  Rate-limit reported: [%s] on %s — cooling down for %ds.",
            service, ACCOUNT_NAMES[account], RATE_LIMIT_COOLDOWN_SECS,
        )

    # ── Gemini ──────────────────────────────────────────────────────────────

    def get_gemini_key(self) -> tuple[Optional[str], Optional[int]]:
        """
        Returns (api_key, account_num).
        Returns (None, None) if both accounts are rate-limited or unconfigured.
        """
        account = self._resolve_account("gemini")
        if account is None:
            return None, None
        key = self.accounts[account]["gemini_key"]
        if not key:
            logger.warning("⚠️  [gemini] %s has no Gemini key configured.", ACCOUNT_NAMES[account])
            return None, None
        logger.info("🔑 [gemini] Active account: %s", ACCOUNT_NAMES[account])
        return key, account

    # ── GROQ ────────────────────────────────────────────────────────────────

    def get_groq_key(self) -> tuple[Optional[str], Optional[int]]:
        """Returns (api_key, account_num) or (None, None)."""
        account = self._resolve_account("groq")
        if account is None:
            return None, None
        key = self.accounts[account]["groq_key"]
        if not key:
            return None, None
        return key, account

    # ── Google Search ────────────────────────────────────────────────────────

    def get_search_creds(self) -> tuple[Optional[str], Optional[str], Optional[int]]:
        """
        Returns (google_search_api_key, cse_id, account_num).
        Returns (None, None, None) if both accounts are rate-limited.
        """
        account = self._resolve_account("search")
        if account is None:
            return None, None, None
        creds = self.accounts[account]
        logger.info("🔍 [search] Active account: %s (CSE: %s)", ACCOUNT_NAMES[account], creds["google_cse_id"])
        return creds["google_search_key"], creds["google_cse_id"], account

    # ── Weather ─────────────────────────────────────────────────────────────

    def get_weather_key(self) -> tuple[Optional[str], Optional[int]]:
        """Returns (openweather_api_key, account_num) or (None, None)."""
        account = self._resolve_account("weather")
        if account is None:
            return None, None
        return self.accounts[account]["weather_key"], account

    # ── Supabase ────────────────────────────────────────────────────────────

    def get_supabase_creds(self) -> tuple[Optional[str], Optional[str], Optional[str], Optional[int]]:
        """
        Returns (supabase_url, anon_key, service_key, account_num).
        Returns (None, None, None, None) if both accounts are unavailable.
        """
        account = self._resolve_account("supabase")
        if account is None:
            return None, None, None, None
        creds = self.accounts[account]
        return (
            creds["supabase_url"],
            creds["supabase_anon_key"],
            creds["supabase_service_key"],
            account,
        )

    # ── Diagnostics ─────────────────────────────────────────────────────────

    def status(self) -> dict:
        """Return current active accounts per service (for health endpoint / logging)."""
        services = ["gemini", "groq", "search", "weather", "supabase"]
        result = {}
        for svc in services:
            acc = self._resolve_account.__func__(self, svc)  # type: ignore[attr-defined]
            result[svc] = ACCOUNT_NAMES.get(acc, "BOTH RATE-LIMITED") if acc else "BOTH RATE-LIMITED"
        return result


# ── Singleton ──────────────────────────────────────────────────────────────
key_manager = KeyManager()
