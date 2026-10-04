"""
Unit and integration tests for DemoWeatherProvider (Offline Demo Mode).
"""

from src.skydeck.providers.demo_provider import DemoWeatherProvider
from src.skydeck.domain.models import DataSourceStatus, GeocodedLocation


def test_demo_provider_search():
    provider = DemoWeatherProvider()
    results = provider.search_locations("London")
    assert len(results) > 0
    assert any("London" in r.name for r in results)


def test_demo_provider_forecast():
    provider = DemoWeatherProvider()
    loc = GeocodedLocation(
        id=2643743,
        name="London",
        latitude=51.50853,
        longitude=-0.12574,
        country="United Kingdom",
    )
    report = provider.get_forecast(loc, forecast_days=7)

    assert report is not None
    assert report.freshness.status == DataSourceStatus.OFFLINE_DEMO
    assert report.current.temperature_2m is not None
    assert len(report.daily.time) == 7
    assert len(report.hourly.time) == 7 * 24
    assert report.air_quality is not None
