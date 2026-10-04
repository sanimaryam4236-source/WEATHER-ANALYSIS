"""
Offline Demo Provider for SkyDeck.

Loads real pre-recorded API responses directly from the sample_data/ directory.
Guarantees zero network calls: perfect for offline rehearsals, disconnected grading,
and unit testing.
"""

import json
import os
from datetime import datetime
from typing import List, Optional, Dict

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
from src.skydeck.core.errors import LocationNotFoundError
from src.skydeck.providers.base import BaseWeatherProvider


class DemoWeatherProvider(BaseWeatherProvider):
    """Zero-network provider backed by local sample JSON datasets."""

    def __init__(self, sample_dir: str = "sample_data"):
        self.sample_dir = sample_dir
        self.available_cities: Dict[str, str] = {
            "london": "london",
            "new york": "new_york",
            "tokyo": "tokyo",
            "paris": "paris",
            "islamabad": "london",
            "lahore": "london",
            "karachi": "london",
            "rawalpindi": "london",
            "peshawar": "london",
        }
        self.bundled_cities = [
            GeocodedLocation(id=1176615, name="Islamabad", latitude=33.6844, longitude=73.0479, country="Pakistan", admin1="Federal Capital Territory", timezone="Asia/Karachi"),
            GeocodedLocation(id=1172451, name="Lahore", latitude=31.5204, longitude=74.3587, country="Pakistan", admin1="Punjab", timezone="Asia/Karachi"),
            GeocodedLocation(id=1174872, name="Karachi", latitude=24.8607, longitude=67.0011, country="Pakistan", admin1="Sindh", timezone="Asia/Karachi"),
            GeocodedLocation(id=1166993, name="Rawalpindi", latitude=33.5986, longitude=73.0441, country="Pakistan", admin1="Punjab", timezone="Asia/Karachi"),
            GeocodedLocation(id=1168194, name="Peshawar", latitude=34.0151, longitude=71.5249, country="Pakistan", admin1="Khyber Pakhtunkhwa", timezone="Asia/Karachi"),
        ]

    def _get_path(self, filename: str) -> str:
        return os.path.join(self.sample_dir, filename)

    def _resolve_city_key(self, name: str) -> str:
        name_lower = name.lower().strip()
        for k, v in self.available_cities.items():
            if k in name_lower:
                return v
        return "london"  # Default fallback

    def search_locations(self, query: str, count: int = 5) -> List[GeocodedLocation]:
        """Search across offline demo files and bundled locations."""
        clean = query.strip().lower()
        if len(clean) < 2:
            return []

        results: List[GeocodedLocation] = []

        # Check bundled cities first
        for loc in self.bundled_cities:
            if clean in loc.name.lower() or (loc.country and clean in loc.country.lower()) or (loc.admin1 and clean in loc.admin1.lower()):
                results.append(loc)

        # Find matching sample geocoding files
        for city_key in set(self.available_cities.values()):
            path = self._get_path(f"geocoding_{city_key}.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("results", []):
                        g_loc = GeocodedLocation(**item)
                        if clean in g_loc.name.lower() or (g_loc.country and clean in g_loc.country.lower()):
                            if not any(r.id == g_loc.id for r in results):
                                results.append(g_loc)

        if not results:
            # Fallback to London geocoding if query was a generic test
            fallback_path = self._get_path("geocoding_london.json")
            if os.path.exists(fallback_path):
                with open(fallback_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    results = [GeocodedLocation(**item) for item in data.get("results", [])]
            else:
                raise LocationNotFoundError(query)

        return results[:count]

    def get_forecast(self, location: GeocodedLocation, forecast_days: int = 16) -> WeatherReport:
        """Load offline forecast from sample_data."""
        city_key = self._resolve_city_key(location.name)
        filename = f"forecast_{city_key}.json"
        path = self._get_path(filename)

        if not os.path.exists(path):
            path = self._get_path("forecast_london.json")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        current = CurrentConditions(**data.get("current", {}))
        hourly = HourlyData(**data.get("hourly", {}))
        daily = DailyData(**data.get("daily", {}))

        # Truncate hourly/daily if forecast_days requested is smaller
        if forecast_days and forecast_days < len(daily.time):
            daily.time = daily.time[:forecast_days]
            hourly_limit = forecast_days * 24
            hourly.time = hourly.time[:hourly_limit]

        aq = self.get_air_quality(location)

        freshness = FreshnessInfo(
            status=DataSourceStatus.OFFLINE_DEMO,
            fetched_at=datetime.now(),
            age_seconds=0.0,
        )

        return WeatherReport(
            location=location,
            current=current,
            hourly=hourly,
            daily=daily,
            air_quality=aq,
            freshness=freshness,
        )

    def get_air_quality(self, location: GeocodedLocation) -> Optional[AirQualityData]:
        """Load offline air quality."""
        city_key = self._resolve_city_key(location.name)
        filename = f"air_quality_{city_key}.json"
        path = self._get_path(filename)

        if not os.path.exists(path):
            path = self._get_path("air_quality_london.json")

        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AirQualityData(**data.get("hourly", {}))
        return None

    def get_multi_city_forecast(self, locations: List[GeocodedLocation]) -> List[WeatherReport]:
        """Return demo forecasts for multiple locations."""
        return [self.get_forecast(loc, forecast_days=3) for loc in locations[:5]]

    def get_historical_climate(
        self, location: GeocodedLocation, start_date: str, end_date: str
    ) -> Optional[DailyData]:
        """Load sample archive file."""
        path = self._get_path("historical_archive_london.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return DailyData(**data.get("daily", {}))
        return None
