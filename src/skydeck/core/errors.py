"""
Custom exception hierarchy for SkyDeck.

Ensures friendly, descriptive user messages are always available and that
raw traceback errors are never leaked to dashboard users.
"""

from typing import Optional


class SkyDeckError(Exception):
    """Base exception for all SkyDeck errors."""

    def __init__(self, message: str, user_friendly_message: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.user_friendly_message = user_friendly_message or message

    def to_user_message(self) -> str:
        """Return clean message suitable for UI display."""
        return self.user_friendly_message


class NetworkError(SkyDeckError):
    """Raised when internet connection is down or DNS resolution fails."""

    def __init__(self, message: str = "Unable to connect to the weather service."):
        super().__init__(
            message=message,
            user_friendly_message=(
                "🌐 Network connection issue. SkyDeck could not connect to the weather server. "
                "Please check your internet connection or switch to Offline Demo mode."
            ),
        )


class RequestTimeoutError(SkyDeckError):
    """Raised when an HTTP request times out."""

    def __init__(self, timeout_sec: float):
        super().__init__(
            message=f"Request timed out after {timeout_sec} seconds.",
            user_friendly_message=(
                f"⏱️ Weather service request timed out ({timeout_sec:.1f}s). "
                "The server may be experiencing high load. Please try refreshing."
            ),
        )


class RateLimitError(SkyDeckError):
    """Raised when Open-Meteo returns 429 Too Many Requests."""

    def __init__(self, retry_after: Optional[int] = None):
        wait_text = f" Please wait {retry_after} seconds before retrying." if retry_after else " Please pause a moment before retrying."
        super().__init__(
            message=f"Rate limit exceeded (HTTP 429). Retry after {retry_after}s.",
            user_friendly_message=f"🚦 API rate limit reached.{wait_text} Showing cached or offline data.",
        )
        self.retry_after = retry_after


class ServerError(SkyDeckError):
    """Raised when Open-Meteo responds with 5xx status."""

    def __init__(self, status_code: int, details: str = ""):
        super().__init__(
            message=f"Server returned HTTP {status_code}: {details}",
            user_friendly_message=(
                f"⚠️ The weather provider encountered an internal error (HTTP {status_code}). "
                "Previous cached data will be preserved."
            ),
        )
        self.status_code = status_code


class LocationNotFoundError(SkyDeckError):
    """Raised when geocoding search yields zero matches."""

    def __init__(self, query: str):
        super().__init__(
            message=f"No locations found matching query '{query}'.",
            user_friendly_message=(
                f"🔍 No location found matching '{query}'. "
                "Try checking your spelling, or enter a nearby major city."
            ),
        )
        self.query = query


class InvalidDataError(SkyDeckError):
    """Raised when API payload is corrupted or missing mandatory structures."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Invalid data received from provider: {reason}",
            user_friendly_message=(
                "📋 The received weather data format was unexpected. "
                "Using safe default indicators without crashing."
            ),
        )
