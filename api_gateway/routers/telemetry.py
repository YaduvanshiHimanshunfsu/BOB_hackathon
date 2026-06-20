"""
api_gateway/routers/telemetry.py
================================
Telemetry ingestion endpoint.
Receives behavioral + device payloads, validates schema, and queues to BackgroundTasks for ML.
"""

import time
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from api_gateway.schemas.telemetry_schema import TelemetryPayload, TelemetryResponse
from api_gateway.processor import process_telemetry_payload
from shared.logger import get_logger

logger = get_logger("TelemetryRouter")
router = APIRouter(prefix="/api/v1/telemetry", tags=["Telemetry"])


@router.post(
    "/ingest",
    response_model=TelemetryResponse,
    status_code=202,
    summary="Ingest telemetry payload",
    description=(
        "Receives behavioral signals and device fingerprint from the client. "
        "Validates the payload schema via Pydantic, then processes asynchronously via BackgroundTasks. "
        "Returns 202 Accepted immediately. "
        "All data transmitted over TLS 1.3 — no client-side encryption needed."
    ),
)
async def ingest_telemetry(payload: TelemetryPayload, request: Request, background_tasks: BackgroundTasks):
    """
    Ingest a telemetry payload into the processing pipeline.

    The API performs:
    1. Pydantic schema validation (automatic via type hints)
    2. Dispatch to BackgroundTasks
    3. Return 202 Accepted immediately

    No DB writes or ML inference block the main thread.
    """
    try:
        # Enrich payload with server-side metadata
        enriched = payload.model_dump()
        enriched["server_timestamp"] = time.time() * 1000
        enriched["client_ip"] = request.client.host if request.client else "unknown"

        # Dispatch async to processor
        background_tasks.add_task(process_telemetry_payload, enriched)

        return TelemetryResponse(
            status="accepted",
            queue_depth=0,  # Not tracked in Demo Mode
            message=f"Telemetry dispatched to background task",
        )

    except Exception as e:
        logger.error(f"Failed to queue telemetry: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue telemetry: {str(e)}"
        )


@router.get(
    "/health",
    summary="Telemetry service health check",
)
async def telemetry_health():
    """Check if the telemetry ingestion pipeline is operational."""
    return {
        "status": "healthy",
        "mode": "Demo (SQLite + BackgroundTasks)",
        "timestamp": time.time(),
    }
