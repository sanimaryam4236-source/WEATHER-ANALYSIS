"""
Weather Advisory Evaluation Service.

Pure logic: Evaluates meteorological data against thresholds defined in config.
Generates structured advisories for heat, cold, high wind, heavy rain, high UV,
thunderstorms, and poor air quality.

Mandatory compliance: Appends the standard model-derived advisory disclaimer.
"""

from typing import List, Optional
from config.settings import ADVISORY_THRESHOLDS, ADVISORY_DISCLAIMER
from src.skydeck.domain.models import (
    CurrentConditions,
    HourlyData,
    DailyData,
    AirQualityData,
    AdvisoryItem,
)
from src.skydeck.domain.weather_codes import is_thunderstorm_code


def evaluate_advisories(
    current: CurrentConditions,
    hourly: Optional[HourlyData] = None,
    daily: Optional[DailyData] = None,
    air_quality: Optional[AirQualityData] = None,
) -> List[AdvisoryItem]:
    """
    Evaluate weather conditions and return active advisories.
    Pure function: no I/O, no network, no UI dependencies.
    """
    advisories: List[AdvisoryItem] = []

    # 1. Thunderstorm Advisory
    thunderstorm_detected = False
    ts_start, ts_end = None, None
    if current.weather_code is not None and is_thunderstorm_code(current.weather_code):
        thunderstorm_detected = True
        ts_start = current.time

    if hourly and hourly.weather_code:
        # Check next 24 hours
        next_24_codes = hourly.weather_code[:24]
        next_24_times = hourly.time[:24]
        for t, code in zip(next_24_times, next_24_codes):
            if code is not None and is_thunderstorm_code(code):
                if not thunderstorm_detected:
                    thunderstorm_detected = True
                    ts_start = t
                ts_end = t

    if thunderstorm_detected:
        cfg = ADVISORY_THRESHOLDS["thunderstorm"]
        advisories.append(
            AdvisoryItem(
                advisory_type="thunderstorm",
                title=cfg["title"],
                severity=cfg["severity"],
                description=cfg["description"],
                trigger_value="Thunderstorm WMO code detected in current/forecast window",
                start_time=ts_start,
                end_time=ts_end,
                disclaimer=ADVISORY_DISCLAIMER,
            )
        )

    # 2. Extreme Heat Advisory
    heat_thresh = ADVISORY_THRESHOLDS["heat"]["temp_c"]
    max_temp = current.temperature_2m or -999.0
    heat_start = current.time if max_temp >= heat_thresh else None
    heat_end = None

    if hourly and hourly.temperature_2m:
        for t, temp in zip(hourly.time[:24], hourly.temperature_2m[:24]):
            if temp is not None and temp >= heat_thresh:
                if heat_start is None:
                    heat_start = t
                heat_end = t
                if temp > max_temp:
                    max_temp = temp

    if heat_start is not None:
        cfg = ADVISORY_THRESHOLDS["heat"]
        advisories.append(
            AdvisoryItem(
                advisory_type="heat",
                title=cfg["title"],
                severity=cfg["severity"],
                description=cfg["description"],
                trigger_value=f"Peak temperature {max_temp:.1f}°C (exceeds {heat_thresh:.0f}°C threshold)",
                start_time=heat_start,
                end_time=heat_end,
                disclaimer=ADVISORY_DISCLAIMER,
            )
        )

    # 3. Freezing Temperature Advisory
    cold_thresh = ADVISORY_THRESHOLDS["cold"]["temp_c"]
    min_temp = current.temperature_2m if current.temperature_2m is not None else 999.0
    cold_start = current.time if min_temp <= cold_thresh else None
    cold_end = None

    if hourly and hourly.temperature_2m:
        for t, temp in zip(hourly.time[:24], hourly.temperature_2m[:24]):
            if temp is not None and temp <= cold_thresh:
                if cold_start is None:
                    cold_start = t
                cold_end = t
                if temp < min_temp:
                    min_temp = temp

    if cold_start is not None:
        cfg = ADVISORY_THRESHOLDS["cold"]
        advisories.append(
            AdvisoryItem(
                advisory_type="cold",
                title=cfg["title"],
                severity=cfg["severity"],
                description=cfg["description"],
                trigger_value=f"Minimum temperature {min_temp:.1f}°C (at or below {cold_thresh:.0f}°C freezing threshold)",
                start_time=cold_start,
                end_time=cold_end,
                disclaimer=ADVISORY_DISCLAIMER,
            )
        )

    # 4. Strong Wind Advisory
    wind_thresh = ADVISORY_THRESHOLDS["strong_wind"]["speed_kmh"]
    gust_thresh = ADVISORY_THRESHOLDS["strong_wind"]["gust_kmh"]
    max_wind = current.wind_speed_10m or 0.0
    max_gust = current.wind_gusts_10m or 0.0
    wind_start = current.time if (max_wind >= wind_thresh or max_gust >= gust_thresh) else None
    wind_end = None

    if hourly and hourly.wind_speed_10m:
        for i, (t, spd) in enumerate(zip(hourly.time[:24], hourly.wind_speed_10m[:24])):
            gst = hourly.wind_gusts_10m[i] if i < len(hourly.wind_gusts_10m) else None
            triggered = (spd is not None and spd >= wind_thresh) or (gst is not None and gst >= gust_thresh)
            if triggered:
                if wind_start is None:
                    wind_start = t
                wind_end = t
                if spd and spd > max_wind:
                    max_wind = spd
                if gst and gst > max_gust:
                    max_gust = gst

    if wind_start is not None:
        cfg = ADVISORY_THRESHOLDS["strong_wind"]
        advisories.append(
            AdvisoryItem(
                advisory_type="strong_wind",
                title=cfg["title"],
                severity=cfg["severity"],
                description=cfg["description"],
                trigger_value=f"Max wind {max_wind:.1f} km/h, peak gusts {max_gust:.1f} km/h (threshold {wind_thresh:.0f}/{gust_thresh:.0f} km/h)",
                start_time=wind_start,
                end_time=wind_end,
                disclaimer=ADVISORY_DISCLAIMER,
            )
        )

    # 5. Heavy Rain Advisory
    rain_rate_thresh = ADVISORY_THRESHOLDS["heavy_rain"]["rate_mm_hr"]
    daily_sum_thresh = ADVISORY_THRESHOLDS["heavy_rain"]["daily_sum_mm"]
    max_rain_rate = current.precipitation or 0.0
    rain_start = current.time if max_rain_rate >= rain_rate_thresh else None
    rain_end = None

    if hourly and hourly.precipitation:
        for t, rate in zip(hourly.time[:24], hourly.precipitation[:24]):
            if rate is not None and rate >= rain_rate_thresh:
                if rain_start is None:
                    rain_start = t
                rain_end = t
                if rate > max_rain_rate:
                    max_rain_rate = rate

    daily_sum = daily.precipitation_sum[0] if (daily and daily.precipitation_sum and daily.precipitation_sum[0] is not None) else 0.0
    if rain_start is not None or daily_sum >= daily_sum_thresh:
        cfg = ADVISORY_THRESHOLDS["heavy_rain"]
        advisories.append(
            AdvisoryItem(
                advisory_type="heavy_rain",
                title=cfg["title"],
                severity=cfg["severity"],
                description=cfg["description"],
                trigger_value=f"Peak rain rate {max_rain_rate:.1f} mm/h, 24h expected accumulation {daily_sum:.1f} mm",
                start_time=rain_start or (daily.time[0] if daily and daily.time else None),
                end_time=rain_end,
                disclaimer=ADVISORY_DISCLAIMER,
            )
        )

    # 6. High UV Advisory
    uv_thresh = ADVISORY_THRESHOLDS["high_uv"]["uv_index"]
    max_uv = 0.0
    uv_start, uv_end = None, None
    if hourly and hourly.uv_index:
        for t, uv in zip(hourly.time[:24], hourly.uv_index[:24]):
            if uv is not None and uv >= uv_thresh:
                if uv_start is None:
                    uv_start = t
                uv_end = t
                if uv > max_uv:
                    max_uv = uv

    if uv_start is not None:
        cfg = ADVISORY_THRESHOLDS["high_uv"]
        advisories.append(
            AdvisoryItem(
                advisory_type="high_uv",
                title=cfg["title"],
                severity=cfg["severity"],
                description=cfg["description"],
                trigger_value=f"Peak UV Index {max_uv:.1f} (exceeds high threshold of {uv_thresh:.0f})",
                start_time=uv_start,
                end_time=uv_end,
                disclaimer=ADVISORY_DISCLAIMER,
            )
        )

    # 7. Poor Air Quality Advisory
    if air_quality and air_quality.us_aqi:
        aqi_thresh = ADVISORY_THRESHOLDS["poor_air_quality"]["us_aqi"]
        max_aqi = 0.0
        aq_start, aq_end = None, None
        for t, aqi in zip(air_quality.time[:24], air_quality.us_aqi[:24]):
            if aqi is not None and aqi >= aqi_thresh:
                if aq_start is None:
                    aq_start = t
                aq_end = t
                if aqi > max_aqi:
                    max_aqi = aqi

        if aq_start is not None:
            cfg = ADVISORY_THRESHOLDS["poor_air_quality"]
            advisories.append(
                AdvisoryItem(
                    advisory_type="poor_air_quality",
                    title=cfg["title"],
                    severity=cfg["severity"],
                    description=cfg["description"],
                    trigger_value=f"US AQI reached {max_aqi:.0f} (unhealthy threshold {aqi_thresh:.0f})",
                    start_time=aq_start,
                    end_time=aq_end,
                    disclaimer=ADVISORY_DISCLAIMER,
                )
            )

    return advisories
