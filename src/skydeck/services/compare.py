"""
Multi-City Comparison and Ranking Service.

Pure logic: Compares a collection of weather reports, computes suitability scores
for each city on a selected activity, and produces ranked comparative insights.
"""

from typing import List, Dict, Any, Union, Tuple
import pandas as pd
import plotly.express as px
from src.skydeck.services.suitability import score_single_activity


def compare_and_rank_cities(
    reports_or_provider: Any,
    locations_or_activity: Any = "outdoor_sport"
) -> Union[List[Dict[str, Any]], Tuple[pd.DataFrame, Any]]:
    """
    Compare multiple city weather reports and rank them by suitability for an activity.

    Supports dual signatures:
    1. compare_and_rank_cities(reports: List[WeatherReport], activity_key="outdoor_sport") -> List[Dict]
    2. compare_and_rank_cities(provider, locations: List[GeocodedLocation]) -> (DataFrame, Figure)
    """
    # Check if first arg is provider and second arg is list of locations
    if hasattr(reports_or_provider, "get_multi_city_forecast") and isinstance(locations_or_activity, list):
        provider = reports_or_provider
        locations = locations_or_activity
        reports = provider.get_multi_city_forecast(locations)
        ranked = compare_and_rank_cities(reports, "outdoor_sport")

        df_data = []
        for r in ranked:
            df_data.append({
                "City": r["city_name"],
                "Country": r["country"],
                "Condition": f"WMO {r['weather_code']}",
                "Temp (°C)": f"{r['temp']:.1f}°C",
                "Rain Chance": f"{r['rain_prob']:.0f}%",
                "Wind": f"{r['wind']:.1f} km/h",
                "Overall Rating": r["rating"],
                "Score": r["score"],
            })
        df = pd.DataFrame(df_data)

        # Build comparison bar chart
        fig = px.bar(
            df,
            x="City",
            y="Score",
            color="Overall Rating",
            title="Multi-City Outdoor Activity Suitability Ranking",
            text="Score",
            template="plotly_dark",
            color_discrete_map={
                "Excellent": "#22C55E",
                "Good": "#10B981",
                "Optimal": "#22C55E",
                "Moderate": "#F59E0B",
                "Marginal": "#F59E0B",
                "Poor": "#EF4444",
                "Hazardous": "#EF4444",
            }
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=300)
        return df, fig

    # Standard list of WeatherReport objects
    reports = reports_or_provider if isinstance(reports_or_provider, list) else [reports_or_provider]
    activity_key = locations_or_activity if isinstance(locations_or_activity, str) else "outdoor_sport"

    ranked = []
    for rep in reports:
        loc = rep.location
        curr = rep.current
        daily = rep.daily

        t_max = daily.temperature_2m_max[0] if (daily.temperature_2m_max and len(daily.temperature_2m_max) > 0) else curr.temperature_2m
        t_min = daily.temperature_2m_min[0] if (daily.temperature_2m_min and len(daily.temperature_2m_min) > 0) else curr.temperature_2m
        p_prob = daily.precipitation_probability_max[0] if (daily.precipitation_probability_max and len(daily.precipitation_probability_max) > 0) else 0.0

        score, rating, breakdown, blocked, reason = score_single_activity(
            activity_key=activity_key,
            temp=curr.temperature_2m,
            wind=curr.wind_speed_10m,
            rain_prob=p_prob,
            rain_rate=curr.precipitation,
            humidity=curr.relative_humidity_2m,
            weather_code=curr.weather_code,
        )

        ranked.append({
            "location": loc,
            "city_name": loc.name,
            "country": loc.country or "",
            "temp": curr.temperature_2m,
            "temp_max": t_max,
            "temp_min": t_min,
            "wind": curr.wind_speed_10m,
            "humidity": curr.relative_humidity_2m,
            "precipitation": curr.precipitation or 0.0,
            "rain_prob": p_prob,
            "weather_code": curr.weather_code or 0,
            "score": score,
            "rating": rating,
            "is_blocked": blocked,
            "block_reason": reason,
        })

    # Sort descending by score
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked
