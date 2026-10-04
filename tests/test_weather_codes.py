"""
Unit tests for WMO weather code translation.
"""

from src.skydeck.domain.weather_codes import (
    get_weather_info,
    get_weather_icon,
    is_thunderstorm_code,
)


def test_clear_sky_code():
    info = get_weather_info(0)
    assert info.description == "Clear sky"
    assert info.category == "clear"
    assert not info.is_thunderstorm
    assert get_weather_icon(0, is_day=1) == "☀️"
    assert get_weather_icon(0, is_day=0) == "🌙"


def test_thunderstorm_detection():
    for code in [95, 96, 99]:
        assert is_thunderstorm_code(code) is True
        info = get_weather_info(code)
        assert info.is_thunderstorm is True
        assert info.is_severe is True


def test_unknown_code_fallback():
    info = get_weather_info(999)
    assert "Unknown weather" in info.description
    assert info.is_thunderstorm is False
