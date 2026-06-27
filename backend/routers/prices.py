from fastapi import APIRouter, Query
from typing import Optional
from services.prices_service import get_prices

router = APIRouter()

@router.get("/")
async def prices(commodity: Optional[str] = Query(None), district: Optional[str] = Query(None)):
    return await get_prices(commodity, district)
