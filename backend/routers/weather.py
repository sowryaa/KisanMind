from fastapi import APIRouter, Query
from services.weather_service import geocode_location, get_weather_by_coords

router = APIRouter()

@router.get("/")
async def weather(district: str = Query(..., description="Name of the district in AP/Telangana")):
    coords = await geocode_location(district)
    if not coords:
        # Default coords for fallback
        coords = {"lat": 18.2949, "lon": 83.8938, "found": "Srikakulam"}
    
    weather_data = await get_weather_by_coords(coords["lat"], coords["lon"])
    
    # Return structured dict to keep the frontend modal happy
    return {
        "district": district,
        "forecasts": [
            {
                "time": "Current Weather",
                "temp": weather_data["temp"],
                "humidity": weather_data["humidity"],
                "rain_mm": 0,
                "description": weather_data["description"],
                "wind_speed": weather_data["wind_speed"]
            }
        ]
    }
