"""
Domain data models for SkyDeck.

Uses Pydantic for strong typing, data validation, and null-safety.
All fields that can be absent from API responses default to None or empty lists,
ensuring missing data never crashes the app and can be rendered as '—'.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class DataSourceStatus(str, Enum):
    LIVE = "Live API"
    CACHED = "Cached"
    OFFLINE_DEMO = "Offline Demo"
    STALE_FALLBACK = "Stale Fallback (Offline)"


class GeocodedLocation(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    country: Optional[str] = None
    country_code: Optional[str] = None
    admin1: Optional[str] = None
    admin2: Optional[str] = None
    timezone: str = "UTC"
    elevation: Optional[float] = None
    population: Optional[int] = None

    @property
    def display_name(self) -> str:
        """Formatted human-friendly location string."""
        parts = [self.name]
        if self.admin1 and self.admin1 != self.name:
            parts.append(self.admin1)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)


class CurrentConditions(BaseModel):
    time: str
    temperature_2m: Optional[float] = None
    apparent_temperature: Optional[float] = None
    relative_humidity_2m: Optional[float] = None
    precipitation: Optional[float] = None
    weather_code: Optional[int] = None
    cloud_cover: Optional[float] = None
    pressure_msl: Optional[float] = None
    wind_speed_10m: Optional[float] = None
    wind_direction_10m: Optional[float] = None
    wind_gusts_10m: Optional[float] = None
    is_day: int = 1


class HourlyData(BaseModel):
    time: List[str] = Field(default_factory=list)
    temperature_2m: List[Optional[float]] = Field(default_factory=list)
    apparent_temperature: List[Optional[float]] = Field(default_factory=list)
    relative_humidity_2m: List[Optional[float]] = Field(default_factory=list)
    dew_point_2m: List[Optional[float]] = Field(default_factory=list)
    precipitation_probability: List[Optional[float]] = Field(default_factory=list)
    precipitation: List[Optional[float]] = Field(default_factory=list)
    weather_code: List[Optional[int]] = Field(default_factory=list)
    pressure_msl: List[Optional[float]] = Field(default_factory=list)
    cloud_cover: List[Optional[float]] = Field(default_factory=list)
    visibility: List[Optional[float]] = Field(default_factory=list)
    wind_speed_10m: List[Optional[float]] = Field(default_factory=list)
    wind_direction_10m: List[Optional[float]] = Field(default_factory=list)
    wind_gusts_10m: List[Optional[float]] = Field(default_factory=list)
    uv_index: List[Optional[float]] = Field(default_factory=list)


class DailyData(BaseModel):
    time: List[str] = Field(default_factory=list)
    weather_code: List[Optional[int]] = Field(default_factory=list)
    temperature_2m_max: List[Optional[float]] = Field(default_factory=list)
    temperature_2m_min: List[Optional[float]] = Field(default_factory=list)
    apparent_temperature_max: List[Optional[float]] = Field(default_factory=list)
    apparent_temperature_min: List[Optional[float]] = Field(default_factory=list)
    sunrise: List[Optional[str]] = Field(default_factory=list)
    sunset: List[Optional[str]] = Field(default_factory=list)
    uv_index_max: List[Optional[float]] = Field(default_factory=list)
    precipitation_sum: List[Optional[float]] = Field(default_factory=list)
    precipitation_probability_max: List[Optional[float]] = Field(default_factory=list)
    wind_speed_10m_max: List[Optional[float]] = Field(default_factory=list)
    wind_gusts_10m_max: List[Optional[float]] = Field(default_factory=list)
    wind_direction_10m_dominant: List[Optional[float]] = Field(default_factory=list)


class AirQualityData(BaseModel):
    time: List[str] = Field(default_factory=list)
    pm10: List[Optional[float]] = Field(default_factory=list)
    pm2_5: List[Optional[float]] = Field(default_factory=list)
    carbon_monoxide: List[Optional[float]] = Field(default_factory=list)
    nitrogen_dioxide: List[Optional[float]] = Field(default_factory=list)
    sulphur_dioxide: List[Optional[float]] = Field(default_factory=list)
    ozone: List[Optional[float]] = Field(default_factory=list)
    uv_index: List[Optional[float]] = Field(default_factory=list)
    european_aqi: List[Optional[float]] = Field(default_factory=list)
    us_aqi: List[Optional[float]] = Field(default_factory=list)


class AdvisoryItem(BaseModel):
    advisory_type: str
    title: str
    severity: str    # "info", "warning", "danger"
    description: str
    trigger_value: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    disclaimer: str


class SuitabilityScore(BaseModel):
    activity_key: str
    activity_name: str
    icon: str
    score: int          # 0 to 100
    rating: str         # "Optimal", "Good", "Marginal", "Poor", "Hazardous"
    best_window: str    # e.g. "09:00 - 12:00"
    breakdown: Dict[str, str]
    is_blocked: bool = False
    block_reason: Optional[str] = None


class DailyBriefing(BaseModel):
    date: str
    day_label: str       # "Today", "Tomorrow", "Thursday"
    headline: str
    temperature_summary: str
    precipitation_summary: str
    wind_summary: str
    advisories: List[str] = Field(default_factory=list)


class FreshnessInfo(BaseModel):
    status: DataSourceStatus
    fetched_at: datetime
    age_seconds: float = 0.0

    @property
    def badge_text(self) -> str:
        if self.status == DataSourceStatus.LIVE:
            return "🟢 Live API"
        elif self.status == DataSourceStatus.CACHED:
            mins = int(self.age_seconds // 60)
            return f"🟡 Cached ({mins}m ago)"
        elif self.status == DataSourceStatus.OFFLINE_DEMO:
            return "🟣 Offline Demo Mode"
        else:
            return "🟠 Stale Cache (Offline Fallback)"


class WeatherReport(BaseModel):
    location: GeocodedLocation
    current: CurrentConditions
    hourly: HourlyData
    daily: DailyData
    air_quality: Optional[AirQualityData] = None
    freshness: FreshnessInfo
