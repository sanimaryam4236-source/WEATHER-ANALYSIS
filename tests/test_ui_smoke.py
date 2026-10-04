"""
UI Smoke and integration tests.

Verifies end-to-end data pipeline from both DemoProvider and OpenMeteoProvider
(with mocked HTTP), through domain models, chart generators, service layers,
and every tab rendering function — in both Metric and Imperial unit systems.

A crash in any tab or any unit system causes the test to fail.
"""

from unittest.mock import MagicMock, patch
import pytest
import json

from src.skydeck.providers.demo_provider import DemoWeatherProvider
from src.skydeck.providers.open_meteo import OpenMeteoProvider
from src.skydeck.domain.models import GeocodedLocation
from src.skydeck.domain.units import UnitSystem
from src.skydeck.ui.charts import (
    create_hourly_temperature_chart,
    create_precipitation_chart,
    create_daily_temperature_band_chart,
    create_wind_rose_chart,
    create_air_quality_chart,
    create_temperature_heatmap,
)
from src.skydeck.services.advisories import evaluate_advisories
from src.skydeck.services.suitability import calculate_suitability
from src.skydeck.services.briefing import generate_briefings
from src.skydeck.services.compare import compare_and_rank_cities
from src.skydeck.ui.tabs import (
    render_overview_tab,
    render_forecast_tab,
    render_air_quality_tab,
    render_activities_tab,
    render_compare_tab,
    render_diagnostics_tab,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def london_loc():
    return GeocodedLocation(
        id=2643743,
        name="London",
        latitude=51.50853,
        longitude=-0.12574,
        country="United Kingdom",
        timezone="Europe/London",
    )


@pytest.fixture
def demo_provider():
    return DemoWeatherProvider()


@pytest.fixture
def demo_report(demo_provider, london_loc):
    return demo_provider.get_forecast(london_loc, forecast_days=16)


@pytest.fixture
def mock_open_meteo_report(london_loc, demo_provider):
    """Return a live-tagged report built from demo data to test OpenMeteoProvider path."""
    with open("sample_data/forecast_london.json", "r", encoding="utf-8") as f:
        fc_payload = json.load(f)
    with open("sample_data/air_quality_london.json", "r", encoding="utf-8") as f:
        aq_payload = json.load(f)
    with open("sample_data/geocoding_london.json", "r", encoding="utf-8") as f:
        geo_payload = json.load(f)

    mock_client = MagicMock()
    # Return different payloads based on URL pattern
    def side_effect(url, **kwargs):
        if "geocoding" in url:
            return geo_payload
        elif "air-quality" in url:
            return aq_payload
        else:
            return fc_payload
    mock_client.get.side_effect = side_effect

    provider = OpenMeteoProvider(client=mock_client)
    return provider.get_forecast(london_loc, forecast_days=16)


# ─── Issue #4: Charts — demo mode, both unit systems ─────────────────────────

@pytest.mark.parametrize("units", [UnitSystem.METRIC, UnitSystem.IMPERIAL])
def test_all_charts_render(demo_report, units):
    """Every chart builder must succeed with demo data in both unit systems."""
    fig1 = create_hourly_temperature_chart(demo_report.hourly, units, hours_limit=48)
    assert fig1 is not None, "Hourly temp chart failed"

    fig2 = create_precipitation_chart(demo_report.hourly, units, hours_limit=48)
    assert fig2 is not None, "Precipitation chart failed"

    fig3 = create_daily_temperature_band_chart(demo_report.daily, units, days_limit=16)
    assert fig3 is not None, "Daily band chart failed"

    fig4 = create_wind_rose_chart(demo_report.hourly, units, hours_limit=48)
    assert fig4 is not None, "Wind rose chart failed"

    if demo_report.air_quality:
        fig5 = create_air_quality_chart(demo_report.air_quality, hours_limit=48)
        assert fig5 is not None, "Air quality chart failed"

    fig6 = create_temperature_heatmap(demo_report.hourly, units, days_limit=7)
    assert fig6 is not None, "Thermal heatmap chart failed"


# ─── Issue #4: Pure services — both unit systems ─────────────────────────────

@pytest.mark.parametrize("units", [UnitSystem.METRIC, UnitSystem.IMPERIAL])
def test_all_services(demo_report, units):
    """All service layers must produce valid output with demo data."""
    advisories = evaluate_advisories(
        demo_report.current, demo_report.hourly, demo_report.daily, demo_report.air_quality
    )
    assert isinstance(advisories, list)

    scores = calculate_suitability(demo_report.current, demo_report.hourly)
    assert len(scores) >= 5
    for s in scores:
        assert 0 <= s.score <= 100, f"Score out of range: {s.score}"
        assert s.rating in ("Optimal", "Excellent", "Good", "Marginal", "Moderate", "Poor", "Hazardous")
        assert len(s.breakdown) > 0

    briefings = generate_briefings(demo_report.current, demo_report.hourly, demo_report.daily)
    assert len(briefings) >= 1

    ranked = compare_and_rank_cities([demo_report], "outdoor_sport")
    assert len(ranked) == 1


# ─── Issue #4: Tab rendering — demo mode, both unit systems ──────────────────

def _make_mock_streamlit():
    """Return a MagicMock that accepts all st.* calls without crashing."""
    mock_st = MagicMock()

    def _columns(spec):
        """Return as many column mocks as columns requested."""
        if isinstance(spec, (list, tuple)):
            n = len(spec)
        elif isinstance(spec, int):
            n = spec
        else:
            n = 4  # safe fallback
        return [MagicMock() for _ in range(n)]

    mock_st.columns.side_effect = _columns
    mock_st.tabs.return_value = [MagicMock() for _ in range(6)]
    mock_st.expander.return_value.__enter__ = lambda s: s
    mock_st.expander.return_value.__exit__ = MagicMock(return_value=False)
    mock_st.container.return_value.__enter__ = lambda s: s
    mock_st.container.return_value.__exit__ = MagicMock(return_value=False)
    return mock_st


@pytest.mark.parametrize("units", [UnitSystem.METRIC, UnitSystem.IMPERIAL])
def test_tab_overview_renders(demo_provider, demo_report, units):
    """Tab 1 (Overview) must render without exceptions in both unit systems."""
    with patch("src.skydeck.ui.tabs.st", _make_mock_streamlit()), \
         patch("src.skydeck.ui.components.st", _make_mock_streamlit()):
        render_overview_tab(demo_report, units)


@pytest.mark.parametrize("units", [UnitSystem.METRIC, UnitSystem.IMPERIAL])
def test_tab_forecast_renders(demo_provider, demo_report, units):
    """Tab 2 (Forecast) must render without exceptions in both unit systems."""
    mock_st = _make_mock_streamlit()
    # select_slider returns a sensible default
    mock_st.select_slider.return_value = 48
    with patch("src.skydeck.ui.tabs.st", mock_st):
        render_forecast_tab(demo_report, units)


def test_tab_air_quality_renders(demo_report):
    """Tab 3 (Air Quality) must render without exceptions."""
    with patch("src.skydeck.ui.tabs.st", _make_mock_streamlit()):
        render_air_quality_tab(demo_report)


def test_tab_activities_renders(demo_report):
    """Tab 4 (Activity Suitability) must render without exceptions."""
    with patch("src.skydeck.ui.tabs.st", _make_mock_streamlit()), \
         patch("src.skydeck.ui.components.st", _make_mock_streamlit()):
        render_activities_tab(demo_report)


def test_tab_compare_renders(demo_provider, demo_report):
    """Tab 5 (Compare Cities) must render without exceptions."""
    saved = [
        {"id": 2643743, "name": "London", "latitude": 51.508, "longitude": -0.125,
         "country": "United Kingdom", "timezone": "Europe/London"},
    ]
    mock_st = _make_mock_streamlit()
    mock_st.multiselect.return_value = ["London"]
    mock_st.selectbox.return_value = ("outdoor_sport", "🏃 Outdoor Sports")
    mock_st.button.return_value = False  # Don't trigger the benchmark button
    with patch("src.skydeck.ui.tabs.st", mock_st):
        render_compare_tab(demo_provider, demo_report, saved)


def test_tab_diagnostics_renders(demo_provider, demo_report):
    """Tab 6 (Diagnostics) must render without exceptions."""
    mock_st = _make_mock_streamlit()
    mock_st.button.return_value = False
    with patch("src.skydeck.ui.tabs.st", mock_st), \
         patch("src.skydeck.ui.components.st", mock_st):
        render_diagnostics_tab(demo_provider, demo_report)


# ─── Issue #4: Live provider path (mocked HTTP) ───────────────────────────────

@pytest.mark.parametrize("units", [UnitSystem.METRIC, UnitSystem.IMPERIAL])
def test_live_provider_report_all_charts(mock_open_meteo_report, units):
    """Charts must also work when report comes through the OpenMeteo (live) provider path."""
    report = mock_open_meteo_report
    assert report.current.temperature_2m is not None

    fig1 = create_hourly_temperature_chart(report.hourly, units)
    assert fig1 is not None

    fig2 = create_daily_temperature_band_chart(report.daily, units)
    assert fig2 is not None

    scores = calculate_suitability(report.current, report.hourly)
    assert len(scores) >= 5


# ─── Backward compatibility: original end-to-end ─────────────────────────────

def test_ui_data_pipeline_end_to_end(demo_provider, london_loc):
    """Backward-compatible check: full provider → services → charts pipeline."""
    results = demo_provider.search_locations("London")
    assert len(results) > 0

    report = demo_provider.get_forecast(results[0], forecast_days=16)
    assert report is not None

    assert create_hourly_temperature_chart(report.hourly, UnitSystem.METRIC) is not None
    assert create_precipitation_chart(report.hourly, UnitSystem.METRIC) is not None
    assert create_daily_temperature_band_chart(report.daily, UnitSystem.METRIC) is not None
    assert create_wind_rose_chart(report.hourly, UnitSystem.METRIC) is not None
    if report.air_quality:
        assert create_air_quality_chart(report.air_quality) is not None
    assert create_temperature_heatmap(report.hourly, UnitSystem.METRIC) is not None

    advisories = evaluate_advisories(report.current, report.hourly, report.daily, report.air_quality)
    assert isinstance(advisories, list)
    suitability = calculate_suitability(report.current, report.hourly)
    assert len(suitability) >= 5
    briefings = generate_briefings(report.current, report.hourly, report.daily)
    assert len(briefings) >= 1
    ranked = compare_and_rank_cities([report], "outdoor_sport")
    assert len(ranked) == 1
    assert ranked[0]["city_name"] == results[0].name

