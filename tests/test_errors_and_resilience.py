"""
Failure tests: Verify error translation, retries, and stale cache fallback.
"""

from unittest.mock import MagicMock, patch
import pytest

from src.skydeck.core.errors import (
    NetworkError,
    RateLimitError,
    ServerError,
)
from src.skydeck.core.http_client import ResilientHttpClient
from src.skydeck.core.cache import SkyDeckCache
from src.skydeck.domain.models import DataSourceStatus, GeocodedLocation
from src.skydeck.providers.open_meteo import OpenMeteoProvider


def test_rate_limit_detection():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers = {"Retry-After": "45"}
    mock_session.get.return_value = mock_response

    client = ResilientHttpClient(session=mock_session)
    with pytest.raises(RateLimitError) as exc_info:
        client.get("https://api.test/rate-limit")

    assert exc_info.value.retry_after == 45
    assert "rate limit reached" in exc_info.value.to_user_message().lower()


def test_server_error_exhaustion():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "Service Unavailable"
    mock_session.get.return_value = mock_response

    client = ResilientHttpClient(session=mock_session)
    # Patch time.sleep to run instantly
    with patch("time.sleep"):
        with pytest.raises(ServerError) as exc_info:
            client.get("https://api.test/503")

    assert exc_info.value.status_code == 503


def test_stale_cache_fallback():
    """Verify that if live API fails, stale cached data is returned with STALE_FALLBACK status."""
    cache = SkyDeckCache()
    client = MagicMock()
    # Mock client to fail with NetworkError
    client.get.side_effect = NetworkError("Internet disconnected")

    provider = OpenMeteoProvider(client=client, cache=cache)
    loc = GeocodedLocation(
        id=2643743,
        name="London",
        latitude=51.50853,
        longitude=-0.12574,
        country="United Kingdom",
    )

    # Pre-populate cache with data (simulating a previous good fetch)
    cache_key = f"forecast_{loc.latitude:.4f}_{loc.longitude:.4f}_16"
    sample_report = {
        "location": loc.model_dump(),
        "current": {"time": "2026-10-04T12:00", "temperature_2m": 19.5},
        "hourly": {"time": ["2026-10-04T12:00"], "temperature_2m": [19.5]},
        "daily": {"time": ["2026-10-04"], "temperature_2m_max": [22.0]},
        "freshness": {"status": "Live API", "fetched_at": "2026-10-04T12:00:00", "age_seconds": 3600},
    }
    import time
    # Expired entry (ttl = 60s, created 3600s ago)
    cache.set(cache_key, sample_report, ttl_seconds=60, created_at=time.time() - 3600)

    # Fetch should catch NetworkError and return the stale report with STALE_FALLBACK
    fallback_report = provider.get_forecast(loc, forecast_days=16)
    assert fallback_report is not None
    assert fallback_report.freshness.status == DataSourceStatus.STALE_FALLBACK
    assert fallback_report.current.temperature_2m == 19.5
