import httpx, os
from datetime import datetime

DATAGOV_KEY = os.getenv("DATAGOV_API_KEY")

MOCK_PRICES = {
    "Cotton": {"min_price": 6500, "max_price": 7200, "modal_price": 6850},
    "Chilli": {"min_price": 11000, "max_price": 13500, "modal_price": 12200},
    "Groundnut": {"min_price": 5000, "max_price": 5800, "modal_price": 5400},
    "Rice": {"min_price": 1900, "max_price": 2300, "modal_price": 2100},
    "Onion": {"min_price": 1500, "max_price": 2200, "modal_price": 1850},
    "Tomato": {"min_price": 800, "max_price": 1600, "modal_price": 1200},
    "Maize": {"min_price": 1600, "max_price": 2100, "modal_price": 1850},
    "Sunflower": {"min_price": 5200, "max_price": 6000, "modal_price": 5600},
}

async def get_prices(commodity: str = None, district: str = None):
    try:
        params = {
            "api-key": DATAGOV_KEY,
            "format": "json",
            "limit": 500,
            "offset": 0,
        }
        if commodity:
            params["filters[commodity]"] = commodity.title()

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
                params=params
            )
            if resp.status_code == 200:
                data = resp.json()
                records = data.get("records", [])

                # Filter for Andhra Pradesh on our side
                ap_records = [r for r in records if "andhra" in r.get("state", "").lower()]

                # Further filter by district if provided
                if district and ap_records:
                    dist_records = [r for r in ap_records if district.lower() in r.get("district", "").lower()]
                    if dist_records:
                        ap_records = dist_records

                if ap_records:
                    return {
                        "source": "live",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "district": district or "Andhra Pradesh",
                        "records": ap_records
                    }
    except Exception as e:
        print(f"Price API error: {e}")

    # Fallback to mock
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
                "arrival_date": datetime.now().strftime("%d/%m/%Y"),
                "state": "Andhra Pradesh"
            }
            for k, v in MOCK_PRICES.items()
        ]
    }
