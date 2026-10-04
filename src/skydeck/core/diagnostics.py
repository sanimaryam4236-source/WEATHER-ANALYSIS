"""
Diagnostics and API usage monitoring for SkyDeck.

Keeps runtime statistics on:
- API calls made vs free-tier limits (10,000/day, 5,000/hour, 600/minute)
- Cache hit ratio
- Estimated weighted request budget
- Latency history and error log
"""


from datetime import datetime
from typing import List, Dict, Any, Optional
from config.settings import DAILY_CALL_LIMIT


class DiagnosticsTracker:
    """Session-level tracker for network activity and health metrics."""

    def __init__(self):
        self.call_count: int = 0
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.estimated_cost_weight: int = 0
        self.last_fetch_time: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.call_history: List[Dict[str, Any]] = []

    def record_call(self, endpoint: str, weight: int = 1, latency_ms: float = 0.0, status: int = 200):
        """Record an outgoing API call."""
        self.call_count += 1
        self.estimated_cost_weight += weight
        self.last_fetch_time = datetime.now()
        self.call_history.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "endpoint": endpoint,
            "weight": weight,
            "latency_ms": round(latency_ms, 1),
            "status": status,
        })
        # Keep last 50 entries
        if len(self.call_history) > 50:
            self.call_history.pop(0)

    def record_cache_hit(self, key: str):
        """Record a cache hit."""
        self.cache_hits += 1

    def record_cache_miss(self, key: str):
        """Record a cache miss."""
        self.cache_misses += 1

    def record_error(self, err_msg: str):
        """Record the latest error."""
        self.last_error = f"{datetime.now().strftime('%H:%M:%S')}: {err_msg}"

    @property
    def hit_ratio_pct(self) -> float:
        """Percentage of requests served from cache."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return round((self.cache_hits / total) * 100.0, 1)

    @property
    def daily_budget_remaining(self) -> int:
        """Remaining calls in daily quota."""
        return max(0, DAILY_CALL_LIMIT - self.estimated_cost_weight)

    @property
    def daily_budget_used_pct(self) -> float:
        """Percentage of daily budget consumed."""
        return round((self.estimated_cost_weight / DAILY_CALL_LIMIT) * 100.0, 2)

    def summary(self) -> Dict[str, Any]:
        """Return diagnostic metrics dictionary."""
        return {
            "total_calls": self.call_count,
            "cost_weight": self.estimated_cost_weight,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_ratio": f"{self.hit_ratio_pct}%",
            "daily_budget_limit": DAILY_CALL_LIMIT,
            "daily_budget_used_pct": f"{self.daily_budget_used_pct}%",
            "daily_budget_remaining": self.daily_budget_remaining,
            "last_fetch": self.last_fetch_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_fetch_time else "None",
            "last_error": self.last_error or "None",
        }


# Global singleton tracker instance
diagnostics = DiagnosticsTracker()
