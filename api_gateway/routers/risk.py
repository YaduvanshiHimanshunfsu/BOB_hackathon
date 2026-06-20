"""
api_gateway/routers/risk.py
===========================
Risk score query endpoint.
Returns the latest computed risk score for a given user from in-memory cache.
"""

import time
import json
from fastapi import APIRouter, HTTPException, Depends
from api_gateway.schemas.risk_schema import RiskScoreResponse
from api_gateway.cache import risk_cache

router = APIRouter(prefix="/api/v1/risk", tags=["Risk Score API"])


@router.get("/{user_id}", response_model=RiskScoreResponse)
async def get_latest_risk_score(user_id: str):
    """
    Fetch the latest computed Contextual Risk Score for a user.
    Reads from the in-memory risk cache.
    """
    # Fetch from memory cache
    data = risk_cache.get(f"risk:{user_id}")
    
    if not data:
        return RiskScoreResponse(
            user_id=user_id,
            session_id=None,
            composite_risk_score=0.0,
            risk_tier="UNKNOWN",
            action="ALLOW",
            behavioral_score=0.0,
            device_score=0.0,
            context_bonus=0.0,
            timestamp="",
            message="No active risk profile found for this user. "
                   "User may not have any telemetry data yet.",
        )

    # In our memory cache, data is already a dict.
    # But if breakdown is somehow a string, handle it.
    breakdown_data = data.get("breakdown", {})
    if isinstance(breakdown_data, str):
        try:
            breakdown = json.loads(breakdown_data)
        except Exception:
            breakdown = {}
    else:
        breakdown = breakdown_data

    return RiskScoreResponse(
        user_id=user_id,
        session_id=data.get("session_id"),
        composite_risk_score=float(data.get("composite_risk_score", 0)),
        behavioral_score=float(breakdown.get("behavioral_score", 0)),
        device_score=float(breakdown.get("device_score", 0)),
        context_bonus=float(data.get("context_bonus", 0)),
        risk_tier=data.get("risk_tier", "LOW"),
        action=data.get("action", "ALLOW"),
        timestamp=float(data.get("timestamp", time.time())),
    )


@router.get(
    "/{user_id}/history",
    summary="Get risk score history for a user",
    description="Returns the last N risk evaluations from PostgreSQL.",
)
async def get_risk_history(user_id: str, limit: int = 50):
    """
    Fetch risk score history from the audit ledger.
    Useful for the admin dashboard timeline view.
    """
    # TODO: Implement PostgreSQL query for risk event history
    return {
        "user_id": user_id,
        "limit": limit,
        "events": [],
        "message": "History endpoint — will query PostgreSQL audit ledger",
    }
