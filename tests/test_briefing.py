"""
Unit tests for conversational daily briefing generation.
"""

from src.skydeck.domain.models import CurrentConditions, HourlyData, DailyData
from src.skydeck.services.briefing import generate_briefings


def test_briefing_generation():
    curr = CurrentConditions(time="2026-10-04T12:00", temperature_2m=18.0)
    hourly = HourlyData(
        time=[f"2026-10-04T{h:02d}:00" for h in range(48)],
        temperature_2m=[15.0 + (h % 10) for h in range(48)],
        precipitation=[0.0] * 48,
        precipitation_probability=[5.0] * 48,
    )
    daily = DailyData(
        time=["2026-10-04", "2026-10-05"],
        temperature_2m_max=[22.0, 20.0],
        temperature_2m_min=[12.0, 11.0],
        weather_code=[0, 1],
        precipitation_sum=[0.0, 0.0],
        precipitation_probability_max=[10.0, 15.0],
        wind_speed_10m_max=[15.0, 18.0],
    )

    briefings = generate_briefings(curr, hourly, daily)
    assert len(briefings) == 2
    assert "Today's Outlook" in briefings[0].day_label
    assert "Tomorrow's Outlook" in briefings[1].day_label
    assert "22°C" in briefings[0].headline or "Clear sky" in briefings[0].headline
    assert "dry" in briefings[0].precipitation_summary.lower()
