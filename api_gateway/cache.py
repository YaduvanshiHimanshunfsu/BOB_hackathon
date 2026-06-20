"""
api_gateway/cache.py
====================
In-memory cache replacing Redis for the Demo Mode.
"""

class InMemoryCache:
    def __init__(self):
        self._cache = {}

    def get(self, key: str) -> dict:
        return self._cache.get(key, {})

    def set(self, key: str, value: dict):
        self._cache[key] = value

# Global singleton cache
risk_cache = InMemoryCache()
