"""
Resilient HTTP Client for SkyDeck.

Single responsibility: Executes all outgoing HTTP requests with:
- Configurable timeout
- Exponential backoff retry on 5xx errors and timeouts (up to MAX_RETRIES)
- Rate-limit (HTTP 429) detection honoring Retry-After headers
- Safe error mapping into the SkyDeckError exception hierarchy
- Diagnostics and latency logging
"""

import time
import requests
from typing import Dict, Any, Optional
from config.settings import (
    REQUEST_TIMEOUT_SECONDS,
    MAX_RETRIES,
    INITIAL_BACKOFF_SECONDS,
    BACKOFF_FACTOR,
    RETRY_STATUS_CODES,
)
from src.skydeck.core.errors import (
    NetworkError,
    RequestTimeoutError,
    RateLimitError,
    ServerError,
    InvalidDataError,
)
from src.skydeck.core.diagnostics import diagnostics


class ResilientHttpClient:
    """Robust HTTP client with retries, backoff, and rate-limit awareness."""

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
        weight: int = 1,
    ) -> Any:
        """
        Execute an HTTP GET request with retries and backoff.

        Args:
            url: The target endpoint.
            params: Query parameters.
            timeout: Request timeout in seconds.
            weight: Cost weight for rate limit accounting.

        Returns:
            Parsed JSON object (dict or list).

        Raises:
            RateLimitError, NetworkError, RequestTimeoutError, ServerError, InvalidDataError.
        """
        attempt = 0
        backoff = INITIAL_BACKOFF_SECONDS
        last_exception = None

        while attempt < MAX_RETRIES:
            attempt += 1
            start_time = time.time()
            try:
                response = self.session.get(url, params=params, timeout=timeout)
                latency_ms = (time.time() - start_time) * 1000.0

                # Check for rate limiting
                if response.status_code == 429:
                    diagnostics.record_call(url, weight=weight, latency_ms=latency_ms, status=429)
                    retry_after_hdr = response.headers.get("Retry-After")
                    retry_after = int(retry_after_hdr) if retry_after_hdr and retry_after_hdr.isdigit() else 60
                    err = RateLimitError(retry_after=retry_after)
                    diagnostics.record_error(str(err))
                    raise err

                # Check for transient server errors (5xx)
                if response.status_code in RETRY_STATUS_CODES:
                    diagnostics.record_call(url, weight=weight, latency_ms=latency_ms, status=response.status_code)
                    if attempt < MAX_RETRIES:
                        time.sleep(backoff)
                        backoff *= BACKOFF_FACTOR
                        continue
                    else:
                        err = ServerError(response.status_code, response.text[:200])
                        diagnostics.record_error(str(err))
                        raise err

                # Non-200 responses
                if response.status_code != 200:
                    diagnostics.record_call(url, weight=weight, latency_ms=latency_ms, status=response.status_code)
                    err = ServerError(response.status_code, response.text[:200])
                    diagnostics.record_error(str(err))
                    raise err

                # Successful request
                diagnostics.record_call(url, weight=weight, latency_ms=latency_ms, status=200)
                try:
                    return response.json()
                except ValueError as e:
                    err = InvalidDataError(f"Response was not valid JSON: {str(e)}")
                    diagnostics.record_error(str(err))
                    raise err

            except requests.exceptions.Timeout:
                diagnostics.record_error(f"Timeout on {url} (attempt {attempt})")
                last_exception = RequestTimeoutError(timeout)
                if attempt < MAX_RETRIES:
                    time.sleep(backoff)
                    backoff *= BACKOFF_FACTOR
                else:
                    raise last_exception

            except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
                diagnostics.record_error(f"Connection failure on {url} (attempt {attempt}): {str(e)}")
                last_exception = NetworkError(f"Connection error: {str(e)}")
                if attempt < MAX_RETRIES:
                    time.sleep(backoff)
                    backoff *= BACKOFF_FACTOR
                else:
                    raise last_exception

        if last_exception:
            raise last_exception
        raise NetworkError("Maximum retries exhausted without a response.")


# Default client instance
default_http_client = ResilientHttpClient()
