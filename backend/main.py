from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, weather, prices, auth, schemes, soil, logistics
import os

app = FastAPI(title="KisanMind API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development flexibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(weather.router, prefix="/api/weather", tags=["weather"])
app.include_router(prices.router, prefix="/api/prices", tags=["prices"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(schemes.router, prefix="/api/schemes", tags=["schemes"])
app.include_router(soil.router, prefix="/api/soil", tags=["soil"])
app.include_router(logistics.router, prefix="/api/logistics", tags=["logistics"])

@app.get("/health")
def health(): return {"status": "ok", "service": "KisanMind API"}
# force rebuild Mon Jun 29 12:00:24 IST 2026
