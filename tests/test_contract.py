"""
Contract tests verifying API payloads against Pydantic domain models.
"""

import json
from src.skydeck.domain.models import (
    GeocodedLocation,
    CurrentConditions,
    HourlyData,
    DailyData,
)


def test_parse_real_geocoding_sample():
    with open("sample_data/geocoding_london.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    results = [GeocodedLocation(**item) for item in data["results"]]
    assert len(results) >= 1
    assert results[0].name == "London"
    assert results[0].latitude == 51.50853


def test_parse_real_forecast_sample():
    with open("sample_data/forecast_london.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    current = CurrentConditions(**data["current"])
    assert current.temperature_2m is not None
    assert current.weather_code is not None

    hourly = HourlyData(**data["hourly"])
    assert len(hourly.time) > 0
    assert len(hourly.temperature_2m) == len(hourly.time)

    daily = DailyData(**data["daily"])
    assert len(daily.time) > 0
    assert len(daily.temperature_2m_max) == len(daily.time)


def test_missing_fields_contract_safety():
    """Ensure missing fields in payload do not crash Pydantic models."""
    empty_curr = CurrentConditions(time="2026-10-04T12:00")
    assert empty_curr.temperature_2m is None
    assert empty_curr.wind_speed_10m is None

    empty_hourly = HourlyData()
    assert empty_hourly.time == []
    assert empty_hourly.temperature_2m == []
