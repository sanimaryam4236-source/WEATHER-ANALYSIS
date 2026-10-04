"""
Unit tests for Search City flow and DemoProvider location search.
"""

from src.skydeck.providers.demo_provider import DemoWeatherProvider


def test_short_search_query_returns_empty():
    provider = DemoWeatherProvider()
    results = provider.search_locations("a", count=5)
    assert len(results) == 0


def test_search_bundled_pakistani_city():
    provider = DemoWeatherProvider()
    results = provider.search_locations("Islamabad", count=5)
    assert len(results) >= 1
    assert results[0].name == "Islamabad"
    assert results[0].country == "Pakistan"


def test_search_sample_data_city():
    provider = DemoWeatherProvider()
    results = provider.search_locations("London", count=5)
    assert len(results) >= 1
    assert any("London" in loc.name for loc in results)


def test_search_unknown_city_returns_fallback_or_error():
    provider = DemoWeatherProvider()
    results = provider.search_locations("XYZNonExistentCity123", count=5)
    assert len(results) >= 1
