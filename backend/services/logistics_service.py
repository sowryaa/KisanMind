from typing import Optional, Dict, Any, Tuple
from math import radians, sin, cos, sqrt, atan2
import os
import httpx


ORS_API_KEY = os.getenv("ORS_API_KEY")


def geocode_place(place_name: str) -> Optional[Tuple[float, float, str]]:
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": place_name,
        "format": "jsonv2",
        "limit": 1,
    }
    headers = {
        "User-Agent": "KisanMind/1.0 (logistics calculator)"
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        if not data:
            return None

        item = data[0]
        lat = float(item["lat"])
        lon = float(item["lon"])
        display_name = item.get("display_name", place_name)
        return lat, lon, display_name
    except Exception:
        return None


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


def get_ors_road_distance_km(
    source_lon: float,
    source_lat: float,
    dest_lon: float,
    dest_lat: float,
) -> Optional[float]:
    if not ORS_API_KEY:
        return None

    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "coordinates": [
            [source_lon, source_lat],
            [dest_lon, dest_lat]
        ]
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        routes = data.get("routes", [])
        if not routes:
            return None

        summary = routes[0].get("summary", {})
        distance_meters = summary.get("distance")
        if distance_meters is None:
            return None

        return float(distance_meters) / 1000.0
    except Exception:
        return None


def calculate_logistics(
    crop_name: str,
    source_market: str,
    destination_market: str,
    quantity_kg: float,
    source_price_per_kg: float,
    destination_price_per_kg: float,
    distance_km: Optional[float] = None,
    loading_unloading: float = 100.0,
    broker_percent: float = 2.0,
    toll_tax: float = 0.0,
    transport_rate_per_km_per_ton: float = 10.0,
    source_contact_number: Optional[str] = None,
) -> Dict[str, Any]:
    if quantity_kg <= 0:
        raise ValueError("quantity_kg must be greater than 0")

    if source_price_per_kg < 0 or destination_price_per_kg < 0:
        raise ValueError("Prices cannot be negative")

    resolved_source = None
    resolved_destination = None
    distance_source = "manual_input"

    if distance_km is None:
        source_geo = geocode_place(source_market)
        dest_geo = geocode_place(destination_market)

        if not source_geo or not dest_geo:
            raise ValueError("Could not estimate distance from source and destination names")

        src_lat, src_lon, resolved_source = source_geo
        dst_lat, dst_lon, resolved_destination = dest_geo

        road_distance_km = get_ors_road_distance_km(src_lon, src_lat, dst_lon, dst_lat)

        if road_distance_km is not None:
            distance_km = road_distance_km
            distance_source = "openrouteservice_road_distance"
        else:
            straight_line_km = haversine_distance_km(src_lat, src_lon, dst_lat, dst_lon)
            distance_km = straight_line_km * 1.2
            distance_source = "estimated_from_geocoded_places"

    if distance_km < 0:
        raise ValueError("Distance cannot be negative")

    quantity_ton = quantity_kg / 1000.0
    base_cost = source_price_per_kg * quantity_kg
    transport_cost = distance_km * transport_rate_per_km_per_ton * quantity_ton
    broker_commission = (broker_percent / 100.0) * base_cost

    total_cost = (
        base_cost
        + transport_cost
        + loading_unloading
        + broker_commission
        + toll_tax
    )

    final_cost_per_kg = total_cost / quantity_kg
    total_revenue = destination_price_per_kg * quantity_kg
    profit_loss_rs = total_revenue - total_cost
    profit_loss_percent = (profit_loss_rs / total_cost * 100.0) if total_cost > 0 else 0.0

    status = "profit" if profit_loss_rs > 0 else "loss" if profit_loss_rs < 0 else "breakeven"

    return {
        "crop_name": crop_name,
        "source_market": source_market,
        "destination_market": destination_market,
        "resolved_source_market": resolved_source,
        "resolved_destination_market": resolved_destination,
        "quantity_kg": quantity_kg,
        "source_contact_number": source_contact_number,
        "cost_breakdown": {
            "source_price_per_kg": round(source_price_per_kg, 2),
            "base_cost": round(base_cost, 2),
            "distance_km": round(distance_km, 2),
            "distance_source": distance_source,
            "transport_rate_per_km_per_ton": round(transport_rate_per_km_per_ton, 2),
            "transport_cost": round(transport_cost, 2),
            "loading_unloading": round(loading_unloading, 2),
            "broker_percent": round(broker_percent, 2),
            "broker_commission": round(broker_commission, 2),
            "toll_tax": round(toll_tax, 2),
            "total_cost": round(total_cost, 2),
            "final_cost_per_kg": round(final_cost_per_kg, 2),
        },
        "market_comparison": {
            "destination_price_per_kg": round(destination_price_per_kg, 2),
            "total_revenue": round(total_revenue, 2),
            "profit_loss_rs": round(profit_loss_rs, 2),
            "profit_loss_percent": round(profit_loss_percent, 2),
            "status": status,
        },
        "notes": {
            "best_time_to_buy": "To be added from historical mandi price trend analysis",
            "alternate_cheaper_markets": [],
            "weather_warning": "Optional - to be added from route weather API",
            "price_data_status": "manual_input_for_now",
        },
    }
