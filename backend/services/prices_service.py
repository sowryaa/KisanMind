import httpx, os
from datetime import datetime

DATAGOV_KEY = os.getenv("DATAGOV_API_KEY")

# Fallback mock prices (update weekly manually or via cron)
MOCK_PRICES = {
    "cotton": {"price": 6850, "unit": "quintal", "trend": "up", "market": "Kurnool"},
    "chilli": {"price": 12200, "unit": "quintal", "trend": "down", "market": "Guntur"},
    "groundnut": {"price": 5400, "unit": "quintal", "trend": "stable", "market": "Kurnool"},
    "rice": {"price": 2100, "unit": "quintal", "trend": "up", "market": "Nellore"},
    "onion": {"price": 1850, "unit": "quintal", "trend": "up", "market": "Kurnool"},
    "tomato": {"price": 1200, "unit": "quintal", "trend": "down", "market": "Madanapalle"},
    "maize": {"price": 1850, "unit": "quintal", "trend": "stable", "market": "Guntur"},
    "soybean": {"price": 4200, "unit": "quintal", "trend": "up", "market": "Adilabad"},
    "jowar": {"price": 2800, "unit": "quintal", "trend": "stable", "market": "Kurnool"},
    "sunflower": {"price": 5600, "unit": "quintal", "trend": "up", "market": "Nandyal"},
}

async def get_prices(commodity: str = None, district: str = None):
    """Try live API first, fall back to mock data."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
                params={
                    "api-key": DATAGOV_KEY,
                    "format": "json",
                    "filters[state]": "Andhra Pradesh",
                    "filters[commodity]": commodity.title() if commodity else "",
                    "limit": 20
                }
            )
            if resp.status_code == 200:
                return {"source": "live", "data": resp.json(), "date": datetime.now().strftime("%Y-%m-%d")}
    except Exception:
        pass
    
    # Fallback to cached mock
    if commodity:
        c = commodity.lower()
        if c in MOCK_PRICES:
            return {"source": "cached", "date": datetime.now().strftime("%Y-%m-%d"), "prices": {c: MOCK_PRICES[c]}}
    
    return {"source": "cached", "date": datetime.now().strftime("%Y-%m-%d"), "prices": MOCK_PRICES}
