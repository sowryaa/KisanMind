from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
from fastapi.responses import StreamingResponse, JSONResponse
from services.claude_service import stream_chat
from services.rate_limiter import check_rate_limit
from services.key_manager import key_manager
from services.weather_service import get_weather
from services.soil_service import get_location_farm_data
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
    is_soil_query = any(w in last_user_msg.lower() for w in ["soil", "matti", "మట్టి", "ph", "fertilizer", "ఎరువు", "nitrogen", "నత్రజని", "land", "భూమి"])
    
    if is_weather_query:
        location = extract_location_from_message(last_user_msg)
        target_location = location or req.district or "Kurnool"
        try:
            weather_context = await get_weather(target_location)
            logger.info(f"☀️ Injected OWM weather context for location: {target_location}")
        except Exception as e:
            logger.error(f"Error fetching weather context for {target_location}: {e}")
    
    if is_soil_query and not weather_context:
        location = extract_location_from_message(last_user_msg)
        target_location = location or req.district or "Kurnool"
        try:
            weather_context = await get_location_farm_data(target_location)
            logger.info(f"🌱 Injected soil+weather context for: {target_location}")
        except Exception as e:
            logger.error(f"Error fetching soil context: {e}")

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
    is_soil_query = any(w in last_user_msg.lower() for w in ["soil", "matti", "మట్టి", "ph", "fertilizer", "ఎరువు", "nitrogen", "నత్రజని", "land", "భూమి"])
    
    if is_weather_query:
        location = extract_location_from_message(last_user_msg)
        target_location = location or req.district or "Kurnool"
        try:
            weather_context = await get_weather(target_location)
            logger.info(f"☀️ Injected OWM weather context for location: {target_location}")
        except Exception as e:
            logger.error(f"Error fetching weather context for {target_location}: {e}")
    
    if is_soil_query and not weather_context:
        location = extract_location_from_message(last_user_msg)
        target_location = location or req.district or "Kurnool"
        try:
            weather_context = await get_location_farm_data(target_location)
            logger.info(f"🌱 Injected soil+weather context for: {target_location}")
        except Exception as e:
            logger.error(f"Error fetching soil context: {e}")

    async def generate():
        async for payload in stream_chat(messages, req.language, weather_context=weather_context):
            if isinstance(payload, dict):
                yield f"data: {json.dumps({'sources': payload.get('sources', [])})}\n\n"
            else:
                yield f"data: {json.dumps({'text': payload})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


class ImageAnalysisRequest(BaseModel):
    image_base64: str
    language: str = "te"
    user_id: Optional[str] = None

@router.post("/analyze-image")
async def analyze_image(req: ImageAnalysisRequest, request: Request):
    """Analyze crop image for diseases, pests, nutrient deficiencies."""
    from pydantic import BaseModel
    from typing import Optional
    import base64

    user_id = req.user_id or request.client.host or "anon"
    limit = check_rate_limit(user_id)
    if not limit["allowed"]:
        return JSONResponse(status_code=429, content={"error": "rate_limited"})

    lang_instruction = {
        "te": "Respond ONLY in Telugu.",
        "hi": "Respond ONLY in Hindi.",
        "en": "Respond in English.",
    }.get(req.language, "Respond in English.")

    prompt = f"""You are KisanMind, an expert AI farming assistant for Indian farmers.
A farmer has shared a photo of their crop. Analyze this image carefully and provide:

1. **వ్యాధి/తెగులు గుర్తింపు** (Disease/Pest Identification): What disease, pest, or deficiency do you see?
2. **లక్షణాలు** (Symptoms): Describe what you observe in the image
3. **కారణాలు** (Causes): What causes this problem?
4. **పరిష్కారాలు** (Solutions): Specific treatments and remedies
5. **నివారణ** (Prevention): How to prevent this in future

{lang_instruction}
Be practical and specific to Indian farming conditions."""

    gemini_key, account_num = key_manager.get_gemini_key()
    if not gemini_key:
        return JSONResponse(status_code=503, content={"error": "Service busy"})

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=gemini_key)
        image_bytes = base64.b64decode(req.image_base64)

        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                types.Part.from_text(text=prompt),
            ],
        )
        return {"analysis": response.text, "status": "success"}
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


class SoilAnalysisRequest(BaseModel):
    image_base64: str
    language: str = "te"
    user_id: Optional[str] = None

@router.post("/analyze-soil")
async def analyze_soil(req: SoilAnalysisRequest, request: Request):
    """Analyze soil test report image and give fertilizer recommendations."""
    import base64

    user_id = req.user_id or request.client.host or "anon"
    limit = check_rate_limit(user_id)
    if not limit["allowed"]:
        return JSONResponse(status_code=429, content={"error": "rate_limited"})

    lang_instruction = {
        "te": "Respond ONLY in Telugu.",
        "hi": "Respond ONLY in Hindi.",
        "en": "Respond in English.",
    }.get(req.language, "Respond in English.")

    prompt = f"""You are KisanMind, an expert soil scientist and farming advisor for Indian farmers.
A farmer has shared their soil test report. Analyze it carefully and provide:

1. **మట్టి స్థితి సారాంశం** (Soil Health Summary): Overall soil health status
2. **పోషక విశ్లేషణ** (Nutrient Analysis): 
   - నత్రజని (Nitrogen/N): Level and interpretation
   - భాస్వరం (Phosphorus/P): Level and interpretation  
   - పొటాష్ (Potassium/K): Level and interpretation
   - pH విలువ: Acidic/Neutral/Alkaline and implications
   - సేంద్రియ కర్బనం (Organic Carbon): Level
3. **ఎరువుల సిఫార్సు** (Fertilizer Recommendations): 
   - Specific fertilizers with exact quantities per acre
   - When and how to apply
4. **సరైన పంటలు** (Suitable Crops): Which crops grow best in this soil
5. **మట్టి మెరుగుదల** (Soil Improvement Tips): How to improve soil health

{lang_instruction}
Be specific with quantities in kg/acre. Consider Indian farming conditions and locally available fertilizers."""

    gemini_key, account_num = key_manager.get_gemini_key()
    if not gemini_key:
        return JSONResponse(status_code=503, content={"error": "Service busy"})

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=gemini_key)
        image_bytes = base64.b64decode(req.image_base64)

        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                types.Part.from_text(text=prompt),
            ],
        )
        return {"analysis": response.text, "status": "success"}
    except Exception as e:
        logger.error(f"Soil analysis error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
