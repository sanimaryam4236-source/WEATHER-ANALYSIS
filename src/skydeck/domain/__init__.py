"""SkyDeck domain layer containing models, units, and weather code tables."""
from src.skydeck.domain.models import GeocodedLocation, WeatherReport, CurrentConditions, HourlyData, DailyData, AirQualityData, FreshnessInfo
from src.skydeck.domain.units import UnitSystem, UNIT_SYMBOLS, convert_temperature, convert_wind_speed
from src.skydeck.domain.weather_codes import get_weather_description, get_weather_icon

__all__ = [
    "GeocodedLocation",
    "WeatherReport",
    "CurrentConditions",
    "HourlyData",
    "DailyData",
    "AirQualityData",
    "FreshnessInfo",
    "UnitSystem",
    "UNIT_SYMBOLS",
    "convert_temperature",
    "convert_wind_speed",
    "get_weather_description",
    "get_weather_icon",
]

