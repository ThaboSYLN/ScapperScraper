import time
import logging
from typing import Any, Optional
from threading import Lock

logger = logging.getLogger(__name__)

class TTLCache:
    """
    Thread-safe in-memory TTL cache.
    Prevents hammering the SofaScore API on every request.
    """

    def __init__(self):
        self._store: dict[str, dict] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            if time.time() > entry["expires_at"]:
                del self._store[key]
                logger.debug(f"Cache EXPIRED: {key}")
                return None
            logger.debug(f"Cache HIT: {key}")
            return entry["value"]

    def set(self, key: str, value: Any, ttl_seconds: int = 30):
        with self._lock:
            self._store[key] = {
                "value": value,
                "expires_at": time.time() + ttl_seconds,
            }
            logger.debug(f"Cache SET: {key} (TTL={ttl_seconds}s)")

    def delete(self, key: str):
        with self._lock:
            self._store.pop(key, None)

    def clear(self):
        with self._lock:
            self._store.clear()
            logger.info("Cache CLEARED")

    def stats(self) -> dict:
        with self._lock:
            now = time.time()
            active = sum(1 for v in self._store.values() if now <= v["expires_at"])
            return {"total_keys": len(self._store), "active_keys": active}


# Singleton cache instance — imported everywhere
cache = TTLCache()

# TTL settings (seconds)
TTL_SPORTS = 3600          # Sports list rarely changes
TTL_CATEGORIES = 1800      # Categories change infrequently
TTL_TOURNAMENTS = 600      # Tournaments moderately stable
TTL_LIVE_EVENTS = 30       # Live events need fresh data
TTL_EVENT_DETAILS = 20     # Match details update frequently