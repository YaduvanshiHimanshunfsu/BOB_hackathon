"""
api_gateway/middleware/rate_limiter.py
=====================================
Redis-backed rate limiting middleware.
Prevents telemetry flood attacks and brute-force API abuse.
"""

import time
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from api_gateway.redis_client import get_redis
from shared.constants import RATE_LIMIT_PER_MINUTE


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limiter using Redis sliding window counters.
    Limits requests per client IP per minute.
    Only applies to telemetry ingestion endpoints.
    """

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit telemetry ingestion
        if "/api/v1/telemetry/ingest" not in request.url.path:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        rate_key = f"rate:{client_ip}:{int(time.time() // 60)}"

        try:
            redis = await get_redis()
            current_count = await redis.incr(rate_key)

            # Set expiry on first increment (auto-cleanup after 2 minutes)
            if current_count == 1:
                await redis.expire(rate_key, 120)

            if current_count > RATE_LIMIT_PER_MINUTE:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {RATE_LIMIT_PER_MINUTE} requests/min. "
                           f"Current: {current_count}",
                )
        except HTTPException:
            raise
        except Exception:
            # If Redis is down, allow the request through (fail-open)
            pass

        return await call_next(request)
