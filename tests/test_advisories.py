"""
Unit tests for rule-based meteorological advisories.
"""

from src.skydeck.domain.models import CurrentConditions
from src.skydeck.services.advisories import evaluate_advisories
from config.settings import ADVISORY_DISCLAIMER


def test_heat_advisory_trigger():
    current = CurrentConditions(time="2026-10-04T12:00", temperature_2m=38.5)
    advisories = evaluate_advisories(current)
    types = [a.advisory_type for a in advisories]

    assert "heat" in types
    heat_adv = next(a for a in advisories if a.advisory_type == "heat")
    assert heat_adv.severity == "warning"
    assert "38.5°C" in heat_adv.trigger_value
    assert heat_adv.disclaimer == ADVISORY_DISCLAIMER


def test_thunderstorm_advisory_trigger():
    current = CurrentConditions(time="2026-10-04T12:00", weather_code=95)
    advisories = evaluate_advisories(current)
    types = [a.advisory_type for a in advisories]

    assert "thunderstorm" in types
    ts_adv = next(a for a in advisories if a.advisory_type == "thunderstorm")
    assert ts_adv.severity == "danger"


def test_strong_wind_advisory():
    current = CurrentConditions(time="2026-10-04T12:00", wind_speed_10m=55.0, wind_gusts_10m=75.0)
    advisories = evaluate_advisories(current)
    types = [a.advisory_type for a in advisories]
    assert "strong_wind" in types


def test_no_advisories_on_calm_conditions():
    current = CurrentConditions(time="2026-10-04T12:00", temperature_2m=21.0, wind_speed_10m=12.0, precipitation=0.0, weather_code=0)
    advisories = evaluate_advisories(current)
    assert len(advisories) == 0
