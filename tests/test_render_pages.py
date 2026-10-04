"""
Render-every-page automated test harness for SkyDeck.

Verifies that every navigation page renders cleanly without exceptions across:
- Live mode (OpenMeteoProvider with live status) and Offline Demo mode (DemoWeatherProvider)
- Metric and Imperial unit systems
"""

import json
from unittest.mock import patch
import pytest

from src.skydeck.domain.models import GeocodedLocation
from src.skydeck.domain.units import UnitSystem
from src.skydeck.providers.demo_provider import DemoWeatherProvider
from src.skydeck.providers.open_meteo import OpenMeteoProvider
from src.skydeck.storage.saved_cities import saved_cities_storage
from src.skydeck.ui.tabs import (
    render_home_page,
    render_weather_page,
    render_forecast_page,
    render_activity_guide_page,
    render_graphs_page,
    render_settings_and_cities_page,
)


def _get_report_and_provider(mode: str):
    last_saved = saved_cities_storage.get_last_active_city()
    loc = GeocodedLocation(**last_saved)
    if mode == "demo":
        provider = DemoWeatherProvider()
        report = provider.get_forecast(loc, forecast_days=16)
        return report, provider
    else:
        provider = OpenMeteoProvider()

        def mock_get(url, params=None, weight=1):
            if "air-quality" in url:
                with open("sample_data/air_quality_london.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            with open("sample_data/forecast_london.json", "r", encoding="utf-8") as f:
                return json.load(f)

        with patch.object(provider.client, "get", side_effect=mock_get):
            report = provider.get_forecast(loc, forecast_days=16)
        return report, provider


@pytest.mark.parametrize("mode", ["live", "demo"])
@pytest.mark.parametrize("units", [UnitSystem.METRIC, UnitSystem.IMPERIAL])
def test_render_home_page(mode, units):
    report, provider = _get_report_and_provider(mode)
    render_home_page(report, units, provider)


@pytest.mark.parametrize("mode", ["live", "demo"])
@pytest.mark.parametrize("units", [UnitSystem.METRIC, UnitSystem.IMPERIAL])
def test_render_weather_page(mode, units):
    report, _ = _get_report_and_provider(mode)
    render_weather_page(report, units)


@pytest.mark.parametrize("mode", ["live", "demo"])
@pytest.mark.parametrize("units", [UnitSystem.METRIC, UnitSystem.IMPERIAL])
def test_render_forecast_page(mode, units):
    report, _ = _get_report_and_provider(mode)
    render_forecast_page(report, units)


@pytest.mark.parametrize("mode", ["live", "demo"])
@pytest.mark.parametrize("units", [UnitSystem.METRIC, UnitSystem.IMPERIAL])
def test_render_activity_guide_page(mode, units):
    report, _ = _get_report_and_provider(mode)
    render_activity_guide_page(report)


@pytest.mark.parametrize("mode", ["live", "demo"])
@pytest.mark.parametrize("units", [UnitSystem.METRIC, UnitSystem.IMPERIAL])
def test_render_graphs_page(mode, units):
    report, _ = _get_report_and_provider(mode)
    render_graphs_page(report, units)


@pytest.mark.parametrize("mode", ["live", "demo"])
@pytest.mark.parametrize("units", [UnitSystem.METRIC, UnitSystem.IMPERIAL])
def test_render_settings_and_cities_page(mode, units):
    report, provider = _get_report_and_provider(mode)
    render_settings_and_cities_page(provider, report)

