from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.logistics_service import calculate_logistics

router = APIRouter()


class LogisticsRequest(BaseModel):
    crop_name: str = Field(..., min_length=1)
    source_market: str = Field(..., min_length=1)
    destination_market: str = Field(..., min_length=1)
    quantity_kg: float = Field(..., gt=0)
    source_price_per_kg: float = Field(..., ge=0)
    destination_price_per_kg: float = Field(..., ge=0)
    distance_km: Optional[float] = Field(None, ge=0)
    loading_unloading: float = Field(100.0, ge=0)
    broker_percent: float = Field(2.0, ge=0)
    toll_tax: float = Field(0.0, ge=0)
    transport_rate_per_km_per_ton: float = Field(10.0, ge=0)
    source_contact_number: Optional[str] = None


class LogisticsResponse(BaseModel):
    crop_name: str
    source_market: str
    destination_market: str
    resolved_source_market: Optional[str] = None
    resolved_destination_market: Optional[str] = None
    quantity_kg: float
    source_contact_number: Optional[str]
    cost_breakdown: dict
    market_comparison: dict
    notes: dict


@router.post("/calculate", response_model=LogisticsResponse)
def calculate_logistics_route(payload: LogisticsRequest):
    try:
        result = calculate_logistics(
            crop_name=payload.crop_name,
            source_market=payload.source_market,
            destination_market=payload.destination_market,
            quantity_kg=payload.quantity_kg,
            source_price_per_kg=payload.source_price_per_kg,
            destination_price_per_kg=payload.destination_price_per_kg,
            distance_km=payload.distance_km,
            loading_unloading=payload.loading_unloading,
            broker_percent=payload.broker_percent,
            toll_tax=payload.toll_tax,
            transport_rate_per_km_per_ton=payload.transport_rate_per_km_per_ton,
            source_contact_number=payload.source_contact_number,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/test")
def logistics_test():
    return calculate_logistics(
        crop_name="Tomato",
        source_market="Kurnool",
        destination_market="Bengaluru",
        quantity_kg=2000,
        source_price_per_kg=18,
        destination_price_per_kg=24,
        distance_km=320,
        loading_unloading=100,
        broker_percent=2,
        toll_tax=500,
        source_contact_number="N/A",
    )
