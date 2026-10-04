"""
Live Open-Meteo API Provider.

Fetches geocoding, high-resolution forecast, air quality, multi-location,
and historical data. Applies caching and stale-fallback on network failures.
"""

from datetime import datetime
from typing import List, Optional

from config.settings import (
    GEOCODING_API_URL,
    FORECAST_API_URL,
    AIR_QUALITY_API_URL,
    ARCHIVE_API_URL,
    CACHE_TTL_GEOCODING,
    CACHE_TTL_FORECAST,
    CACHE_TTL_AIR_QUALITY,
    CACHE_TTL_ARCHIVE,
    CURRENT_PARAMS,
    HOURLY_PARAMS,
    DAILY_PARAMS,
    AIR_QUALITY_HOURLY_PARAMS,
)
from src.skydeck.core.http_client import ResilientHttpClient, default_http_client
from src.skydeck.core.cache import SkyDeckCache, app_cache
from src.skydeck.core.diagnostics import diagnostics
from src.skydeck.core.errors import LocationNotFoundError, SkyDeckError
from src.skydeck.domain.models import (
    GeocodedLocation,
    CurrentConditions,
    HourlyData,
    DailyData,
    AirQualityData,
    WeatherReport,
    FreshnessInfo,
    DataSourceStatus,
)
from src.skydeck.providers.base import BaseWeatherProvider


class OpenMeteoProvider(BaseWeatherProvider):
    """Production provider using Open-Meteo endpoints with resiliency."""

    def __init__(
        self,
        client: Optional[ResilientHttpClient] = None,
        cache: Optional[SkyDeckCache] = None,
    ):
        self.client = client or default_http_client
        self.cache = cache or app_cache

    def search_locations(self, query: str, count: int = 5) -> List[GeocodedLocation]:
        """Search locations with 24h caching."""
        clean_query = query.strip()
        if len(clean_query) < 2:
            return []

        cache_key = f"geo_{clean_query.lower()}_{count}"
        cached = self.cache.get(cache_key)
        if cached:
            diagnostics.record_cache_hit(cache_key)
            data, _, _ = cached
            return [GeocodedLocation(**item) for item in data]

        diagnostics.record_cache_miss(cache_key)
        params = {
            "name": clean_query,
            "count": count,
            "language": "en",
            "format": "json",
        }

        try:
            payload = self.client.get(GEOCODING_API_URL, params=params, weight=1)
            results = payload.get("results", [])
            if not results:
                raise LocationNotFoundError(clean_query)

            locations = [GeocodedLocation(**item) for item in results]
            self.cache.set(cache_key, [loc.model_dump() for loc in locations], CACHE_TTL_GEOCODING)
            return locations
        except SkyDeckError:
            # Check stale cache
            stale = self.cache.get(cache_key, allow_stale=True)
            if stale:
                data, _, _ = stale
                return [GeocodedLocation(**item) for item in data]
            raise

    def get_forecast(self, location: GeocodedLocation, forecast_days: int = 16) -> WeatherReport:
        """Fetch forecast with 15-minute caching and stale fallback."""
        cache_key = f"forecast_{location.latitude:.4f}_{location.longitude:.4f}_{forecast_days}"
        cached = self.cache.get(cache_key)
        if cached:
            diagnostics.record_cache_hit(cache_key)
            data, is_stale, age = cached
            report = WeatherReport(**data)
            report.freshness = FreshnessInfo(
                status=DataSourceStatus.CACHED if not is_stale else DataSourceStatus.STALE_FALLBACK,
                fetched_at=datetime.fromtimestamp(datetime.now().timestamp() - age),
                age_seconds=age,
            )
            return report

        diagnostics.record_cache_miss(cache_key)
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "current": CURRENT_PARAMS,
            "hourly": HOURLY_PARAMS,
            "daily": DAILY_PARAMS,
            "timezone": location.timezone or "auto",
            "forecast_days": min(max(forecast_days, 1), 16),
        }

        try:
            payload = self.client.get(FORECAST_API_URL, params=params, weight=1)
            current_raw = payload.get("current", {})
            hourly_raw = payload.get("hourly", {})
            daily_raw = payload.get("daily", {})

            current = CurrentConditions(**current_raw)
            hourly = HourlyData(**hourly_raw)
            daily = DailyData(**daily_raw)

            # Optional air quality fetch
            aq = None
            try:
                aq = self.get_air_quality(location)
            except Exception:
                # Air quality failure shouldn't break the main weather dashboard
                pass

            freshness = FreshnessInfo(
                status=DataSourceStatus.LIVE,
                fetched_at=datetime.now(),
                age_seconds=0.0,
            )

            report = WeatherReport(
                location=location,
                current=current,
                hourly=hourly,
                daily=daily,
                air_quality=aq,
                freshness=freshness,
            )

            self.cache.set(cache_key, report.model_dump(), CACHE_TTL_FORECAST)
            return report

        except SkyDeckError as err:
            # Fallback to stale cache if network or server failed
            stale = self.cache.get(cache_key, allow_stale=True)
            if stale:
                data, _, age = stale
                report = WeatherReport(**data)
                report.freshness = FreshnessInfo(
                    status=DataSourceStatus.STALE_FALLBACK,
                    fetched_at=datetime.fromtimestamp(datetime.now().timestamp() - age),
                    age_seconds=age,
                )
                return report
            raise err

    def get_air_quality(self, location: GeocodedLocation) -> Optional[AirQualityData]:
        """Fetch modelled air quality with 30-minute caching."""
        cache_key = f"aq_{location.latitude:.4f}_{location.longitude:.4f}"
        cached = self.cache.get(cache_key)
        if cached:
            diagnostics.record_cache_hit(cache_key)
            data, _, _ = cached
            return AirQualityData(**data)

        diagnostics.record_cache_miss(cache_key)
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "hourly": AIR_QUALITY_HOURLY_PARAMS,
            "timezone": location.timezone or "auto",
        }

        try:
            payload = self.client.get(AIR_QUALITY_API_URL, params=params, weight=1)
            hourly_raw = payload.get("hourly", {})
            aq = AirQualityData(**hourly_raw)
            self.cache.set(cache_key, aq.model_dump(), CACHE_TTL_AIR_QUALITY)
            return aq
        except Exception:
            stale = self.cache.get(cache_key, allow_stale=True)
            if stale:
                data, _, _ = stale
                return AirQualityData(**data)
            return None

    def get_multi_city_forecast(self, locations: List[GeocodedLocation]) -> List[WeatherReport]:
        """
        Batch query up to 5 cities in a single HTTP request to minimize API cost.
        """
        if not locations:
            return []

        batch_locations = locations[:5]
        lats = [loc.latitude for loc in batch_locations]
        lons = [loc.longitude for loc in batch_locations]

        params = {
            "latitude": lats,
            "longitude": lons,
            "current": ["temperature_2m", "weather_code", "wind_speed_10m", "relative_humidity_2m", "precipitation"],
            "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max", "weather_code"],
            "timezone": "auto",
            "forecast_days": 3,
        }

        try:
            payload = self.client.get(FORECAST_API_URL, params=params, weight=len(batch_locations))
            # Open-Meteo returns a list of dictionaries for multi-location
            reports: List[WeatherReport] = []
            if isinstance(payload, list):
                for loc, p in zip(batch_locations, payload):
                    current = CurrentConditions(**p.get("current", {}))
                    daily = DailyData(**p.get("daily", {}))
                    hourly = HourlyData()
                    reports.append(WeatherReport(
                        location=loc,
                        current=current,
                        hourly=hourly,
                        daily=daily,
                        freshness=FreshnessInfo(status=DataSourceStatus.LIVE, fetched_at=datetime.now()),
                    ))
            elif isinstance(payload, dict):
                # Single result returned
                loc = batch_locations[0]
                current = CurrentConditions(**payload.get("current", {}))
                daily = DailyData(**payload.get("daily", {}))
                reports.append(WeatherReport(
                    location=loc,
                    current=current,
                    hourly=HourlyData(),
                    daily=daily,
                    freshness=FreshnessInfo(status=DataSourceStatus.LIVE, fetched_at=datetime.now()),
                ))
            return reports
        except SkyDeckError:
            # Fallback to single requests from cache if batch fails
            reports = []
            for loc in batch_locations:
                try:
                    reports.append(self.get_forecast(loc, forecast_days=3))
                except Exception:
                    pass
            return reports

    def get_historical_climate(
        self, location: GeocodedLocation, start_date: str, end_date: str
    ) -> Optional[DailyData]:
        """Fetch historical climate data from the archive endpoint with 7-day caching."""
        cache_key = f"archive_{location.latitude:.4f}_{location.longitude:.4f}_{start_date}_{end_date}"
        cached = self.cache.get(cache_key)
        if cached:
            diagnostics.record_cache_hit(cache_key)
            data, _, _ = cached
            return DailyData(**data)

        diagnostics.record_cache_miss(cache_key)
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
            "timezone": location.timezone or "auto",
        }

        try:
            payload = self.client.get(ARCHIVE_API_URL, params=params, weight=1)
            daily_raw = payload.get("daily", {})
            daily = DailyData(**daily_raw)
            self.cache.set(cache_key, daily.model_dump(), CACHE_TTL_ARCHIVE)
            return daily
        except Exception:
            return None
