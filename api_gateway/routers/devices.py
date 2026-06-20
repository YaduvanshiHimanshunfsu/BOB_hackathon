"""
api_gateway/routers/devices.py
==============================
Device registry endpoints.
Manages the list of known/trusted devices per user.
"""

from fastapi import APIRouter, HTTPException
from api_gateway.schemas.risk_schema import DeviceListResponse

router = APIRouter(prefix="/api/v1/devices", tags=["Device Registry"])


@router.get(
    "/{user_id}",
    response_model=DeviceListResponse,
    summary="List registered devices for a user",
    description="Returns all known devices associated with a user account.",
)
async def list_devices(user_id: str):
    """
    Fetch all registered devices for a user from PostgreSQL.
    Used by the admin dashboard to display device trust levels.
    """
    # TODO: Implement PostgreSQL query for device registry
    return DeviceListResponse(
        user_id=user_id,
        devices=[],
        total_count=0,
    )


@router.delete(
    "/{user_id}/{device_id}",
    summary="Revoke a device's trusted status",
    description="Marks a device as blocked, forcing re-verification on next login.",
)
async def revoke_device(user_id: str, device_id: str):
    """
    Revoke trust for a specific device.
    Next login from this device will trigger CHALLENGE_HARD.
    """
    # TODO: Implement device revocation in PostgreSQL
    return {
        "status": "revoked",
        "user_id": user_id,
        "device_id": device_id,
        "message": "Device trust revoked. Next login will require step-up authentication.",
    }
