"""
api_gateway/main.py
===================
FastAPI application entry point for the Contextual Identity Fusion Engine.
Running in "Demo Mode" using SQLite and BackgroundTasks.
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api_gateway.config import settings
from api_gateway.routers import telemetry, risk, devices
from api_gateway.middleware.rate_limiter import rate_limit_middleware
from shared.logger import get_logger

logger = get_logger("APIGateway")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown of async resources."""
    print(f"[CIFE API] Starting in Demo Mode on {settings.api_host}:{settings.api_port}")
    yield
    print("[CIFE API] Shutdown complete.")

app = FastAPI(
    title="CIFE — Contextual Identity Fusion Engine (Demo Mode)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom rate limiter middleware
@app.middleware("http")
async def apply_rate_limit(request: Request, call_next):
    return await rate_limit_middleware(request, call_next)

# --- Routers ---
app.include_router(telemetry.router)
app.include_router(risk.router)
app.include_router(devices.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "CIFE API Gateway",
        "version": "1.0.0",
        "status": "operational",
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "mode": "Demo Mode (SQLite + BackgroundTasks)",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_gateway.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
