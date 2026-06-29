"""
KisanMind — Gemini Chat Service
================================
Streams responses from Google Gemini 2.5 Flash using the modern google-genai SDK.
Auto-switches between Account 1 and Account 2 via KeyManager when a rate limit (429)
is detected. Also yields a sources dict before the text stream when web search was used.

Yield protocol:
  - First (optional): dict {"sources": [...]}
  - Then:             str (text chunks)
  - Rate-limit/error: str (localized message)
"""

from google import genai
from google.genai import types
import logging
from system_prompt import KISANMIND_SYSTEM_PROMPT
from services.search_service import needs_search, build_search_query, fetch_search_results, format_search_context
from services.key_manager import key_manager

logger = logging.getLogger("uvicorn.error")

# ── Localised messages ───────────────────────────────────────────────────────

_BOTH_BUSY_MSGS = {
    "te": "సేవ ప్రస్తుతం అందుబాటులో లేదు (రెండు ఖాతాలు బిజీగా ఉన్నాయి). దయచేసి కొన్ని నిమిషాల తర్వాత మళ్ళీ ప్రయత్నించండి. 🙏",
    "hi": "सेवा अभी उपलब्ध नहीं है (दोनों खाते व्यस्त हैं)। कृपया कुछ मिनट बाद पुनः प्रयास करें। 🙏",
    "en": "Service is temporarily busy, please try again in a few minutes. 🙏",
}

_CONN_ERROR_MSGS = {
    "te": "సహాయకుడిని సంప్రదించడంలో సమస్య ఏర్పడింది. దయచేసి మీ ఇంటర్నెట్ కనెక్షన్‌ని సరిచూసుకోండి లేదా మళ్లీ ప్రయత్నించండి.",
    "hi": "सहायक से कनेक्ट करने में समस्या आ रही है। कृपया अपनी इंटरनेट कनेक्टिविटी की जांच करें या पुनः प्रयास करें।",
    "en": "We had trouble connecting to the assistant. Please check your internet connection or try again.",
}


def _localize(msg_dict: dict, language: str) -> str:
    return msg_dict.get(language, msg_dict["en"])


# ── Stream chat ──────────────────────────────────────────────────────────────

async def stream_chat(messages: list, language: str = "en", weather_context: str = ""):
    """
    Async generator that yields:
      1. dict(sources=[...])  — only when web search was used
      2. str chunks           — Gemini response text

    On rate-limit/error, yields a single localized error string.
    """
    lang_instruction = {
        "te": "The farmer is writing in Telugu. Respond ONLY in Telugu.",
        "hi": "The farmer is writing in Hindi. Respond ONLY in Hindi.",
        "en": "Respond in English.",
    }.get(language, "Detect language from the message and respond accordingly.")

    # ── Real-time search augmentation ─────────────────────────────────────────
    search_context = ""
    sources: list[dict] = []
    
    # Bypass search if we already have weather context from OpenWeatherMap
    if not weather_context and messages:
        last_user_msg = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        if last_user_msg and needs_search(last_user_msg):
            query = build_search_query(last_user_msg, language)
            logger.info("🔍 Fetching live search results for: %s", query)
            results = await fetch_search_results(query, num_results=5)
            if results:
                sources = results
                search_context = format_search_context(results, language)
                logger.info("✅ Injected %d search results into context.", len(results))

    # Yield sources metadata first so the frontend can display them
    if sources:
        yield {"sources": sources}

    # Inject weather context if available
    injected_weather = f"\n\nLIVE WEATHER DATA:\n{weather_context}" if weather_context else ""

    system_instruction = (
        f"{KISANMIND_SYSTEM_PROMPT}\n\n"
        f"Current language instruction: {lang_instruction}\n\n"
        f"{injected_weather}\n\n"
        f"{search_context}"
    )

    # Build Gemini contents
    gemini_contents = [
        types.Content(
            role="user" if msg["role"] == "user" else "model",
            parts=[types.Part.from_text(text=msg["content"])],
        )
        for msg in messages
    ]

    config = types.GenerateContentConfig(system_instruction=system_instruction)

    # ── Auto-failover (Account 1 → Account 2 on 429) ─────────────────────────
    for attempt in range(2):
        gemini_key, account_num = key_manager.get_gemini_key()

        if gemini_key is None:
            logger.error("🔴 Both Gemini accounts rate-limited.")
            yield _localize(_BOTH_BUSY_MSGS, language)
            return

        logger.info("🤖 [attempt %d] gemini-1.5-flash via Account %d", attempt + 1, account_num)

        try:
            client = genai.Client(api_key=gemini_key)
            response_stream = await client.aio.models.generate_content_stream(
                model="gemini-1.5-flash",
                contents=gemini_contents,
                config=config,
            )

            async for chunk in response_stream:
                if chunk.text:
                    yield chunk.text

            return  # ✅ Success

        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = any(k in err_str for k in ["429", "quota", "exhausted", "rate", "limit"])

            if is_rate_limit:
                logger.warning("⚠️  Rate-limit on Account %d [gemini]: %s", account_num, e)
                key_manager.report_rate_limit("gemini", account_num)
                if attempt == 0:
                    logger.info("🔄 Retrying with fallback account...")
                    continue
                else:
                    logger.error("🔴 Both Gemini accounts exhausted.")
                    yield _localize(_BOTH_BUSY_MSGS, language)
                    return
            else:
                logger.error("❌ Gemini API Error: %s", e)
                yield _localize(_CONN_ERROR_MSGS, language)
                return
