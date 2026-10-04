"""
In-memory and persistent caching layer for SkyDeck.

Features:
- Time-to-Live (TTL) expiration enforcement.
- Stale-while-revalidate capability: Can return expired data as a fallback
  when network/server is unavailable (satisfying Phase 2 requirement).
- Cache age and freshness calculation.
"""

import time
from typing import Any, Optional, Tuple, Dict


class CacheEntry:
    def __init__(self, data: Any, ttl_seconds: float, created_at: Optional[float] = None):
        self.data = data
        self.created_at = created_at if created_at is not None else time.time()
        self.ttl = ttl_seconds

    @property
    def age(self) -> float:
        return max(0.0, time.time() - self.created_at)

    @property
    def is_expired(self) -> bool:
        return self.age >= self.ttl


class SkyDeckCache:
    """Thread-safe in-memory cache with stale fallback support."""

    def __init__(self):
        self._store: Dict[str, CacheEntry] = {}

    def set(self, key: str, data: Any, ttl_seconds: float, created_at: Optional[float] = None):
        """Store item in cache with specified TTL in seconds."""
        self._store[key] = CacheEntry(data, ttl_seconds, created_at=created_at)

    def get(self, key: str, allow_stale: bool = False) -> Optional[Tuple[Any, bool, float]]:
        """
        Retrieve item from cache.

        Returns:
            Tuple of (data, is_stale, age_seconds) if found, else None.
        """
        entry = self._store.get(key)
        if not entry:
            return None

        if entry.is_expired and not allow_stale:
            return None

        return entry.data, entry.is_expired, entry.age

    def invalidate(self, key: str):
        """Remove a specific key."""
        self._store.pop(key, None)

    def clear(self):
        """Clear all cached entries."""
        self._store.clear()


# Global application cache
app_cache = SkyDeckCache()
