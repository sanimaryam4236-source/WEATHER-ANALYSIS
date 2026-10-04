"""
Unit tests for unit conversion and formatting.
"""

from src.skydeck.domain.units import (
    UnitSystem,
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
    kmh_to_mph,
    mm_to_inches,
    convert_temperature,
    convert_wind_speed,
    format_value,
)


def test_temperature_conversions():
    # 0°C -> 32°F
    assert celsius_to_fahrenheit(0.0) == 32.0
    # 100°C -> 212°F
    assert celsius_to_fahrenheit(100.0) == 212.0
    # 32°F -> 0°C
    assert fahrenheit_to_celsius(32.0) == 0.0
    # None safety
    assert celsius_to_fahrenheit(None) is None


def test_speed_and_precipitation():
    # 100 km/h -> ~62.1 mph
    assert kmh_to_mph(100.0) == 62.1
    # 25.4 mm -> 1.00 inch
    assert mm_to_inches(25.4) == 1.0
    # None safety
    assert kmh_to_mph(None) is None
    assert mm_to_inches(None) is None


def test_convert_by_system():
    assert convert_temperature(20.0, UnitSystem.METRIC) == 20.0
    assert convert_temperature(20.0, UnitSystem.IMPERIAL) == 68.0

    assert convert_wind_speed(50.0, UnitSystem.METRIC) == 50.0
    assert convert_wind_speed(50.0, UnitSystem.IMPERIAL) == 31.1


def test_format_value_null_safety():
    # Never show fake zeros for None!
    assert format_value(None, "°C", fallback="—") == "—"
    assert format_value(22.456, "°C", precision=1) == "22.5 °C"
    assert format_value(15, "", precision=0) == "15"
