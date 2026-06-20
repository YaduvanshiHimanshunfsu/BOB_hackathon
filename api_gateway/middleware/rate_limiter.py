"""
api_gateway/middleware/rate_limiter.py
======================================
In-memory rate limiter for Demo Mode.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
import time
from shared.constants import RATE_LIMIT_PER_MINUTE

# Simple in-memory rate limiting dictionary
_rate_limit_cache = {}

async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    current_time = int(time.time())
    
    # We only rate limit telemetry endpoints to prevent spam
    if request.url.path.startswith("/api/v1/telemetry"):
        # Create or update sliding window
        window = _rate_limit_cache.get(client_ip, [])
        # Keep only timestamps within the last 60 seconds
        window = [ts for ts in window if current_time - ts < 60]
        
        if len(window) >= RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again in a minute."}
            )
            
        window.append(current_time)
        _rate_limit_cache[client_ip] = window

    response = await call_next(request)
    return response
