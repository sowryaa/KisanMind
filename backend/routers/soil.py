from fastapi import APIRouter, Query
from services.soil_service import get_location_farm_data, get_coordinates, get_soil_data, get_open_meteo_weather, interpret_soil

router = APIRouter()

@router.get("/data")
async def soil_data(location: str = Query(..., description="Village, mandal, or district name")):
    """Get soil + weather data for any location."""
    result = await get_location_farm_data(location)
    return {"location": location, "data": result}

@router.get("/weather")
async def open_meteo_weather(location: str = Query(..., description="Place name")):
    """Get detailed weather forecast from Open-Meteo."""
    coords = await get_coordinates(location)
    if not coords:
        return {"error": f"Location not found: {location}"}
    weather = await get_open_meteo_weather(coords["lat"], coords["lon"])
    return {"location": coords, "weather": weather}
