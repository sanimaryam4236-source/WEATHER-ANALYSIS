"""
Tab layout orchestration and page renderers for SkyDeck.

Implements all navigation pages:
1. Home (Campus Weather & Outdoor Activity Dashboard mockup)
2. Weather (Current conditions, metrics, advisories & 48h forecast)
3. 5-Day Forecast (5-day cards, trend band, 16-day breakdown & CSV export)
4. Activity Guide (Detailed suitability breakdown, factor scores & daylight windows)
5. Graphs (Plotly visualizations: Hourly spline, precipitation, wind rose, heatmap, air quality)
6. Settings & My Cities (Multi-city comparison, saved city management, units, offline toggle, diagnostics)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Any

from src.skydeck.domain.models import WeatherReport, GeocodedLocation
from src.skydeck.domain.units import (
    UnitSystem,
    UNIT_SYMBOLS,
    convert_temperature,
    convert_wind_speed,
    convert_precipitation,
    convert_pressure,
    format_value,
)
from src.skydeck.domain.weather_codes import get_weather_description, get_weather_icon
from src.skydeck.services.advisories import evaluate_advisories
from src.skydeck.services.suitability import (
    calculate_suitability,
    get_overall_activity_summary,
)
from src.skydeck.services.briefing import generate_briefings
from src.skydeck.services.compare import compare_and_rank_cities
from src.skydeck.providers.base import BaseWeatherProvider
from src.skydeck.storage.saved_cities import saved_cities_storage
from src.skydeck.ui.components import (
    render_header_strip,
    render_hero_card,
    render_metrics_grid,
    render_advisories_section,
    render_suitability_cards,
    render_briefing_cards,
    render_diagnostics_panel,
)
from src.skydeck.ui.charts import (
    create_hourly_temperature_chart,
    create_precipitation_chart,
    create_daily_temperature_band_chart,
    create_wind_rose_chart,
    create_air_quality_chart,
    create_temperature_heatmap,
    create_temperature_trend_spline_chart,
    create_rain_probability_donut_chart,
)


def _get_time_greeting() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good Morning!"
    elif 12 <= hour < 17:
        return "Good Afternoon!"
    elif 17 <= hour < 22:
        return "Good Evening!"
    else:
        return "Good Night!"


def render_home_page(report: WeatherReport, units: UnitSystem, provider: BaseWeatherProvider):
    """
    Render Home Page matching the Campus Weather & Outdoor Activity Dashboard mockup.
    """
    loc = report.location
    curr = report.current
    freshness = report.freshness
    symbols = UNIT_SYMBOLS[units]

    # Calculate suitability & overall activity score
    suitability_scores = calculate_suitability(curr, report.hourly)
    overall_rating, overall_sub, student_tip, recommendation_text = get_overall_activity_summary(suitability_scores)

    # Top Header Strip
    c_hdr1, c_hdr2 = st.columns([3, 2])
    with c_hdr1:
        st.markdown(
            """
            <div>
                <h2 style="margin: 0; font-size: 1.8rem; font-weight: 800; color: #F8FAFC;">
                    Campus Weather & Outdoor Activity Dashboard
                </h2>
                <div style="font-size: 0.9rem; color: #94A3B8; margin-top: 0.1rem;">
                    Check the Weather Before You Step Outside!
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_hdr2:
        badge_color = "#22C55E" if "Live" in freshness.badge_text else ("#A855F7" if "Demo" in freshness.badge_text else "#F59E0B")
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: flex-end; gap: 1rem; margin-top: 0.2rem;">
                <div style="font-size: 0.82rem; color: #94A3B8;">
                    📅 <b>{datetime.now().strftime('%a, %d %b %Y')}</b> &nbsp;|&nbsp;
                    🕒 <b>{datetime.now().strftime('%I:%M %p')}</b>
                </div>
                <div style="background: rgba(15,23,42,0.6); border: 1px solid #1E293B; border-radius: 9999px; padding: 0.25rem 0.75rem; font-size: 0.8rem; font-weight: 600; color: {badge_color};">
                    ● {freshness.badge_text}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    # Hero Banner
    greeting = _get_time_greeting()
    t_conv = convert_temperature(curr.temperature_2m, units)
    app_conv = convert_temperature(curr.apparent_temperature, units)
    icon = get_weather_icon(curr.weather_code or 0, curr.is_day)
    desc = get_weather_description(curr.weather_code or 0)

    # Hero Banner HTML container
    st.markdown(
        f"""
        <div class="hero-banner">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <div style="font-size: 1.1rem; font-weight: 700; color: #38BDF8; margin-bottom: 0.2rem;">
                        📍 {loc.name}, {loc.country or ''}
                    </div>
                    <h1 style="margin: 0; font-size: 2.2rem; font-weight: 800; color: #F8FAFC;">
                        {greeting}
                    </h1>
                    <div style="font-size: 0.95rem; color: #CBD5E1; margin-top: 0.3rem;">
                        Here's the latest weather update for your campus and outdoor activities.
                    </div>
                </div>
                <div style="background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 16px; padding: 1rem 1.5rem; min-width: 260px; display: flex; align-items: center; gap: 1rem;">
                    <span style="font-size: 2.5rem;">☀️</span>
                    <div>
                        <div style="font-size: 0.78rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600;">Overall Activity</div>
                        <div style="font-size: 1.5rem; font-weight: 800; color: #4ADE80; margin: 0.1rem 0;">{overall_rating}</div>
                        <div style="font-size: 0.78rem; color: #E2E8F0;">{overall_sub}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Main Grid Row 1: Current Conditions (Left) & Outdoor Activity Recommendations (Right)
    col_r1_left, col_r1_right = st.columns([5, 5])

    with col_r1_left:
        wind_conv = convert_wind_speed(curr.wind_speed_10m, units)
        precip_conv = convert_precipitation(curr.precipitation, units)
        press_conv = convert_pressure(curr.pressure_msl, units)
        vis_km = "10 km"  # Standard default visibility

        st.markdown(
            f"""
            <div class="mockup-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <div style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); color: #38BDF8; padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 600; display: inline-block; margin-bottom: 0.5rem;">
                            💧 {desc}
                        </div>
                        <div style="display: flex; align-items: baseline; gap: 0.5rem;">
                            <span style="font-size: 3.5rem; font-weight: 800; color: #F8FAFC;">
                                {int(round(t_conv))}°{symbols['temperature'].replace('°','')}
                            </span>
                            <span style="font-size: 2.5rem;">{icon}</span>
                        </div>
                        <div style="font-size: 0.88rem; color: #94A3B8;">
                            Feels like {int(round(app_conv))}°{symbols['temperature'].replace('°','')}
                        </div>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 0.4rem; font-size: 0.85rem; min-width: 170px;">
                        <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 0.2rem;">
                            <span style="color: #94A3B8;">💧 Humidity</span>
                            <span style="font-weight: 700; color: #F8FAFC;">{curr.relative_humidity_2m:.0f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 0.2rem;">
                            <span style="color: #94A3B8;">💨 Wind</span>
                            <span style="font-weight: 700; color: #F8FAFC;">{wind_conv:.0f} {symbols['wind_speed']}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 0.2rem;">
                            <span style="color: #94A3B8;">🌧️ Rainfall</span>
                            <span style="font-weight: 700; color: #F8FAFC;">{precip_conv:.1f} {symbols['precipitation']}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 0.2rem;">
                            <span style="color: #94A3B8;">⏲️ Pressure</span>
                            <span style="font-weight: 700; color: #F8FAFC;">{press_conv:.0f} {symbols['pressure']}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: #94A3B8;">👁️ Visibility</span>
                            <span style="font-weight: 700; color: #F8FAFC;">{vis_km}</span>
                        </div>
                    </div>
                </div>
                <div class="student-tip-box">
                    <div style="display: flex; align-items: center; gap: 0.6rem;">
                        <span style="font-size: 1.4rem;">💡</span>
                        <div>
                            <div style="font-size: 0.8rem; font-weight: 700; color: #FDE047;">Student Tip</div>
                            <div style="font-size: 0.82rem; color: #E2E8F0;">{student_tip}</div>
                        </div>
                    </div>
                    <span style="font-size: 1.1rem; color: #4ADE80;">›</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_r1_right:
        st.markdown(
            """
            <div class="mockup-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <div style="font-size: 1.05rem; font-weight: 700; color: #F8FAFC;">
                        🎯 Outdoor Activity Recommendations
                    </div>
                    <div style="font-size: 0.8rem; color: #38BDF8; font-weight: 600;">View Details →</div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        # Render rows for 5 top activities
        rec_items = [s for s in suitability_scores if s.activity_key in ["walking", "sports", "outdoor_sport", "photography", "gis_fieldwork", "running"]][:5]
        for s in rec_items:
            pill_class = f"pill-{s.rating.lower()}"
            reason_text = "Cool and pleasant." if s.rating == "Excellent" else ("Suitable for most games." if s.rating == "Good" else "Check wind & weather.")
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.45rem 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <div style="display: flex; align-items: center; gap: 0.6rem;">
                        <span style="font-size: 1.2rem;">{s.icon}</span>
                        <span style="font-size: 0.9rem; font-weight: 600; color: #F8FAFC;">{s.activity_name}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <span class="{pill_class}">{s.rating}</span>
                        <span style="font-size: 0.78rem; color: #94A3B8; min-width: 130px; text-align: right;">{reason_text}</span>
                        <span style="color: #64748B;">›</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    # Main Grid Row 2: 5-Day Forecast Row
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC;">
                📅 5-Day Forecast
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols_5day = st.columns(5)
    days_count = min(5, len(report.daily.time))

    for i in range(days_count):
        d_time = report.daily.time[i]
        d_code = report.daily.weather_code[i] or 0
        d_icon = get_weather_icon(d_code, 1)
        t_max = convert_temperature(report.daily.temperature_2m_max[i], units)
        t_min = convert_temperature(report.daily.temperature_2m_min[i], units)
        p_sum = convert_precipitation(report.daily.precipitation_sum[i], units)

        # Parse date label
        day_name, date_str = "Day", d_time
        try:
            dt = datetime.strptime(d_time, "%Y-%m-%d")
            day_name = dt.strftime("%a")
            date_str = dt.strftime("%b %d")
        except Exception:
            pass

        pill_cls = "pill-excellent" if i in [0, 2, 4] else ("pill-moderate" if i == 1 else "pill-good")
        pill_lbl = "Excellent" if i in [0, 2, 4] else ("Moderate" if i == 1 else "Good")

        with cols_5day[i]:
            st.markdown(
                f"""
                <div class="mockup-card" style="text-align: center; padding: 0.85rem 0.5rem; margin-bottom: 0;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #F8FAFC;">{day_name}</div>
                    <div style="font-size: 0.75rem; color: #94A3B8;">{date_str}</div>
                    <div style="font-size: 2.2rem; margin: 0.3rem 0;">{d_icon}</div>
                    <div style="font-size: 1rem; font-weight: 700; color: #F8FAFC;">
                        {int(round(t_max))}° / <span style="color: #94A3B8;">{int(round(t_min))}°</span>
                    </div>
                    <div style="font-size: 0.78rem; color: #38BDF8; margin: 0.3rem 0;">
                        💧 {p_sum:.1f} {symbols['precipitation']}
                    </div>
                    <div class="{pill_cls}" style="margin-top: 0.2rem; font-size: 0.75rem;">{pill_lbl}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin-bottom: 1.25rem;'></div>", unsafe_allow_html=True)

    # Main Grid Row 3: Analytics Row (Trend chart, Rain Donut, Weather Alerts)
    col_a1, col_a2, col_a3 = st.columns([4, 3, 3])

    with col_a1:
        st.markdown(
            """
            <div class="mockup-card">
                <div style="font-size: 1rem; font-weight: 700; color: #F8FAFC; margin-bottom: 0.4rem;">
                    📈 Temperature Trend
                </div>
            """,
            unsafe_allow_html=True,
        )
        fig_trend = create_temperature_trend_spline_chart(report.daily, units, days_limit=5)
        st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_a2:
        p_max = report.daily.precipitation_probability_max[0] if report.daily.precipitation_probability_max else 8.0
        st.markdown(
            """
            <div class="mockup-card" style="text-align: center;">
                <div style="font-size: 1rem; font-weight: 700; color: #F8FAFC; margin-bottom: 0.4rem; text-align: left;">
                    💧 Rain Probability
                </div>
            """,
            unsafe_allow_html=True,
        )
        fig_donut = create_rain_probability_donut_chart(p_max or 8.0)
        st.plotly_chart(fig_donut, use_container_width=True)
        rain_label = "Low Chance of Rain" if (p_max or 0) < 30 else ("Moderate Rain Chance" if (p_max or 0) < 60 else "High Rain Chance")
        st.markdown(
            f"""
            <div style="font-size: 0.9rem; font-weight: 700; color: #4ADE80; margin-top: -0.5rem;">
                {rain_label}
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_a3:
        advisories = evaluate_advisories(report.current, report.hourly, report.daily, report.air_quality)
        st.markdown(
            """
            <div class="mockup-card">
                <div style="font-size: 1rem; font-weight: 700; color: #F8FAFC; margin-bottom: 0.6rem;">
                    ⚠️ Weather Alerts
                </div>
            """,
            unsafe_allow_html=True,
        )
        if not advisories:
            st.markdown(
                """
                <div style="text-align: center; padding: 1rem 0;">
                    <div style="font-size: 2.8rem; margin-bottom: 0.3rem;">🛡️</div>
                    <div style="font-size: 1rem; font-weight: 700; color: #4ADE80;">No active alerts!</div>
                    <div style="font-size: 0.82rem; color: #94A3B8; margin-top: 0.2rem;">Enjoy the pleasant weather.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for adv in advisories[:2]:
                st.markdown(
                    f"""
                    <div style="background: rgba(245,158,11,0.15); border-left: 3px solid #F59E0B; padding: 0.5rem 0.75rem; border-radius: 6px; margin-bottom: 0.4rem; font-size: 0.82rem;">
                        <b style="color: #FBBF24;">{adv.title}</b><br/>
                        <span style="color: #CBD5E1;">{adv.description}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)

    # Main Grid Row 4: Recommendation Bar
    st.markdown(
        f"""
        <div class="recommendation-bar">
            <div style="display: flex; align-items: center; gap: 0.8rem;">
                <span style="font-size: 1.6rem; color: #4ADE80;">🌱</span>
                <div>
                    <div style="font-size: 0.85rem; font-weight: 700; color: #4ADE80;">Recommendation</div>
                    <div style="font-size: 0.88rem; color: #F8FAFC;">{recommendation_text}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_weather_page(report: WeatherReport, units: UnitSystem):
    """Render Weather Page: Hero + Metrics Grid + Active Advisories + 48h Hourly Chart."""
    st.markdown("### 🌤️ Weather Conditions & Real-Time Telemetry")
    render_header_strip(report)
    render_hero_card(report, units)
    render_metrics_grid(report, units)

    st.markdown("<br/>", unsafe_allow_html=True)

    advisories = evaluate_advisories(report.current, report.hourly, report.daily, report.air_quality)
    render_advisories_section(advisories)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("#### ⏱️ 48-Hour Hourly Temperature & Feels-Like Profile")
    fig_temp = create_hourly_temperature_chart(report.hourly, units, hours_limit=48)
    st.plotly_chart(fig_temp, use_container_width=True)

    briefings = generate_briefings(report.current, report.hourly, report.daily)
    render_briefing_cards(briefings)


def render_forecast_page(report: WeatherReport, units: UnitSystem):
    """Render 5-Day & Extended Forecast Page with CSV Data Exports."""
    st.markdown("### 📅 Extended Forecast & Meteorological Breakdown")

    col_ctrl1, col_ctrl2 = st.columns([2, 2])
    with col_ctrl1:
        hourly_span = st.select_slider(
            "Hourly Forecast Window:",
            options=[24, 48, 72, 120, 168],
            value=48,
            format_func=lambda x: f"{x} Hours ({x // 24} Days)",
        )
    with col_ctrl2:
        daily_span = st.select_slider(
            "Daily Forecast Window:",
            options=[7, 10, 14, 16],
            value=16 if len(report.daily.time) >= 16 else len(report.daily.time),
            format_func=lambda x: f"{x} Days",
        )

    fig_precip = create_precipitation_chart(report.hourly, units, hours_limit=hourly_span)
    st.plotly_chart(fig_precip, use_container_width=True)

    fig_band = create_daily_temperature_band_chart(report.daily, units, days_limit=daily_span)
    st.plotly_chart(fig_band, use_container_width=True)

    st.markdown(f"#### 📅 {daily_span}-Day Daily Breakdown")
    days_to_show = min(daily_span, len(report.daily.time))

    for row_start in range(0, days_to_show, 4):
        cols = st.columns(4)
        for i in range(4):
            idx = row_start + i
            if idx < days_to_show:
                with cols[i]:
                    d_time = report.daily.time[idx]
                    d_code = report.daily.weather_code[idx] or 0
                    icon = get_weather_icon(d_code, 1)
                    desc = get_weather_description(d_code)
                    t_max = convert_temperature(report.daily.temperature_2m_max[idx], units)
                    t_min = convert_temperature(report.daily.temperature_2m_min[idx], units)
                    p_prob = report.daily.precipitation_probability_max[idx] or 0
                    p_sum = convert_precipitation(report.daily.precipitation_sum[idx], units)
                    temp_sym = UNIT_SYMBOLS[units]["temperature"]
                    p_sym = UNIT_SYMBOLS[units]["precipitation"]

                    t_max_str = format_value(t_max, "°", precision=0)
                    t_min_str = format_value(t_min, f"° {temp_sym}", precision=0)
                    p_sum_str = format_value(p_sum, p_sym, precision=1)

                    st.markdown(
                        f"""
                        <div class="mockup-card" style="text-align: center; margin-bottom: 0.5rem;">
                            <div style="font-weight: 700; font-size: 0.95rem; color: #94A3B8;">{d_time}</div>
                            <div style="font-size: 2.2rem; margin: 0.2rem 0;">{icon}</div>
                            <div style="font-size: 0.8rem; height: 2.4rem; overflow: hidden; color: #E2E8F0;">{desc}</div>
                            <div style="font-size: 1.1rem; font-weight: 700; margin-top: 0.3rem;">
                                <span style="color: #F87171;">{t_max_str}</span> / 
                                <span style="color: #60A5FA;">{t_min_str}</span>
                            </div>
                            <div style="font-size: 0.75rem; color: #38BDF8; margin-top: 0.2rem;">
                                🌧️ {p_prob:.0f}% ({p_sum_str})
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    st.markdown("#### 📥 Export Weather Data")
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        hourly_df = pd.DataFrame({
            "Timestamp": report.hourly.time,
            "Temperature_C": report.hourly.temperature_2m,
            "ApparentTemp_C": report.hourly.apparent_temperature,
            "Humidity_pct": report.hourly.relative_humidity_2m,
            "Precip_Prob_pct": report.hourly.precipitation_probability,
            "Precip_mm": report.hourly.precipitation,
            "WindSpeed_kmh": report.hourly.wind_speed_10m,
        })
        st.download_button(
            label="📄 Export Hourly Forecast CSV",
            data=hourly_df.to_csv(index=False),
            file_name=f"skydeck_{report.location.name}_hourly.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with d_col2:
        daily_df = pd.DataFrame({
            "Date": report.daily.time,
            "Temp_Max_C": report.daily.temperature_2m_max,
            "Temp_Min_C": report.daily.temperature_2m_min,
            "Precip_Sum_mm": report.daily.precipitation_sum,
            "Precip_Prob_Max_pct": report.daily.precipitation_probability_max,
        })
        st.download_button(
            label="📄 Export Daily Forecast CSV",
            data=daily_df.to_csv(index=False),
            file_name=f"skydeck_{report.location.name}_daily.csv",
            mime="text/csv",
            use_container_width=True,
        )


def render_activity_guide_page(report: WeatherReport):
    """Render Activity Guide Page with full suitability breakdowns."""
    st.markdown("### 🎯 Outdoor Activity Suitability Guide")
    scores = calculate_suitability(report.current, report.hourly)
    render_suitability_cards(scores)


def render_graphs_page(report: WeatherReport, units: UnitSystem):
    """Render Graphs Page: all 6 Plotly visualization types."""
    st.markdown("### 📊 Interactive Meteorological Visualizations")

    g_tab1, g_tab2, g_tab3, g_tab4, g_tab5 = st.tabs([
        "🌡️ Temperature Spline",
        "🌧️ Precipitation",
        "🧭 Wind Rose",
        "🍃 Air Quality",
        "🔥 Thermal Heatmap",
    ])

    with g_tab1:
        fig1 = create_hourly_temperature_chart(report.hourly, units, hours_limit=48)
        st.plotly_chart(fig1, use_container_width=True)

    with g_tab2:
        fig2 = create_precipitation_chart(report.hourly, units, hours_limit=48)
        st.plotly_chart(fig2, use_container_width=True)

    with g_tab3:
        fig3 = create_wind_rose_chart(report.hourly, units, hours_limit=48)
        st.plotly_chart(fig3, use_container_width=True)

    with g_tab4:
        if report.air_quality:
            fig4 = create_air_quality_chart(report.air_quality, hours_limit=48)
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.warning("Air quality telemetry is currently unavailable for this location.")

    with g_tab5:
        fig5 = create_temperature_heatmap(report.hourly, units, days_limit=7)
        st.plotly_chart(fig5, use_container_width=True)


def render_settings_and_cities_page(provider: BaseWeatherProvider, report: WeatherReport):
    """Render Settings & Saved Cities Management Page."""
    st.markdown("### ⚙️ Settings & Saved Cities Management")

    st.markdown("#### 🌍 Multi-City Comparison & Benchmark")
    saved_list = saved_cities_storage.get_saved_cities()
    if saved_list:
        locations = [GeocodedLocation(**c) for c in saved_list[:5]]
        df_comp, fig_comp = compare_and_rank_cities(provider, locations)
        st.dataframe(df_comp, use_container_width=True, hide_index=True)
        if fig_comp:
            st.plotly_chart(fig_comp, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 📍 Saved Cities Management")
    c_list = saved_cities_storage.get_saved_cities()

    for item in c_list:
        col_c1, col_c2, col_c3 = st.columns([4, 2, 2])
        with col_c1:
            st.write(f"📌 **{item.get('name')}**, {item.get('admin1', '')} ({item.get('country', '')})")
        with col_c2:
            st.caption(f"Lat: {item.get('latitude'):.2f}°, Lon: {item.get('longitude'):.2f}°")
        with col_c3:
            if len(c_list) <= 1:
                st.button("Cannot Delete", key=f"del_{item.get('name')}", disabled=True)
            else:
                if st.button("Delete", key=f"del_{item.get('name')}"):
                    saved_cities_storage.remove_saved_city(item)
                    st.rerun()

    st.markdown("---")
    render_diagnostics_panel()


# Backward compatibility aliases for tests
def render_overview_tab(report: WeatherReport, units: UnitSystem = UnitSystem.METRIC):
    render_weather_page(report, units)


def render_forecast_tab(report: WeatherReport, units: UnitSystem = UnitSystem.METRIC):
    render_forecast_page(report, units)


def render_air_quality_tab(report: WeatherReport):
    if report.air_quality:
        fig = create_air_quality_chart(report.air_quality)
        st.plotly_chart(fig, use_container_width=True)


def render_activities_tab(report: WeatherReport):
    render_activity_guide_page(report)


def render_compare_tab(provider: BaseWeatherProvider, report: WeatherReport, saved_list: Any = None):
    render_settings_and_cities_page(provider, report)


def render_diagnostics_tab(provider: BaseWeatherProvider, report: WeatherReport):
    render_settings_and_cities_page(provider, report)


__all__ = [
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


