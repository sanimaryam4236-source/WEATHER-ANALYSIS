"""
UI Component Builders for SkyDeck.

Renders modern, responsive widgets:
- Header strip with location, coordinates, local time, and freshness badge
- Hero weather summary card
- Multi-metric meteorological indicators
- Active safety advisories callouts
- Activity suitability ranking cards
- Plain-language briefings
- System health and diagnostics panel
"""

import streamlit as st
from datetime import datetime
from typing import List

from src.skydeck.domain.models import (
    WeatherReport,
    AdvisoryItem,
    SuitabilityScore,
    DailyBriefing,
)
from src.skydeck.domain.units import (
    UnitSystem,
    convert_temperature,
    convert_wind_speed,
    convert_precipitation,
    convert_pressure,
    format_value,
    UNIT_SYMBOLS,
)
from src.skydeck.domain.weather_codes import get_weather_icon, get_weather_description
from src.skydeck.core.diagnostics import diagnostics


def render_header_strip(report: WeatherReport):
    """Render top header bar with location details and freshness status."""
    loc = report.location
    freshness = report.freshness

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(
            f"""
            <div style="margin-bottom: 0.5rem;">
                <h1 style="margin: 0; font-size: 2.2rem; font-weight: 800; display: inline-block;">
                    {loc.name}
                </h1>
                <span style="font-size: 1.1rem; color: #94A3B8; margin-left: 0.5rem;">
                    {loc.country or ''}
                </span>
            </div>
            <div style="font-size: 0.85rem; color: #64748B;">
                📍 Coordinates: {loc.latitude:.3f}°, {loc.longitude:.3f}° &nbsp;|&nbsp; 
                🌐 Timezone: {loc.timezone} &nbsp;|&nbsp;
                ⏱️ Local Time: {datetime.now().strftime('%A, %d %b %H:%M')}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div style="text-align: right; padding-top: 0.75rem;">
                <span class="freshness-pill">
                    {freshness.badge_text}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_hero_card(report: WeatherReport, units: UnitSystem):
    """Render high-impact hero weather card."""
    curr = report.current
    symbols = UNIT_SYMBOLS[units]

    temp_conv = convert_temperature(curr.temperature_2m, units)
    app_conv = convert_temperature(curr.apparent_temperature, units)

    icon = get_weather_icon(curr.weather_code or 0, curr.is_day)
    desc = get_weather_description(curr.weather_code or 0)

    # Today's high/low
    today_max = (
        convert_temperature(report.daily.temperature_2m_max[0], units)
        if report.daily.temperature_2m_max
        else None
    )
    today_min = (
        convert_temperature(report.daily.temperature_2m_min[0], units)
        if report.daily.temperature_2m_min
        else None
    )

    st.markdown(
        f"""
        <div class="hero-card">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <div style="display: flex; align-items: baseline;">
                        <span class="hero-temp">{format_value(temp_conv, symbols['temperature'], precision=1)}</span>
                        <span style="font-size: 3.5rem; margin-left: 1.25rem;">{icon}</span>
                    </div>
                    <div class="hero-condition">{desc}</div>
                    <div style="color: var(--sky-text-muted); font-size: 0.95rem; margin-top: 0.4rem;">
                        Feels like {format_value(app_conv, symbols['temperature'], precision=1)} &nbsp;•&nbsp;
                        High: {format_value(today_max, symbols['temperature'], precision=0)} &nbsp;•&nbsp;
                        Low: {format_value(today_min, symbols['temperature'], precision=0)}
                    </div>
                </div>
                <div style="text-align: right; margin-top: 0.5rem;">
                    <div style="font-size: 0.9rem; color: var(--sky-text-secondary);">
                        💧 Humidity: <b>{format_value(curr.relative_humidity_2m, '%', precision=0)}</b>
                    </div>
                    <div style="font-size: 0.9rem; color: var(--sky-text-secondary); margin-top: 0.25rem;">
                        💨 Wind: <b>{format_value(convert_wind_speed(curr.wind_speed_10m, units), symbols['wind_speed'], precision=1)}</b>
                    </div>
                    <div style="font-size: 0.9rem; color: var(--sky-text-secondary); margin-top: 0.25rem;">
                        🌧️ Precipitation: <b>{format_value(convert_precipitation(curr.precipitation, units), symbols['precipitation'], precision=1)}</b>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics_grid(report: WeatherReport, units: UnitSystem):
    """Render 4 secondary atmospheric metric cards."""
    curr = report.current
    symbols = UNIT_SYMBOLS[units]

    cols = st.columns(4)

    # 1. Barometric Pressure
    with cols[0]:
        press = convert_pressure(curr.pressure_msl, units)
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-label">Barometric Pressure</div>
                <div class="metric-val">{format_value(press, symbols['pressure'], precision=1)}</div>
                <div class="metric-sub">Sea-level adjusted</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. Cloud Cover
    with cols[1]:
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-label">Cloud Cover</div>
                <div class="metric-val">{format_value(curr.cloud_cover, '%', precision=0)}</div>
                <div class="metric-sub">Total sky coverage</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3. Wind Gusts & Direction
    with cols[2]:
        gust = convert_wind_speed(curr.wind_gusts_10m, units)
        direction = f"{curr.wind_direction_10m:.0f}°" if curr.wind_direction_10m is not None else "—"
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-label">Wind Gusts & Dir</div>
                <div class="metric-val">{format_value(gust, symbols['wind_speed'], precision=1)}</div>
                <div class="metric-sub">Heading: {direction}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 4. UV Index or Visibility
    with cols[3]:
        # UV index from hourly[0] if available
        uv = report.hourly.uv_index[0] if report.hourly.uv_index else None
        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-label">Current UV Index</div>
                <div class="metric-val">{format_value(uv, '', precision=1)}</div>
                <div class="metric-sub">{'Sun protection required' if (uv and uv >= 6) else 'Low to moderate exposure'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_advisories_section(advisories: List[AdvisoryItem]):
    """Render active weather advisories."""
    if not advisories:
        st.success("✅ **No active weather advisories.** Conditions are currently within normal baseline thresholds.")
        return

    st.markdown("### ⚠️ Active Meteorological Advisories")
    for adv in advisories:
        css_class = "advisory-danger" if adv.severity == "danger" else "advisory-warning"
        start_str = f"<b>Onset:</b> {adv.start_time}" if adv.start_time else ""
        end_str = f"&nbsp;|&nbsp; <b>Expires:</b> {adv.end_time}" if adv.end_time else ""

        st.markdown(
            f"""
            <div class="advisory-callout {css_class}">
                <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.25rem;">
                    {adv.title}
                </div>
                <div style="font-size: 0.9rem; color: #E2E8F0;">
                    {adv.description}
                </div>
                <div style="font-size: 0.85rem; color: #CBD5E1; margin-top: 0.35rem;">
                    <b>Trigger:</b> {adv.trigger_value} <br/>
                    {start_str} {end_str}
                </div>
                <div class="advisory-disclaimer">
                    ℹ️ {adv.disclaimer}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_suitability_cards(scores: List[SuitabilityScore]):
    """Render activity suitability cards with breakdown expanders."""
    st.markdown("### 🎯 Activity Suitability Index")

    rating_classes = {
        "Optimal": "badge-optimal",
        "Good": "badge-good",
        "Marginal": "badge-marginal",
        "Poor": "badge-poor",
        "Hazardous": "badge-hazard",
    }

    cols = st.columns(len(scores))
    for col, item in zip(cols, scores):
        badge_cls = rating_classes.get(item.rating, "badge-marginal")
        with col:
            st.markdown(
                f"""
                <div class="metric-box" style="margin-bottom: 0.5rem;">
                    <div style="font-size: 1.8rem; margin-bottom: 0.25rem;">{item.icon}</div>
                    <div style="font-weight: 700; font-size: 1rem; margin-bottom: 0.4rem;">{item.activity_name}</div>
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.8rem; font-weight: 800;">{item.score}<span style="font-size: 1rem; color: #64748B;">/100</span></span>
                        <span class="suitability-badge {badge_cls}">{item.rating}</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #94A3B8;">
                        🕒 <b>Best Window:</b><br/>{item.best_window}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("Why this score?"):
                if item.is_blocked:
                    st.error(f"⛔ {item.block_reason}")
                for factor, explanation in item.breakdown.items():
                    st.write(f"• **{factor}:** {explanation}")


def render_briefing_cards(briefings: List[DailyBriefing]):
    """Render conversational daily briefings."""
    st.markdown("### 🎙️ Plain-Language Forecast Briefing")

    cols = st.columns(len(briefings))
    for col, b in zip(cols, briefings):
        with col:
            with st.container():
                st.markdown(
                    f"""
                    <div class="briefing-card">
                        <div class="briefing-title">
                            📅 {b.day_label} ({b.date})
                        </div>
                        <div class="briefing-title" style="font-size:1.05rem; font-weight:600; margin-bottom:0.5rem;">
                            {b.headline}
                        </div>
                        <div class="briefing-body">
                            🌡️ <b>Temperature Trend:</b> {b.temperature_summary} <br/><br/>
                            🌧️ <b>Precipitation Timing:</b> {b.precipitation_summary} <br/><br/>
                            💨 <b>Wind Profile:</b> {b.wind_summary}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_diagnostics_panel():
    """Render runtime diagnostics and API consumption telemetry."""
    summary = diagnostics.summary()

    st.markdown("### 🛠️ System Health & API Budget Telemetry")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Calls (Session)", summary["total_calls"])
    c2.metric("Cache Hit Ratio", summary["cache_hit_ratio"])
    c3.metric("Daily Budget Consumed", summary["daily_budget_used_pct"], f"Left: {summary['daily_budget_remaining']}")
    c4.metric("Last Fetch", summary["last_fetch"].split(" ")[-1] if " " in summary["last_fetch"] else summary["last_fetch"])

    with st.expander("Detailed Diagnostics Log"):
        st.json(summary)
        if diagnostics.call_history:
            st.markdown("**Recent Network Invocations (Last 10)**")
            st.table(diagnostics.call_history[-10:])
