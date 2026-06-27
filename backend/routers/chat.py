from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from services.claude_service import stream_chat
from services.rate_limiter import check_rate_limit
from services.weather_service import get_weather
from models.chat import ChatRequest
import json
import re
import logging

router = APIRouter()
logger = logging.getLogger("uvicorn.error")

def extract_location_from_message(text: str) -> str | None:
    """Extract place name from weather questions."""
    patterns = [
        r'(?:weather|temperature|temp|వాతావరణ|ఉష్ణోగ్రత|मौसम|तापमान).*?(?:in|at|of|లో|में)\s+(.+?)(?:\?|$)',
        r'(.+?)\s+(?:weather|temperature|temp|వాతావరణ|ఉష్ణోగ్రత)',
        r'(?:in|at)\s+(.+?)\s+(?:village|mandal|district|గ్రామం|మండలం)',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


@router.post("/stream")
async def chat_stream(req: ChatRequest, request: Request):
    """Stream AI farming advice response with rate limiting."""

    # Use IP as anonymous user ID if no user_id provided
    user_id = req.user_id or request.client.host or "anon"

    # Check rate limit before streaming
    limit = check_rate_limit(user_id)
    if not limit["allowed"]:
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limited",
                "type": limit["type"],
                "reset_at": limit["reset_at"],
                "used_today": limit["used_today"],
                "limit_day": limit["limit_day"],
                "message": "Rate limit reached. Please wait.",
            }
        )

    messages = [m.model_dump() for m in req.messages]
    last_user_msg = messages[-1]["content"] if messages else ""

    # Weather extraction & injection
    weather_context = ""
    is_weather_query = any(w in last_user_msg.lower() for w in ["weather", "temperature", "temp", "forecast", "rain", "వాతావరణ", "ఉష్ణోగ్రత", "मौसम", "तापमान"])
    
    if is_weather_query:
        location = extract_location_from_message(last_user_msg)
        target_location = location or req.district or "Kurnool"
        try:
            weather_context = await get_weather(target_location)
            logger.info(f"☀️ Injected OWM weather context for location: {target_location}")
        except Exception as e:
            logger.error(f"Error fetching weather context for {target_location}: {e}")

    async def generate():
        sources_sent = False
        async for payload in stream_chat(messages, req.language, weather_context=weather_context):
            if isinstance(payload, dict):
                # Sources payload — send once
                if not sources_sent:
                    yield f"data: {json.dumps({'sources': payload.get('sources', [])})}\n\n"
                    sources_sent = True
            else:
                # Text chunk
                data = {
                    "text": payload,
                    "used_today": limit["used_today"],
                    "limit_day": limit["limit_day"],
                }
                yield f"data: {json.dumps(data)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/incognito")
async def chat_incognito(req: ChatRequest, request: Request):
    """Incognito chat — no DB save, still rate-limited."""
    user_id = req.user_id or request.client.host or "anon"
    limit = check_rate_limit(user_id)
    if not limit["allowed"]:
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limited",
                "type": limit["type"],
                "reset_at": limit["reset_at"],
                "used_today": limit["used_today"],
                "limit_day": limit["limit_day"],
            }
        )

    messages = [m.model_dump() for m in req.messages]
    last_user_msg = messages[-1]["content"] if messages else ""

    # Weather extraction & injection
    weather_context = ""
    is_weather_query = any(w in last_user_msg.lower() for w in ["weather", "temperature", "temp", "forecast", "rain", "వాతావరణ", "ఉష్ణోగ్రత", "मौसम", "तापमान"])
    
    if is_weather_query:
        location = extract_location_from_message(last_user_msg)
        target_location = location or req.district or "Kurnool"
        try:
            weather_context = await get_weather(target_location)
            logger.info(f"☀️ Injected OWM weather context for location: {target_location}")
        except Exception as e:
            logger.error(f"Error fetching weather context for {target_location}: {e}")

    async def generate():
        async for payload in stream_chat(messages, req.language, weather_context=weather_context):
            if isinstance(payload, dict):
                yield f"data: {json.dumps({'sources': payload.get('sources', [])})}\n\n"
            else:
                yield f"data: {json.dumps({'text': payload})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
