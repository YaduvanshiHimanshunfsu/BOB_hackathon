"""
api_gateway/schemas/telemetry_schema.py
=======================================
Pydantic models for validating incoming telemetry payloads.
Enforces strict schema validation at the API boundary before queueing to Redis.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
import time


class KeystrokeEvent(BaseModel):
    """A single keystroke timing event."""
    key_code: int = Field(..., ge=0, le=255, description="ASCII key code")
    hold_ms: float = Field(..., ge=0, le=5000, description="Key press duration in ms")
    flight_ms: float = Field(..., ge=0, le=10000, description="Time since previous key release in ms")


class MouseEvent(BaseModel):
    """A single mouse movement/click event."""
    x: float = Field(..., description="Cursor X position in viewport pixels")
    y: float = Field(..., description="Cursor Y position in viewport pixels")
    velocity: float = Field(..., ge=0, description="Cursor velocity in px/ms")
    timestamp: float = Field(..., description="Event timestamp (Unix ms)")


class BehavioralPayload(BaseModel):
    """Behavioral telemetry signals collected from user interaction."""
    keystrokes: list[KeystrokeEvent] = Field(default_factory=list, max_length=500)
    mouse_events: list[MouseEvent] = Field(default_factory=list, max_length=1000)
    scroll_delta_y: list[float] = Field(default_factory=list, max_length=200)
    touch_pressure: list[float] = Field(default_factory=list, max_length=200)


class DevicePayload(BaseModel):
    """Device fingerprint attributes collected from browser APIs."""
    canvas_hash: str = Field(..., min_length=8, max_length=128)
    webgl_renderer: str = Field(default="unknown", max_length=512)
    audio_hash: str = Field(default="unknown", max_length=128)
    screen: str = Field(default="unknown", max_length=32)  # e.g., "1920x1080x24"
    timezone: str = Field(default="unknown", max_length=64)
    language: str = Field(default="unknown", max_length=16)
    user_agent: str = Field(default="unknown", max_length=512)
    fonts_hash: str = Field(default="unknown", max_length=128)


class TelemetryPayload(BaseModel):
    """
    Complete telemetry payload from the client.
    Contains both behavioral signals and device fingerprint.
    """
    session_id: str = Field(..., min_length=1, max_length=64)
    user_id: str = Field(..., min_length=1, max_length=128)
    timestamp: float = Field(default_factory=lambda: time.time() * 1000)
    event_trigger: str = Field(
        default="passive",
        description="What triggered this payload: 'passive' (30s timer) or event name"
    )
    behavioral: BehavioralPayload = Field(default_factory=BehavioralPayload)
    device: DevicePayload

    @field_validator("event_trigger")
    @classmethod
    def validate_event_trigger(cls, v: str) -> str:
        valid_triggers = [
            "passive", "login", "fund_transfer_initiate", "beneficiary_add",
            "password_change", "otp_page_load", "profile_update", "logout",
        ]
        if v not in valid_triggers:
            v = "passive"  # Default to passive for unknown triggers
        return v


class TelemetryResponse(BaseModel):
    """Response returned after successful telemetry ingestion."""
    status: str = "accepted"
    queue_depth: int = 0
    message: str = "Telemetry queued for processing"
