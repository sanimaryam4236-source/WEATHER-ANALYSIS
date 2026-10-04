"""
Plain-Language Weather Briefing Generator.

Pure logic: Synthesizes forecast metrics into conversational, human-friendly briefings
for Today and Tomorrow:
- Peak temperature timing and thermal comfort
- Precipitation onset, peak intensity, and cessation
- Notable wind shifts and gusts
- Highlighted advisories
"""

from typing import List, Optional
from src.skydeck.domain.models import (
    CurrentConditions,
    HourlyData,
    DailyData,
    DailyBriefing,
)
from src.skydeck.domain.weather_codes import get_weather_description


def generate_daily_briefing(
    day_idx: int,
    day_label: str,
    current: Optional[CurrentConditions],
    hourly: HourlyData,
    daily: DailyData,
) -> DailyBriefing:
    """
    Generate conversational briefing for a specific forecast day (0 = Today, 1 = Tomorrow).
    """
    date_str = daily.time[day_idx] if (daily.time and len(daily.time) > day_idx) else "Unknown Date"
    t_max = daily.temperature_2m_max[day_idx] if (daily.temperature_2m_max and len(daily.temperature_2m_max) > day_idx) else None
    t_min = daily.temperature_2m_min[day_idx] if (daily.temperature_2m_min and len(daily.temperature_2m_min) > day_idx) else None
    w_code = daily.weather_code[day_idx] if (daily.weather_code and len(daily.weather_code) > day_idx) else 0
    p_sum = daily.precipitation_sum[day_idx] if (daily.precipitation_sum and len(daily.precipitation_sum) > day_idx) else 0.0
    p_prob = daily.precipitation_probability_max[day_idx] if (daily.precipitation_probability_max and len(daily.precipitation_probability_max) > day_idx) else 0.0
    w_max = daily.wind_speed_10m_max[day_idx] if (daily.wind_speed_10m_max and len(daily.wind_speed_10m_max) > day_idx) else None
    g_max = daily.wind_gusts_10m_max[day_idx] if (daily.wind_gusts_10m_max and len(daily.wind_gusts_10m_max) > day_idx) else None

    cond_desc = get_weather_description(w_code or 0)

    # 1. Headline
    if t_max is not None and t_min is not None:
        headline = f"{cond_desc} with highs around {t_max:.0f}°C and lows near {t_min:.0f}°C."
    else:
        headline = f"Predominantly {cond_desc.lower()} throughout the day."

    # 2. Temperature narrative & peak timing
    h_start = day_idx * 24
    h_end = h_start + 24
    day_hours = hourly.time[h_start:h_end] if hourly.time else []
    day_temps = hourly.temperature_2m[h_start:h_end] if hourly.temperature_2m else []

    peak_time_str = "afternoon"
    if day_hours and day_temps:
        valid_pairs = [(t, temp) for t, temp in zip(day_hours, day_temps) if temp is not None]
        if valid_pairs:
            peak_t, peak_val = max(valid_pairs, key=lambda x: x[1])
            if "T" in peak_t:
                h = peak_t.split("T")[1][:5]
                peak_time_str = f"around {h}"

    if t_max is not None:
        if t_max >= 30.0:
            temp_summary = f"Hot weather peaking at {t_max:.1f}°C {peak_time_str}. Seek shade and stay hydrated."
        elif t_max <= 5.0:
            temp_summary = f"Frigid conditions reaching only {t_max:.1f}°C. Warm layered clothing strongly recommended."
        else:
            temp_summary = f"Pleasant thermal trend reaching a peak of {t_max:.1f}°C {peak_time_str}."
    else:
        temp_summary = "Moderate temperatures across the day."

    # 3. Precipitation timing narrative
    day_precip = hourly.precipitation[h_start:h_end] if hourly.precipitation else []
    day_probs = hourly.precipitation_probability[h_start:h_end] if hourly.precipitation_probability else []

    rain_hours = []
    if day_hours and day_precip:
        for t, r, prob in zip(day_hours, day_precip, day_probs):
            if (r is not None and r > 0.1) or (prob is not None and prob >= 40.0):
                if "T" in t:
                    rain_hours.append(t.split("T")[1][:5])

    if rain_hours:
        start_hr = rain_hours[0]
        end_hr = rain_hours[-1]
        if start_hr == end_hr:
            precip_summary = f"Showers expected around {start_hr} (total ~{p_sum:.1f} mm, {p_prob:.0f}% chance). Keep an umbrella handy."
        else:
            precip_summary = f"Rain likely from {start_hr} until {end_hr} (total ~{p_sum:.1f} mm). Peak probability {p_prob:.0f}%."
    else:
        if p_sum and p_sum > 0:
            precip_summary = f"Scattered light dampness possible (~{p_sum:.1f} mm). Major rain unlikely."
        else:
            precip_summary = "Completely dry conditions expected throughout the period. No rain gear required."

    # 4. Wind narrative
    if w_max is not None:
        if w_max >= 45.0 or (g_max and g_max >= 65.0):
            wind_summary = f"Breezy to stormy winds averaging {w_max:.0f} km/h with gusts up to {g_max or w_max:.0f} km/h. Secure loose outdoor objects."
        elif w_max >= 25.0:
            wind_summary = f"Moderate breeze at {w_max:.0f} km/h. Noticeable in open spaces."
        else:
            wind_summary = f"Calm to light winds around {w_max:.0f} km/h."
    else:
        wind_summary = "Gentle airflow."

    return DailyBriefing(
        date=date_str,
        day_label=day_label,
        headline=headline,
        temperature_summary=temp_summary,
        precipitation_summary=precip_summary,
        wind_summary=wind_summary,
        advisories=[],
    )


def generate_briefings(
    current: Optional[CurrentConditions],
    hourly: HourlyData,
    daily: DailyData,
) -> List[DailyBriefing]:
    """Generate briefings for Today and Tomorrow."""
    briefings = []
    if daily.time and len(daily.time) >= 1:
        briefings.append(generate_daily_briefing(0, "Today's Outlook", current, hourly, daily))
    if daily.time and len(daily.time) >= 2:
        briefings.append(generate_daily_briefing(1, "Tomorrow's Outlook", None, hourly, daily))
    return briefings
