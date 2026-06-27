import httpx
import os
import logging
from services.key_manager import key_manager

logger = logging.getLogger("uvicorn.error")

def _get_owm_key() -> tuple[str, int]:
    """Retrieve weather key and account number dynamically from key_manager."""
    key, acc = key_manager.get_weather_key()
    if not key:
        return os.getenv("OPENWEATHER_API_KEY", ""), 1
    return key, acc

# Step 1: Convert any village/mandal/district name to lat/lon
async def geocode_location(place: str) -> dict:
    """Convert village name like 'Jagathi, Kaviti Mandal' to coordinates."""
    owm_key, acc = _get_owm_key()
    logger.info(f"Geocoding location '{place}' using Account {acc} weather key")
    
    async with httpx.AsyncClient() as client:
        # Try with India country code for accuracy
        try:
            resp = await client.get(
                "http://api.openweathermap.org/geo/1.0/direct",
                params={
                    "q": f"{place},Andhra Pradesh,IN",
                    "limit": 5,
                    "appid": owm_key
                }
            )
            if resp.status_code == 429:
                logger.warning(f"Weather API rate-limited on Account {acc} during geocoding.")
                key_manager.report_rate_limit("weather", acc)
                owm_key, acc = _get_owm_key()
                resp = await client.get(
                    "http://api.openweathermap.org/geo/1.0/direct",
                    params={
                        "q": f"{place},Andhra Pradesh,IN",
                        "limit": 5,
                        "appid": owm_key
                    }
                )
            results = resp.json()
            if isinstance(results, list) and results:
                return {"lat": results[0]["lat"], "lon": results[0]["lon"], "found": results[0]["name"]}
        except Exception as e:
            logger.error(f"Error in geocode_location primary: {e}")

        # Fallback: try without state
        try:
            resp2 = await client.get(
                "http://api.openweathermap.org/geo/1.0/direct",
                params={"q": f"{place},IN", "limit": 5, "appid": owm_key}
            )
            if resp2.status_code == 429:
                logger.warning(f"Weather API rate-limited on Account {acc} during geocoding fallback.")
                key_manager.report_rate_limit("weather", acc)
                owm_key, acc = _get_owm_key()
                resp2 = await client.get(
                    "http://api.openweathermap.org/geo/1.0/direct",
                    params={"q": f"{place},IN", "limit": 5, "appid": owm_key}
                )
            results2 = resp2.json()
            if isinstance(results2, list) and results2:
                return {"lat": results2[0]["lat"], "lon": results2[0]["lon"], "found": results2[0]["name"]}
        except Exception as e:
            logger.error(f"Error in geocode_location fallback: {e}")

        return None

# Step 2: Get weather by coordinates (works for any location on Earth)
async def get_weather_by_coords(lat: float, lon: float) -> dict:
    owm_key, acc = _get_owm_key()
    logger.info(f"Fetching weather for coords ({lat}, {lon}) using Account {acc} weather key")
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "lat": lat,
                "lon": lon,
                "appid": owm_key,
                "units": "metric",   # Celsius
                "lang": "en"
            }
        )
        if resp.status_code == 429:
            logger.warning(f"Weather API rate-limited on Account {acc} during weather fetch.")
            key_manager.report_rate_limit("weather", acc)
            owm_key, acc = _get_owm_key()
            resp = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": owm_key,
                    "units": "metric",
                    "lang": "en"
                }
            )
        d = resp.json()
        return {
            "temp": round(d["main"]["temp"]),
            "feels_like": round(d["main"]["feels_like"]),
            "humidity": d["main"]["humidity"],
            "description": d["weather"][0]["description"],
            "wind_speed": d["wind"]["speed"],
            "visibility": d.get("visibility", 0) // 1000,
            "city_found": d["name"]
        }

# Step 3: Main function — takes any village/mandal/district name
async def get_weather(location: str) -> str:
    """Get weather for any Indian village, mandal, or district."""
    import re
    
    # Extract mandal name if mentioned
    mandal_match = re.search(r'(\w+)\s+mandal', location, re.IGNORECASE)
    village_match = re.search(r'(\w+)\s+village', location, re.IGNORECASE)
    
    search_terms = []
    if village_match: search_terms.append(village_match.group(1))
    if mandal_match: search_terms.append(mandal_match.group(1))
    search_terms.append(location.strip())  # full text as last fallback

    coords = None
    found_via = None
    for term in search_terms:
        coords = await geocode_location(term)
        if coords:
            found_via = term
            break

    if not coords:
        # Hard fallback: use Srikakulam district (nearest district HQ for Kaviti area)
        coords = {"lat": 18.2949, "lon": 83.8938, "found": "Srikakulam (nearest district)"}
        found_via = "district fallback"

    weather = await get_weather_by_coords(coords["lat"], coords["lon"])

    note = ""
    if found_via == "district fallback" or coords["found"].lower() not in location.lower():
        note = f"\n⚠️ Exact village not found in weather database. Showing weather for nearest location: **{weather['city_found']}**."

    return f"""
🌡️ **Current Weather near {location}**
(Data from: {weather['city_found']})

• Temperature: **{weather['temp']}°C** (feels like {weather['feels_like']}°C)
• Condition: {weather['description'].title()}
• Humidity: {weather['humidity']}%
• Wind: {weather['wind_speed']} m/s
• Visibility: {weather['visibility']} km
{note}

🌾 **Farming advice:**
{"🔥 Very hot — irrigate in evening only, avoid afternoon fieldwork." if weather['temp'] > 38 else ""}
{"🌧️ High humidity — risk of fungal diseases. Consider preventive fungicide spray." if weather['humidity'] > 85 else ""}
{"✅ Good conditions for field work today." if weather['temp'] <= 35 and weather['humidity'] <= 75 else ""}
"""
