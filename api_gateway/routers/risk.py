"""
api_gateway/routers/risk.py
===========================
Risk score query endpoint.
Returns the latest computed risk score for a given user from Redis cache.
"""

import time
from fastapi import APIRouter, HTTPException
from api_gateway.redis_client import get_latest_risk_score
from api_gateway.schemas.risk_schema import RiskScoreResponse

router = APIRouter(prefix="/api/v1/risk", tags=["Risk Scoring"])


@router.get(
    "/{user_id}",
    response_model=RiskScoreResponse,
    summary="Get latest risk score for a user",
    description="Returns the most recent Composite Risk Score computed by the ML worker.",
)
async def get_risk_score(user_id: str):
    """
    Fetch the latest risk score for a user from Redis cache.
    The ML worker daemon updates this cache after each scoring evaluation.
    """
    data = await get_latest_risk_score(user_id)

    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"No risk score found for user '{user_id}'. "
                   "User may not have any telemetry data yet.",
        )

    return RiskScoreResponse(
        user_id=user_id,
        session_id=data.get("session_id"),
        composite_risk_score=float(data.get("composite_risk_score", 0)),
        behavioral_score=float(data.get("behavioral_score", 0)),
        device_score=float(data.get("device_score", 0)),
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
