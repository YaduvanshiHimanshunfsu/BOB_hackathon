"""
api_gateway/routers/telemetry.py
================================
Telemetry ingestion endpoint.
Receives behavioral + device payloads, validates schema, and queues to Redis Streams.
This endpoint does ZERO computation — validate, queue, return 202.
"""

import time
from fastapi import APIRouter, HTTPException, Request
from api_gateway.schemas.telemetry_schema import TelemetryPayload, TelemetryResponse
from api_gateway.redis_client import push_to_stream, get_stream_length
from shared.constants import REDIS_STREAM_KEY, RATE_LIMIT_PER_MINUTE

router = APIRouter(prefix="/api/v1/telemetry", tags=["Telemetry"])


@router.post(
    "/ingest",
    response_model=TelemetryResponse,
    status_code=202,
    summary="Ingest telemetry payload",
    description=(
        "Receives behavioral signals and device fingerprint from the client. "
        "Validates the payload schema via Pydantic, then pushes to Redis Streams "
        "for asynchronous ML processing. Returns 202 Accepted immediately (<5ms). "
        "All data transmitted over TLS 1.3 — no client-side encryption needed."
    ),
)
async def ingest_telemetry(payload: TelemetryPayload, request: Request):
    """
    Ingest a telemetry payload into the processing pipeline.

    The API performs:
    1. Pydantic schema validation (automatic via type hints)
    2. Push to Redis Stream (XADD — non-blocking)
    3. Return 202 Accepted immediately

    No ML inference, no DB writes, no heavy computation here.
    """
    try:
        # Enrich payload with server-side metadata
        enriched = payload.model_dump()
        enriched["server_timestamp"] = time.time() * 1000
        enriched["client_ip"] = request.client.host if request.client else "unknown"

        # Push to Redis Stream for async processing
        entry_id = await push_to_stream(REDIS_STREAM_KEY, enriched)

        # Get current queue depth for monitoring
        queue_depth = await get_stream_length(REDIS_STREAM_KEY)

        return TelemetryResponse(
            status="accepted",
            queue_depth=queue_depth,
            message=f"Telemetry queued as {entry_id}",
        )

    except Exception as e:
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
    try:
        queue_depth = await get_stream_length(REDIS_STREAM_KEY)
        return {
            "status": "healthy",
            "stream": REDIS_STREAM_KEY,
            "queue_depth": queue_depth,
            "timestamp": time.time(),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
