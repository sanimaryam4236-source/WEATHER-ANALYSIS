"""
Activity Suitability Scoring Service.

Pure mathematical logic: Calculates a 0-100 suitability score, rating,
best time window, and explanatory breakdown for outdoor activities:
- Outdoor Sport & Running
- Daily Commute & Cycling
- Outdoor Clothes Drying (Laundry)
- Sightseeing & Leisure Travel
- Farming & Field Spraying

Rule: Thunderstorm occurrence strictly forces score to 0 (Unsafe).
Thresholds and weights are loaded exclusively from config.settings.
"""

from typing import Dict, List, Optional, Tuple
from config.settings import SUITABILITY_CONFIG
from src.skydeck.domain.models import (
    CurrentConditions,
    HourlyData,
    SuitabilityScore,
)
from src.skydeck.domain.weather_codes import is_thunderstorm_code


ACTIVITY_ICONS = {
    "walking": "🚶",
    "sports": "⚽",
    "outdoor_sport": "⚽",
    "photography": "📷",
    "gis_fieldwork": "🗺️",
    "running": "🏃",
    "commute": "🚴",
    "laundry": "🧺",
    "travel": "🏛️",
    "farming": "🚜",
}


def _score_temperature(temp: Optional[float], ideal: Tuple[float, float], acceptable: Tuple[float, float]) -> Tuple[float, str]:
    if temp is None:
        return 70.0, "Temperature data unavailable"
    i_min, i_max = ideal
    a_min, a_max = acceptable

    if i_min <= temp <= i_max:
        return 100.0, f"{temp:.1f}°C (Ideal comfort)"
    elif a_min <= temp < i_min:
        pct = (temp - a_min) / (i_min - a_min)
        score = 50.0 + 50.0 * pct
        return max(0.0, min(100.0, score)), f"{temp:.1f}°C (Slightly cool)"
    elif i_max < temp <= a_max:
        pct = (a_max - temp) / (a_max - i_max)
        score = 50.0 + 50.0 * pct
        return max(0.0, min(100.0, score)), f"{temp:.1f}°C (Slightly warm)"
    elif temp < a_min:
        diff = a_min - temp
        score = max(0.0, 50.0 - diff * 8.0)
        return score, f"{temp:.1f}°C (Uncomfortably cold)"
    else:
        diff = temp - a_max
        score = max(0.0, 50.0 - diff * 8.0)
        return score, f"{temp:.1f}°C (Uncomfortably hot)"


def _score_wind(wind: Optional[float], max_wind: float, min_wind: Optional[float] = None) -> Tuple[float, str]:
    if wind is None:
        return 70.0, "Wind data unavailable"
    if min_wind and wind < min_wind:
        return 70.0, f"{wind:.1f} km/h (Calm air, slow drying)"
    if wind <= max_wind * 0.5:
        return 100.0, f"{wind:.1f} km/h (Gentle breeze)"
    elif wind <= max_wind:
        pct = (max_wind - wind) / (max_wind * 0.5)
        score = 50.0 + 50.0 * pct
        return max(0.0, min(100.0, score)), f"{wind:.1f} km/h (Moderate breeze)"
    else:
        diff = wind - max_wind
        score = max(0.0, 50.0 - diff * 4.0)
        return score, f"{wind:.1f} km/h (Excessive gusts)"


def _score_precipitation(prob: Optional[float], rate: Optional[float], max_prob: float, max_rate: float) -> Tuple[float, str]:
    p = prob if prob is not None else 0.0
    r = rate if rate is not None else 0.0

    if p == 0.0 and r == 0.0:
        return 100.0, "0% rain chance (Completely dry)"

    p_penalty = (p / 100.0) * 60.0
    r_penalty = min(50.0, (r / (max_rate if max_rate > 0 else 0.5)) * 40.0)

    score = max(0.0, 100.0 - (p_penalty + r_penalty))
    desc = f"{p:.0f}% chance, {r:.1f} mm/h"
    return score, desc


def _score_humidity(hum: Optional[float], max_hum: float) -> Tuple[float, str]:
    if hum is None:
        return 70.0, "Humidity data unavailable"
    if hum <= 50.0:
        return 100.0, f"{hum:.0f}% (Dry air, fast evaporation)"
    elif hum <= max_hum:
        pct = (max_hum - hum) / (max_hum - 50.0)
        score = 60.0 + 40.0 * pct
        return score, f"{hum:.0f}% (Moderate humidity)"
    else:
        score = max(10.0, 60.0 - (hum - max_hum) * 1.5)
        return score, f"{hum:.0f}% (Damp air, slow drying)"


def _get_rating(score: int) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Moderate"
    else:
        return "Poor"


def get_overall_activity_summary(scores: List[SuitabilityScore]) -> Tuple[str, str, str, str]:
    """
    Calculate overall campus activity index.
    Returns: (overall_rating: str, subtitle: str, student_tip: str, recommendation: str)
    """
    if not scores:
        return "GOOD", "Ideal for most outdoor activities!", "Check local forecast before stepping out.", "Great day for outdoor activities!"

    avg_score = sum(s.score for s in scores) / len(scores)

    if avg_score >= 80:
        return (
            "EXCELLENT",
            "Ideal for most outdoor activities!",
            "Perfect weather for walking, sports and outdoor study sessions!",
            "Great day for outdoor activities! The weather is comfortable and mostly clear."
        )
    elif avg_score >= 60:
        return (
            "GOOD",
            "Favorable conditions for campus activities.",
            "Great weather for campus walks and light outdoor exercise.",
            "Good conditions for outdoor study and sports today!"
        )
    elif avg_score >= 40:
        return (
            "MODERATE",
            "Fair conditions, plan outdoor activities carefully.",
            "Stay hydrated and carry an umbrella if needed.",
            "Moderate conditions. Outdoor activities are manageable with minor precautions."
        )
    else:
        return (
            "POOR",
            "Unfavorable outdoor weather.",
            "Consider indoor study spaces or covered campus walkways.",
            "Poor weather conditions. Better to stay indoors for study and activities today."
        )


def score_single_activity(
    activity_key: str,
    temp: Optional[float],
    wind: Optional[float],
    rain_prob: Optional[float],
    rain_rate: Optional[float],
    humidity: Optional[float],
    weather_code: Optional[int],
) -> Tuple[int, str, Dict[str, str], bool, Optional[str]]:
    """Calculate single score for an activity."""
    cfg = SUITABILITY_CONFIG[activity_key]
    breakdown = {}

    # Strict Thunderstorm rule
    if weather_code is not None and is_thunderstorm_code(weather_code):
        breakdown["Weather Warning"] = "Thunderstorm active (Score overridden to 0)"
        return 0, "Hazardous", breakdown, True, "Thunderstorm active. Outdoor presence is dangerous."

    weights = cfg["weights"]
    total_score = 0.0

    # Temperature factor
    t_score, t_desc = _score_temperature(temp, cfg["ideal_temp"], cfg["acceptable_temp"])
    total_score += t_score * weights["temp"]
    breakdown["Temperature"] = f"{t_desc} (Factor: {int(t_score)}/100)"

    # Wind factor
    min_w = cfg.get("min_wind")
    w_score, w_desc = _score_wind(wind, cfg["max_wind"], min_w)
    total_score += w_score * weights["wind"]
    breakdown["Wind"] = f"{w_desc} (Factor: {int(w_score)}/100)"

    # Precipitation factor
    p_score, p_desc = _score_precipitation(rain_prob, rain_rate, cfg["max_rain_prob"], cfg["max_rain_rate"])
    total_score += p_score * weights["precip"]
    breakdown["Precipitation"] = f"{p_desc} (Factor: {int(p_score)}/100)"

    # Humidity factor (if applicable)
    if "humidity" in weights:
        h_score, h_desc = _score_humidity(humidity, cfg.get("max_humidity", 70.0))
        total_score += h_score * weights["humidity"]
        breakdown["Air Humidity"] = f"{h_desc} (Factor: {int(h_score)}/100)"

    final_score = int(round(max(0.0, min(100.0, total_score))))
    rating = _get_rating(final_score)
    return final_score, rating, breakdown, False, None


def find_best_window(activity_key: str, hourly: HourlyData) -> str:
    """Find the best 3-hour daylight window (06:00 to 20:00) for this activity."""
    if not hourly.time or len(hourly.time) < 12:
        return "Midday (11:00 - 14:00)"

    best_score = -1.0
    best_range = "Midday (11:00 - 14:00)"

    # Examine 3-hour sliding windows in next 24h
    window_size = 3
    limit = min(24, len(hourly.time) - window_size)

    for i in range(limit):
        time_str = hourly.time[i]
        # Parse hour
        hour_part = 12
        if "T" in time_str:
            try:
                hour_part = int(time_str.split("T")[1].split(":")[0])
            except Exception:
                pass

        # Favor daytime hours (06 to 20)
        if not (6 <= hour_part <= 18):
            continue

        window_scores = []
        for j in range(i, i + window_size):
            t = hourly.temperature_2m[j] if j < len(hourly.temperature_2m) else None
            w = hourly.wind_speed_10m[j] if j < len(hourly.wind_speed_10m) else None
            rp = hourly.precipitation_probability[j] if j < len(hourly.precipitation_probability) else None
            rr = hourly.precipitation[j] if j < len(hourly.precipitation) else None
            hum = hourly.relative_humidity_2m[j] if j < len(hourly.relative_humidity_2m) else None
            wc = hourly.weather_code[j] if j < len(hourly.weather_code) else None

            sc, _, _, _, _ = score_single_activity(activity_key, t, w, rp, rr, hum, wc)
            window_scores.append(sc)

        avg_score = sum(window_scores) / len(window_scores) if window_scores else 0
        if avg_score > best_score:
            best_score = avg_score
            start_hour = hour_part
            end_hour = (hour_part + window_size) % 24
            best_range = f"{start_hour:02d}:00 – {end_hour:02d}:00"

    return best_range


def calculate_suitability(current: CurrentConditions, hourly: Optional[HourlyData] = None) -> List[SuitabilityScore]:
    """
    Calculate suitability scores across all configured activities.
    """
    results: List[SuitabilityScore] = []

    for key, cfg in SUITABILITY_CONFIG.items():
        score, rating, breakdown, blocked, reason = score_single_activity(
            activity_key=key,
            temp=current.temperature_2m,
            wind=current.wind_speed_10m,
            rain_prob=(hourly.precipitation_probability[0] if (hourly and hourly.precipitation_probability) else 0.0),
            rain_rate=current.precipitation,
            humidity=current.relative_humidity_2m,
            weather_code=current.weather_code,
        )

        best_window = find_best_window(key, hourly) if hourly else "Current Hour"

        results.append(
            SuitabilityScore(
                activity_key=key,
                activity_name=cfg["label"],
                icon=ACTIVITY_ICONS.get(key, "📌"),
                score=score,
                rating=rating,
                best_window=best_window,
                breakdown=breakdown,
                is_blocked=blocked,
                block_reason=reason,
            )
        )

    return results
