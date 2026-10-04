"""SkyDeck UI components, charts, design system, and tabs."""
from src.skydeck.ui.theme import apply_theme
from src.skydeck.ui.tabs import (
    render_home_page,
    render_weather_page,
    render_forecast_page,
    render_activity_guide_page,
    render_graphs_page,
    render_settings_and_cities_page,
    render_overview_tab,
    render_forecast_tab,
    render_air_quality_tab,
    render_activities_tab,
    render_compare_tab,
    render_diagnostics_tab,
)

__all__ = [
    "apply_theme",
    "render_home_page",
    "render_weather_page",
    "render_forecast_page",
    "render_activity_guide_page",
    "render_graphs_page",
    "render_settings_and_cities_page",
    "render_overview_tab",
    "render_forecast_tab",
    "render_air_quality_tab",
    "render_activities_tab",
    "render_compare_tab",
    "render_diagnostics_tab",
]

