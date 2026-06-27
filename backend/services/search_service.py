"""
KisanMind — Google Custom Search Service
=========================================
Fetches real-time web results to augment AI responses with live data
(mandi prices, weather, news, government schemes, pest alerts, etc.).

Key rotation: uses KeyManager to auto-switch between Account 1 and Account 2
Google CSE credentials when a search API quota / 429 error occurs.
"""

import asyncio
import logging
import traceback

logger = logging.getLogger("uvicorn.error")

# Keywords that strongly indicate the user needs live / real-time data
SEARCH_TRIGGER_KEYWORDS = [
    # Prices & markets
    "price", "rate", "mandi", "market", "rates", "cost", "ధర", "ధరలు",
    "మండి", "ఖర్చు", "కీమత్", "కీమతు", "कीमत", "भाव", "मंडी", "दर",
    # Weather
    "weather", "rain", "forecast", "temperature", "climate", "వాతావరణం",
    "వర్షం", "వేడి", "मौसम", "बारिश", "तापमान",
    # News & current events
    "news", "today", "current", "latest", "recent", "now", "update",
    "నేడు", "తాజా", "ప్రస్తుత", "आज", "ताजा", "अभी",
    # Government & schemes
    "scheme", "subsidy", "yojana", "pm kisan", "government", "policy",
    "పథకం", "సబ్సిడీ", "ప్రభుత్వం", "योजना", "सरकार", "सब्सिडी",
    # Pest & disease alerts
    "pest", "disease", "attack", "outbreak", "alert", "తెగులు",
    "రోగం", "దాడి", "कीट", "बीमारी", "हमला",
    # Seasons & crop calendar
    "season", "kharif", "rabi", "zaid", "sowing", "harvest",
]


def _needs_search(user_message: str) -> bool:
    """Return True if the message contains any real-time keywords."""
    lower = user_message.lower()
    return any(kw in lower for kw in SEARCH_TRIGGER_KEYWORDS)


def _build_search_query(user_message: str, language: str) -> str:
    """Enhance query with concise terms to avoid search over-filtering."""
    query = user_message.lower()

    fillers = [
        "please", "tell me", "what is", "what are", "show me", "can you",
        "i want to know", "how to", "do you know", "today", "today's",
        "దయచేసి", "చెప్పండి", "నాకు", "తెలుసుకోవాలి", "कृपया", "बताएं", "मुझे",
    ]
    for word in fillers:
        query = query.replace(word, "")

    query = query.strip("? .!/,;").strip()
    if not query:
        query = user_message.strip("? .!/,;")

    location_keywords = [
        "india", "andhra", "telangana", "guntur", "kurnool", "nellore",
        "కరీంనగర్", "గుంటూరు", "వరంగల్", "ఆంధ్ర", "తెలంగాణ", "భారత్", "భారత",
        "भारत",
    ]
    if not any(loc in query for loc in location_keywords):
        if language == "te":
            return f"{query} Andhra Pradesh Telangana"
        else:
            return f"{query} India"

    return query


async def fetch_search_results(query: str, num_results: int = 5) -> list[dict]:
    """
    Run a Google Custom Search query and return a list of result dicts.
    Uses KeyManager to pick the best available account credentials.
    Falls back to DuckDuckGo if Google Custom Search fails or is rate-limited.

    Each dict has: title, link, snippet.
    """
    from services.key_manager import key_manager

    loop = asyncio.get_event_loop()

    # ── 1. Google Custom Search via KeyManager (with per-account failover) ──
    for attempt in range(2):
        api_key, cse_id, account_num = key_manager.get_search_creds()
        if api_key and cse_id:
            try:
                logger.info(
                    "🔍 Google Custom Search (Account %d, CSE: %s)...",
                    account_num, cse_id,
                )
                results = await loop.run_in_executor(
                    None,
                    lambda k=api_key, c=cse_id: _sync_google_search(query, num_results, k, c),
                )
                if results:
                    logger.info(
                        "✅ Google Custom Search returned %d results (Account %d).",
                        len(results), account_num,
                    )
                    return results
                logger.warning("Google Custom Search returned empty results (Account %d).", account_num)
                break  # empty ≠ rate limit; don't retry on the other account
            except Exception as e:
                err_str = str(e)
                is_quota = "429" in err_str or "quota" in err_str.lower() or "403" in err_str
                logger.warning(
                    "Google Custom Search Account %d failed: %s\n%s",
                    account_num, e, traceback.format_exc(),
                )
                if is_quota and attempt == 0:
                    logger.warning("Quota error — reporting to KeyManager and retrying with Account 2.")
                    key_manager.report_rate_limit("search", account_num)
                    continue
                break  # non-quota error or both accounts failed
        else:
            logger.warning("No search credentials available from KeyManager.")
            break

    # ── 2. DuckDuckGo fallback ───────────────────────────────────────────────
    try:
        logger.info("Performing DuckDuckGo Search fallback...")
        results = await loop.run_in_executor(
            None,
            lambda: _ddg_search(query, num_results),
        )
        return results
    except Exception as e:
        logger.error("DuckDuckGo Search fallback error: %s\n%s", e, traceback.format_exc())
        return []


def _sync_google_search(query: str, num_results: int, api_key: str, cse_id: str) -> list[dict]:
    """Synchronous Google Custom Search call (runs in executor thread)."""
    from googleapiclient.discovery import build
    service = build("customsearch", "v1", developerKey=api_key)
    response = service.cse().list(q=query, cx=cse_id, num=num_results).execute()
    items = response.get("items", [])
    return [
        {
            "title": item.get("title", ""),
            "link":  item.get("link", ""),
            "snippet": item.get("snippet", ""),
        }
        for item in items
    ]


def _ddg_search(query: str, num_results: int) -> list[dict]:
    """Synchronous DuckDuckGo Search with HTML → Lite → default text fallback chain."""
    from duckduckgo_search import DDGS

    with DDGS() as ddgs:
        # HTML backend
        try:
            logger.info("DuckDuckGo HTML backend...")
            res = ddgs._text_html(query, max_results=num_results)
            if res:
                logger.info("DDG HTML backend: %d results.", len(res))
                return [{"title": r.get("title", ""), "link": r.get("href", ""), "snippet": r.get("body", "")} for r in res]
        except Exception as e:
            logger.warning("DDG HTML backend failed: %s", e)

        # Lite backend
        try:
            logger.info("DuckDuckGo Lite backend...")
            res = ddgs._text_lite(query, max_results=num_results)
            if res:
                logger.info("DDG Lite backend: %d results.", len(res))
                return [{"title": r.get("title", ""), "link": r.get("href", ""), "snippet": r.get("body", "")} for r in res]
        except Exception as e:
            logger.warning("DDG Lite backend failed: %s", e)

        # Default text backend
        try:
            logger.info("DuckDuckGo default text backend...")
            res = ddgs.text(query, max_results=num_results)
            if res:
                logger.info("DDG default text backend: %d results.", len(res))
                return [{"title": r.get("title", ""), "link": r.get("href", ""), "snippet": r.get("body", "")} for r in res]
        except Exception as e:
            logger.warning("DDG default text backend failed: %s", e)

    return []


def format_search_context(results: list[dict], language: str) -> str:
    """Convert search results into a clean text block to inject into the prompt."""
    if not results:
        return ""

    if language == "te":
        header = "📡 తాజా వెబ్ సమాచారం (Google నుండి):\n"
    elif language == "hi":
        header = "📡 ताज़ा वेब जानकारी (Google से):\n"
    else:
        header = "📡 Latest web information (from Google Search):\n"

    lines = [header]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. **{r['title']}**")
        lines.append(f"   {r['snippet']}")
        lines.append(f"   Source: {r['link']}\n")

    lines.append(
        "\n[Use the above live search results to answer the farmer's question accurately. "
        "Cite sources where relevant. Do NOT mention that you searched the web — just answer naturally.]\n"
    )
    return "\n".join(lines)


# ── Public API aliases ────────────────────────────────────────────────────────
needs_search = _needs_search
build_search_query = _build_search_query

__all__ = [
    "needs_search", "build_search_query",
    "fetch_search_results", "format_search_context",
]
