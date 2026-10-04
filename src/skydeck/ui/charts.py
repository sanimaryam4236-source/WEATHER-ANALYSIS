"""
Plotly Chart Builders for SkyDeck Weather Intelligence.

Includes all 6 specialized visualizations:
1. Hourly Temperature Profile with Day/Night Shading & Apparent Temp Spline
2. Precipitation Analysis: Rain Probability (Bars) + Expected Volume (Line/Secondary Axis)
3. Multi-Day High/Low Temperature Confidence Range Band
4. Polar Wind Rose (Direction distribution & speed intensity)
5. Air Quality Pollutant Concentrations & US/European AQI Gauge
6. Hour-by-Day Temperature Thermal Heatmap
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.skydeck.domain.models import HourlyData, DailyData, AirQualityData
from src.skydeck.domain.units import (
    UnitSystem,
    convert_temperature,
    convert_wind_speed,
    convert_precipitation,
    UNIT_SYMBOLS,
)


CHART_LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Outfit, Inter, sans-serif", color="#CBD5E1", size=12),
    margin=dict(l=40, r=30, t=50, b=40),
    hovermode="x unified",
)


def create_hourly_temperature_chart(
    hourly: HourlyData,
    units: UnitSystem,
    hours_limit: int = 48
) -> go.Figure:
    """
    1. Hourly temperature and apparent temperature chart with day/night shading.
    """
    times = hourly.time[:hours_limit]
    temp_unit = UNIT_SYMBOLS[units]["temperature"]

    temps = [convert_temperature(t, units) for t in hourly.temperature_2m[:hours_limit]]
    apparents = [convert_temperature(a, units) for a in hourly.apparent_temperature[:hours_limit]]

    fig = go.Figure()

    # Apparent temp area
    fig.add_trace(go.Scatter(
        x=times,
        y=apparents,
        name=f"Feels Like ({temp_unit})",
        line=dict(color="rgba(147, 197, 253, 0.4)", width=1.5, dash="dot"),
        mode="lines",
    ))

    # Actual temp line
    fig.add_trace(go.Scatter(
        x=times,
        y=temps,
        name=f"Temperature ({temp_unit})",
        line=dict(color="#38BDF8", width=3, shape="spline"),
        fill="tonexty",
        fillcolor="rgba(56, 189, 248, 0.08)",
        mode="lines+markers",
        marker=dict(size=4, color="#38BDF8"),
    ))

    # Add day/night background shading bands
    shapes = []
    for i, t in enumerate(times):
        if "T" in t:
            try:
                hour = int(t.split("T")[1][:2])
                # Shading for night hours (20:00 to 06:00)
                if hour >= 21 or hour <= 5:
                    next_t = times[i + 1] if i + 1 < len(times) else t
                    shapes.append(dict(
                        type="rect",
                        xref="x",
                        yref="paper",
                        x0=t,
                        x1=next_t,
                        y0=0,
                        y1=1,
                        fillcolor="rgba(15, 23, 42, 0.35)",
                        opacity=0.5,
                        layer="below",
                        line_width=0,
                    ))
            except Exception:
                pass

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        title=f"<b>Hourly Temperature Forecast ({hours_limit}h)</b>",
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickangle=-30),
        yaxis=dict(title=temp_unit, showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
        shapes=shapes,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_precipitation_chart(
    hourly: HourlyData,
    units: UnitSystem,
    hours_limit: int = 48
) -> go.Figure:
    """
    2. Precipitation Probability (%) bars + Rainfall Volume (mm/in) spline on secondary y-axis.
    """
    times = hourly.time[:hours_limit]
    probs = hourly.precipitation_probability[:hours_limit]
    precip_unit = UNIT_SYMBOLS[units]["precipitation"]
    vols = [convert_precipitation(p, units) for p in hourly.precipitation[:hours_limit]]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Probability Bars
    fig.add_trace(
        go.Bar(
            x=times,
            y=probs,
            name="Precipitation Probability (%)",
            marker_color="rgba(96, 165, 250, 0.45)",
            marker_line=dict(color="rgba(96, 165, 250, 0.8)", width=1),
        ),
        secondary_y=False,
    )

    # Volume Spline
    fig.add_trace(
        go.Scatter(
            x=times,
            y=vols,
            name=f"Volume ({precip_unit})",
            line=dict(color="#06B6D4", width=2.5, shape="spline"),
            mode="lines+markers",
            marker=dict(size=4, color="#06B6D4"),
        ),
        secondary_y=True,
    )

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        title=f"<b>Precipitation Probability & Intensity ({hours_limit}h)</b>",
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickangle=-30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(title_text="Probability (%)", range=[0, 105], showgrid=True, gridcolor="rgba(255,255,255,0.06)", secondary_y=False)
    fig.update_yaxes(title_text=f"Volume ({precip_unit})", showgrid=False, secondary_y=True)
    return fig


def create_daily_temperature_band_chart(
    daily: DailyData,
    units: UnitSystem,
    days_limit: int = 16
) -> go.Figure:
    """
    3. Multi-day High/Low temperature range band.
    """
    dates = daily.time[:days_limit]
    temp_unit = UNIT_SYMBOLS[units]["temperature"]

    t_max = [convert_temperature(t, units) for t in daily.temperature_2m_max[:days_limit]]
    t_min = [convert_temperature(t, units) for t in daily.temperature_2m_min[:days_limit]]

    fig = go.Figure()

    # Minimum line
    fig.add_trace(go.Scatter(
        x=dates,
        y=t_min,
        name=f"Daily Low ({temp_unit})",
        line=dict(color="#60A5FA", width=2, dash="dash"),
        mode="lines+markers",
    ))

    # Maximum line with band fill
    fig.add_trace(go.Scatter(
        x=dates,
        y=t_max,
        name=f"Daily High ({temp_unit})",
        line=dict(color="#F87171", width=2.5),
        fill="tonexty",
        fillcolor="rgba(248, 113, 113, 0.12)",
        mode="lines+markers",
        marker=dict(size=6, color="#F87171"),
    ))

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        title=f"<b>Daily Temperature Range ({len(dates)} Days)</b>",
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
        yaxis=dict(title=temp_unit, showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_wind_rose_chart(
    hourly: HourlyData,
    units: UnitSystem,
    hours_limit: int = 48
) -> go.Figure:
    """
    4. Polar Wind Rose showing wind direction and speed frequency.
    """
    wind_unit = UNIT_SYMBOLS[units]["wind_speed"]
    speeds = [convert_wind_speed(s, units) for s in hourly.wind_speed_10m[:hours_limit]]
    directions = hourly.wind_direction_10m[:hours_limit]

    # Group into 8 cardinal bins (N, NE, E, SE, S, SW, W, NW)
    cardinal_bins = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    bin_counts = {b: 0 for b in cardinal_bins}
    bin_speeds = {b: [] for b in cardinal_bins}

    for deg, spd in zip(directions, speeds):
        if deg is None or spd is None:
            continue
        idx = int((deg + 22.5) // 45) % 8
        b = cardinal_bins[idx]
        bin_counts[b] += 1
        bin_speeds[b].append(spd)

    avg_speeds = [
        round(sum(bin_speeds[b]) / len(bin_speeds[b]), 1) if bin_speeds[b] else 0.0
        for b in cardinal_bins
    ]

    fig = go.Figure()
    fig.add_trace(go.Barpolar(
        r=avg_speeds,
        theta=cardinal_bins,
        name=f"Avg Speed ({wind_unit})",
        marker=dict(
            color=avg_speeds,
            colorscale="Viridis",
            line=dict(color="rgba(255,255,255,0.4)", width=1),
        ),
        opacity=0.85,
    ))

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        title="<b>Wind Direction & Speed Distribution (Wind Rose)</b>",
        polar=dict(
            radialaxis=dict(showline=True, gridcolor="rgba(255,255,255,0.1)", ticksuffix=f" {wind_unit}"),
            angularaxis=dict(direction="clockwise", rotation=90, gridcolor="rgba(255,255,255,0.1)"),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig


def create_air_quality_chart(aq: AirQualityData, hours_limit: int = 48) -> go.Figure:
    """
    5. Air Quality & Major Pollutants Chart (PM2.5, PM10, NO2, O3).
    """
    times = aq.time[:hours_limit]
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=times,
        y=aq.us_aqi[:hours_limit],
        name="US AQI Index",
        line=dict(color="#F59E0B", width=3),
        mode="lines",
    ))
    fig.add_trace(go.Scatter(
        x=times,
        y=aq.pm2_5[:hours_limit],
        name="PM2.5 (µg/m³)",
        line=dict(color="#EC4899", width=2, dash="dash"),
        mode="lines",
    ))
    fig.add_trace(go.Scatter(
        x=times,
        y=aq.pm10[:hours_limit],
        name="PM10 (µg/m³)",
        line=dict(color="#8B5CF6", width=2, dash="dot"),
        mode="lines",
    ))
    fig.add_trace(go.Scatter(
        x=times,
        y=aq.ozone[:hours_limit],
        name="Ozone O₃ (µg/m³)",
        line=dict(color="#10B981", width=1.5),
        mode="lines",
    ))

    # Add guideline threshold line at AQI 100
    fig.add_hline(
        y=100,
        line_dash="dot",
        line_color="#EF4444",
        annotation_text="Unhealthy Threshold (AQI 100)",
        annotation_position="top right",
    )

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        title="<b>Atmospheric Pollutants & US AQI Trend</b>",
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickangle=-30),
        yaxis=dict(title="Index / Concentration", showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_temperature_heatmap(
    hourly: HourlyData,
    units: UnitSystem,
    days_limit: int = 7
) -> go.Figure:
    """
    6. Hour-by-Day 24h Temperature Heatmap.
    """
    total_hours = days_limit * 24
    if len(hourly.time) < total_hours:
        total_hours = len(hourly.time)

    times = hourly.time[:total_hours]
    temp_unit = UNIT_SYMBOLS[units]["temperature"]
    temps = [convert_temperature(t, units) for t in hourly.temperature_2m[:total_hours]]

    # Parse into matrix: rows = dates, cols = 0-23 hours
    matrix_data = {}
    for t, val in zip(times, temps):
        if "T" in t:
            date_part, hour_part = t.split("T")
            h = int(hour_part.split(":")[0])
            if date_part not in matrix_data:
                matrix_data[date_part] = [None] * 24
            matrix_data[date_part][h] = val

    dates = list(matrix_data.keys())
    z_matrix = [matrix_data[d] for d in dates]
    hours_header = [f"{h:02d}:00" for h in range(24)]

    fig = go.Figure(data=go.Heatmap(
        z=z_matrix,
        x=hours_header,
        y=dates,
        colorscale="RdYlBu_r",
        colorbar=dict(title=temp_unit),
        hoverongaps=False,
    ))

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        title=f"<b>Hour-by-Day Thermal Heatmap ({len(dates)} Days)</b>",
        xaxis=dict(title="Hour of Day", tickangle=-45),
        yaxis=dict(title="Date", autorange="reversed"),
    )
    return fig


def create_temperature_trend_spline_chart(
    daily: DailyData,
    units: UnitSystem,
    days_limit: int = 5
) -> go.Figure:
    """
    5-Day Temperature Trend Spline chart for the Home page grid (matching mockup).
    """
    days = min(days_limit, len(daily.time))
    dates = daily.time[:days]
    temp_unit = UNIT_SYMBOLS[units]["temperature"]

    t_max = [convert_temperature(t, units) for t in daily.temperature_2m_max[:days]]

    labels = []
    for d in dates:
        try:
            from datetime import datetime
            dt = datetime.strptime(d, "%Y-%m-%d")
            labels.append(dt.strftime("%a\n%b %d"))
        except Exception:
            labels.append(d)

    text_values = [f"{int(round(t))}°C" if units == UnitSystem.METRIC else f"{int(round(t))}°F" for t in t_max]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels,
        y=t_max,
        name=f"High ({temp_unit})",
        line=dict(color="#38BDF8", width=3, shape="spline"),
        fill="tozeroy",
        fillcolor="rgba(56, 189, 248, 0.15)",
        mode="lines+markers+text",
        marker=dict(size=8, color="#38BDF8"),
        text=text_values,
        textposition="top center",
        textfont=dict(color="#F8FAFC", size=11, family="Outfit, sans-serif"),
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit, Inter, sans-serif", color="#CBD5E1", size=11),
        margin=dict(l=20, r=20, t=30, b=30),
        height=220,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False, visible=False),
        showlegend=False,
    )
    return fig


def create_rain_probability_donut_chart(prob: float) -> go.Figure:
    """
    Rain Probability Donut chart for the Home page grid (matching mockup).
    """
    prob_val = max(0.0, min(100.0, float(prob if prob is not None else 0.0)))
    rem_val = 100.0 - prob_val

    fig = go.Figure(data=[go.Pie(
        values=[prob_val, rem_val],
        labels=["Rain", "Dry"],
        hole=0.75,
        marker=dict(colors=["#F59E0B" if prob_val > 30 else "#38BDF8", "rgba(255,255,255,0.08)"]),
        textinfo="none",
        hoverinfo="label+value",
        sort=False,
    )])

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        height=180,
        showlegend=False,
        annotations=[dict(
            text=f"<b>{int(round(prob_val))}%</b>",
            x=0.5, y=0.5,
            font_size=24,
            font_color="#F8FAFC",
            font_family="Outfit, sans-serif",
            showarrow=False,
        )],
    )
    return fig

