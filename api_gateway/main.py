"""
api_gateway/main.py
===================
FastAPI application entry point for the Contextual Identity Fusion Engine.

This is the Ingestion Gateway — it receives telemetry payloads from the
banking frontend, validates them, and queues them into Redis Streams for
asynchronous ML processing. It does ZERO computation on payloads.

Transport Security: All endpoints served over TLS 1.3 (enforced at
reverse proxy / load balancer level). No client-side encryption — see
shared/constants.py Fix #2 for rationale.
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_gateway.config import settings
from api_gateway.redis_client import close_redis
from api_gateway.routers import telemetry, risk, devices
from api_gateway.middleware.rate_limiter import RateLimiterMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown of async resources."""
    # Startup
    print(f"[CIFE API] Starting on {settings.api_host}:{settings.api_port}")
    print(f"[CIFE API] Redis: {settings.redis_host}:{settings.redis_port}")
    print(f"[CIFE API] PostgreSQL: {settings.postgres_host}:{settings.postgres_port}")
    yield
    # Shutdown
    await close_redis()
    print("[CIFE API] Shutdown complete.")


app = FastAPI(
    title="CIFE — Contextual Identity Fusion Engine",
    description=(
        "Privacy-first, risk-based Identity Trust Framework for Bank of Baroda. "
        "Continuously validates customer identities by fusing behavioral biometrics "
        "and device fingerprinting into a real-time Composite Risk Score (0-100). "
        "Triggers step-up verification only when risk is elevated."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimiterMiddleware)

# --- Routers ---
app.include_router(telemetry.router)
app.include_router(risk.router)
app.include_router(devices.router)


@app.get("/", tags=["Health"])
async def root():
    """API root — basic health check."""
    return {
        "service": "CIFE API Gateway",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": time.time(),
        "endpoints": {
            "telemetry_ingest": "/api/v1/telemetry/ingest",
            "risk_score": "/api/v1/risk/{user_id}",
            "device_list": "/api/v1/devices/{user_id}",
            "docs": "/docs",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check for monitoring."""
    return {
        "status": "healthy",
        "service": "api_gateway",
        "uptime": time.time(),
        "redis": f"{settings.redis_host}:{settings.redis_port}",
        "postgres": f"{settings.postgres_host}:{settings.postgres_port}",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_gateway.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
    )
