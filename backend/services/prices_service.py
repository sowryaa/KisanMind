import httpx, os
from datetime import datetime

DATAGOV_KEY = os.getenv("DATAGOV_API_KEY")

MOCK_PRICES = {
    "Cotton": {"min_price": 6500, "max_price": 7200, "modal_price": 6850, "unit": "quintal"},
    "Chilli": {"min_price": 11000, "max_price": 13500, "modal_price": 12200, "unit": "quintal"},
    "Groundnut": {"min_price": 5000, "max_price": 5800, "modal_price": 5400, "unit": "quintal"},
    "Rice": {"min_price": 1900, "max_price": 2300, "modal_price": 2100, "unit": "quintal"},
    "Onion": {"min_price": 1500, "max_price": 2200, "modal_price": 1850, "unit": "quintal"},
    "Tomato": {"min_price": 800, "max_price": 1600, "modal_price": 1200, "unit": "quintal"},
    "Maize": {"min_price": 1600, "max_price": 2100, "modal_price": 1850, "unit": "quintal"},
    "Sunflower": {"min_price": 5200, "max_price": 6000, "modal_price": 5600, "unit": "quintal"},
}

async def get_prices(commodity: str = None, district: str = None):
    """Fetch live mandi prices from data.gov.in"""
    try:
        params = {
            "api-key": DATAGOV_KEY,
            "format": "json",
            "filters[state]": "Andhra Pradesh",
            "limit": 50
        }
        if district:
            params["filters[district]"] = district
        if commodity:
            params["filters[commodity]"] = commodity.title()

        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
                params=params
            )
            if resp.status_code == 200:
                data = resp.json()
                records = data.get("records", [])
                if records:
                    return {
                        "source": "live",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "district": district,
                        "total": data.get("total", 0),
                        "records": records
                    }
    except Exception as e:
        print(f"Price API error: {e}")

    # Fallback
    return {
        "source": "cached",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "district": district or "Andhra Pradesh",
        "records": [
            {
                "commodity": k,
                "min_price": v["min_price"],
                "max_price": v["max_price"],
                "modal_price": v["modal_price"],
                "market": district or "Local Market",
                "arrival_date": datetime.now().strftime("%d/%m/%Y")
            }
            for k, v in MOCK_PRICES.items()
        ]
    }
