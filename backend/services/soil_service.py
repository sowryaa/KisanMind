"""
KisanMind — Soil Data Service
================================
Fetches real soil data from ISRIC SoilGrids API (free, no API key needed)
for any location. Returns pH, NPK, organic carbon, texture, and moisture.
"""

import httpx
import logging

logger = logging.getLogger("uvicorn.error")

async def get_coordinates(place: str) -> dict:
    """Convert place name to lat/lon using Open-Meteo geocoding (free)."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": place, "count": 1, "language": "en", "format": "json"}
            )
            data = resp.json()
            results = data.get("results", [])
            if results:
                r = results[0]
                return {"lat": r["latitude"], "lon": r["longitude"], "name": r.get("name", place)}
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
    return None

async def get_soil_data(lat: float, lon: float) -> dict:
    """
    Fetch soil properties from ISRIC SoilGrids REST API.
    No API key required! Free for all.
    Properties: phh2o, nitrogen, soc (organic carbon), clay, sand, silt
    Depth: 0-5cm (topsoil)
    """
    properties = ["phh2o", "nitrogen", "soc", "clay", "sand", "silt", "bdod"]
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://rest.isric.org/soilgrids/v2.0/properties/query",
                params={
                    "lon": lon,
                    "lat": lat,
                    "property": properties,
                    "depth": "0-5cm",
                    "value": "mean"
                }
            )
            
            if resp.status_code != 200:
                logger.error(f"SoilGrids API error: {resp.status_code}")
                return None
                
            data = resp.json()
            layers = data.get("properties", {}).get("layers", [])
            
            soil = {}
            for layer in layers:
                name = layer.get("name")
                depths = layer.get("depths", [])
                if depths:
                    value = depths[0].get("values", {}).get("mean")
                    unit_factor = layer.get("unit_measure", {}).get("d_factor", 1)
                    if value is not None and unit_factor:
                        soil[name] = round(value / unit_factor, 2)
            
            return soil
    except Exception as e:
        logger.error(f"SoilGrids API error: {e}")
        return None

async def get_open_meteo_weather(lat: float, lon: float) -> dict:
    """
    Fetch detailed weather + forecast from Open-Meteo (completely free, no API key).
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": [
                        "temperature_2m", "relative_humidity_2m", "precipitation",
                        "wind_speed_10m", "weather_code", "soil_moisture_0_to_1cm"
                    ],
                    "daily": [
                        "precipitation_sum", "temperature_2m_max", "temperature_2m_min",
                        "et0_fao_evapotranspiration"
                    ],
                    "timezone": "Asia/Kolkata",
                    "forecast_days": 7
                }
            )
            return resp.json()
    except Exception as e:
        logger.error(f"Open-Meteo error: {e}")
        return None

def interpret_soil(soil: dict) -> dict:
    """Convert raw soil values into farmer-friendly interpretations."""
    result = {}
    
    # pH (phh2o is pH*10 already divided by d_factor=10)
    ph = soil.get("phh2o")
    if ph:
        result["ph"] = ph
        if ph < 5.5:
            result["ph_status"] = "Very Acidic — Apply lime 200kg/acre to correct"
        elif ph < 6.5:
            result["ph_status"] = "Slightly Acidic — Good for most crops"
        elif ph < 7.5:
            result["ph_status"] = "Neutral — Ideal for all crops ✅"
        elif ph < 8.5:
            result["ph_status"] = "Alkaline — Add gypsum or organic matter"
        else:
            result["ph_status"] = "Very Alkaline — Needs treatment before farming"
    
    # Nitrogen (cg/kg → g/kg)
    nitrogen = soil.get("nitrogen")
    if nitrogen:
        result["nitrogen"] = nitrogen
        if nitrogen < 1.0:
            result["nitrogen_status"] = "Low — Apply Urea 50kg/acre"
        elif nitrogen < 2.0:
            result["nitrogen_status"] = "Medium — Apply Urea 25kg/acre"
        else:
            result["nitrogen_status"] = "High — Reduce nitrogen fertilizer"
    
    # Organic Carbon (SOC in dg/kg → %)
    soc = soil.get("soc")
    if soc:
        result["organic_carbon"] = soc
        if soc < 0.5:
            result["soc_status"] = "Very Low — Add FYM 2 tonnes/acre urgently"
        elif soc < 1.0:
            result["soc_status"] = "Low — Add compost or FYM regularly"
        elif soc < 2.0:
            result["soc_status"] = "Medium — Good, maintain with organic matter"
        else:
            result["soc_status"] = "High — Excellent soil health ✅"
    
    # Texture
    clay = soil.get("clay", 0)
    sand = soil.get("sand", 0)
    silt = soil.get("silt", 0)
    result["clay_pct"] = clay
    result["sand_pct"] = sand
    result["silt_pct"] = silt
    
    if clay > 40:
        result["texture"] = "Heavy Clay — Good water retention, risk of waterlogging"
        result["best_crops"] = "Cotton, Sugarcane, Rice"
    elif sand > 70:
        result["texture"] = "Sandy — Poor water retention, needs frequent irrigation"
        result["best_crops"] = "Groundnut, Watermelon, Sesame"
    elif clay > 25:
        result["texture"] = "Clay Loam — Good for most crops"
        result["best_crops"] = "Cotton, Chilli, Maize, Soybean"
    else:
        result["texture"] = "Loamy — Best soil type for farming ✅"
        result["best_crops"] = "Vegetables, Groundnut, Chilli, Maize"
    
    return result

async def get_location_farm_data(place: str) -> str:
    """
    Main function: Given a place name, return complete soil + weather data
    formatted as a string for the AI to use.
    """
    coords = await get_coordinates(place)
    if not coords:
        return f"Could not find location: {place}"
    
    lat, lon = coords["lat"], coords["lon"]
    location_name = coords["name"]
    
    # Fetch soil and weather in parallel
    import asyncio
    soil_raw, weather = await asyncio.gather(
        get_soil_data(lat, lon),
        get_open_meteo_weather(lat, lon)
    )
    
    output = [f"📍 Location: {location_name} ({lat:.2f}°N, {lon:.2f}°E)\n"]
    
    # Soil data — use district fallback if ISRIC returns null
    if not soil_raw:
        soil_raw = get_district_soil_fallback(place)
        if soil_raw:
            soil_raw["source"] = "icar_fallback"
    if soil_raw:
        soil = interpret_soil(soil_raw)
        output.append("🌱 SOIL DATA (ISRIC SoilGrids — 0-5cm depth):")
        if "ph" in soil:
            output.append(f"  • pH: {soil['ph']} — {soil['ph_status']}")
        if "nitrogen" in soil:
            output.append(f"  • Nitrogen: {soil['nitrogen']} g/kg — {soil['nitrogen_status']}")
        if "organic_carbon" in soil:
            output.append(f"  • Organic Carbon: {soil['organic_carbon']}% — {soil['soc_status']}")
        if "clay_pct" in soil:
            output.append(f"  • Texture: Clay {soil['clay_pct']}%, Sand {soil['sand_pct']}%, Silt {soil['silt_pct']}%")
            output.append(f"  • Soil Type: {soil['texture']}")
            output.append(f"  • Best Crops: {soil['best_crops']}")
    else:
        output.append("🌱 Soil data temporarily unavailable.")
    
    # Weather data
    if weather:
        current = weather.get("current", {})
        daily = weather.get("daily", {})
        output.append("\n☀️ WEATHER (Open-Meteo — Live):")
        output.append(f"  • Temperature: {current.get('temperature_2m')}°C")
        output.append(f"  • Humidity: {current.get('relative_humidity_2m')}%")
        output.append(f"  • Rainfall today: {current.get('precipitation', 0)}mm")
        output.append(f"  • Wind: {current.get('wind_speed_10m')} km/h")
        soil_moisture = current.get("soil_moisture_0_to_1cm")
        if soil_moisture:
            output.append(f"  • Soil Moisture: {round(soil_moisture*100, 1)}%")
        
        if daily.get("precipitation_sum"):
            rain_7d = daily["precipitation_sum"][:7]
            output.append(f"  • 7-day rainfall forecast: {rain_7d} mm")
            total_rain = sum(r for r in rain_7d if r)
            if total_rain > 50:
                output.append("  ⚠️ Heavy rainfall expected — delay fertilizer application")
            elif total_rain < 5:
                output.append("  ⚠️ Dry week ahead — plan irrigation")
    
    return "\n".join(output)
