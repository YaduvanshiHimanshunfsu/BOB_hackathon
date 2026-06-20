"""
api_gateway/schemas/risk_schema.py
==================================
Pydantic models for risk score responses returned by the API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class RiskScoreResponse(BaseModel):
    """Risk score breakdown returned for a user."""
    user_id: str
    session_id: Optional[str] = None
    composite_risk_score: float = Field(..., ge=0, le=100)
    behavioral_score: float = Field(..., ge=0, le=100)
    device_score: float = Field(..., ge=0, le=100)
    context_bonus: float = Field(..., ge=0, le=50)
    risk_tier: str = Field(..., description="LOW | MODERATE | HIGH | CRITICAL")
    action: str = Field(..., description="ALLOW | CHALLENGE_SOFT | CHALLENGE_HARD | DENY")
    timestamp: float
    details: Optional[dict] = None


class DeviceInfo(BaseModel):
    """Information about a registered device."""
    device_id: str
    fingerprint_hash: str
    first_seen: float
    last_seen: float
    trust_level: str = Field(default="unknown", description="trusted | known | new | blocked")
    session_count: int = 0


class DeviceListResponse(BaseModel):
    """List of devices registered to a user."""
    user_id: str
    devices: list[DeviceInfo] = []
    total_count: int = 0
