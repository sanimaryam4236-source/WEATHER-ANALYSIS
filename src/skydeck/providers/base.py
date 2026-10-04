"""
Base weather provider interface for SkyDeck.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from src.skydeck.domain.models import (
    GeocodedLocation,
    WeatherReport,
    AirQualityData,
    DailyData,
)


class BaseWeatherProvider(ABC):
    """Abstract interface defining required provider capabilities."""

    @abstractmethod
    def search_locations(self, query: str, count: int = 5) -> List[GeocodedLocation]:
        """Search for cities/places matching query string."""
        pass

    @abstractmethod
    def get_forecast(self, location: GeocodedLocation, forecast_days: int = 16) -> WeatherReport:
        """Fetch current conditions, hourly, and daily forecasts for a location."""
        pass

    @abstractmethod
    def get_air_quality(self, location: GeocodedLocation) -> Optional[AirQualityData]:
        """Fetch atmospheric air quality and pollutant index data."""
        pass

    @abstractmethod
    def get_multi_city_forecast(self, locations: List[GeocodedLocation]) -> List[WeatherReport]:
        """Fetch basic current and daily forecast for multiple locations in a single batch."""
        pass

    @abstractmethod
    def get_historical_climate(
        self, location: GeocodedLocation, start_date: str, end_date: str
    ) -> Optional[DailyData]:
        """Fetch historical climate data for the location across a date range."""
        pass
