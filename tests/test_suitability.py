"""
Unit tests for activity suitability scoring formulas.
"""

from src.skydeck.domain.models import CurrentConditions, HourlyData
from src.skydeck.services.suitability import calculate_suitability, score_single_activity


def test_thunderstorm_forces_zero_score():
    """Rule requirement: Thunderstorm forces a score of 0."""
    score, rating, breakdown, blocked, reason = score_single_activity(
        activity_key="outdoor_sport",
        temp=20.0,
        wind=10.0,
        rain_prob=0.0,
        rain_rate=0.0,
        humidity=50.0,
        weather_code=95,  # Thunderstorm
    )
    assert score == 0
    assert rating == "Hazardous"
    assert blocked is True
    assert "Thunderstorm active" in reason


def test_ideal_conditions_high_score():
    """Pleasant 19°C, calm wind, 0% rain should yield Optimal/Excellent score >= 85."""
    score, rating, breakdown, blocked, _ = score_single_activity(
        activity_key="outdoor_sport",
        temp=19.0,
        wind=8.0,
        rain_prob=0.0,
        rain_rate=0.0,
        humidity=45.0,
        weather_code=0,
    )
    assert score >= 85
    assert rating in ["Optimal", "Excellent"]
    assert not blocked
    assert "Ideal comfort" in breakdown["Temperature"]


def test_extreme_cold_lowers_score():
    score, rating, breakdown, blocked, _ = score_single_activity(
        activity_key="outdoor_sport",
        temp=-10.0,
        wind=30.0,
        rain_prob=60.0,
        rain_rate=2.0,
        humidity=80.0,
        weather_code=71,
    )
    assert score < 35
    assert rating in ["Poor", "Hazardous"]


def test_full_suitability_suite():
    curr = CurrentConditions(
        time="2026-10-04T12:00",
        temperature_2m=18.0,
        wind_speed_10m=10.0,
        precipitation=0.0,
        relative_humidity_2m=50.0,
        weather_code=1,
    )
    hourly = HourlyData(
        time=[f"2026-10-04T{h:02d}:00" for h in range(24)],
        temperature_2m=[18.0] * 24,
        wind_speed_10m=[10.0] * 24,
        precipitation_probability=[0.0] * 24,
        precipitation=[0.0] * 24,
        relative_humidity_2m=[50.0] * 24,
        weather_code=[1] * 24,
    )

    scores = calculate_suitability(curr, hourly)
    assert len(scores) >= 5
    for item in scores:
        assert 0 <= item.score <= 100
        assert item.rating in ["Optimal", "Excellent", "Good", "Marginal", "Moderate", "Poor", "Hazardous"]
        assert len(item.breakdown) > 0

