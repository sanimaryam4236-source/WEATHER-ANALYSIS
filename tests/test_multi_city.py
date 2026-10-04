"""
Unit tests for multi-city management rules and SavedCitiesManager.
"""

import os
import tempfile
import pytest
from src.skydeck.storage.saved_cities import SavedCitiesManager
from config.settings import DEFAULT_CITIES, MAX_SAVED_CITIES


@pytest.fixture
def temp_storage():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name
    manager = SavedCitiesManager(filepath=tmp_path)
    yield manager
    if os.path.exists(tmp_path):
        os.remove(tmp_path)


def test_initial_defaults(temp_storage):
    cities = temp_storage.get_saved_cities()
    assert len(cities) == len(DEFAULT_CITIES)
    assert cities[0]["name"] == "Islamabad"


def test_add_duplicate_coordinate(temp_storage):
    # Islamabad coordinate test
    dup_city = {
        "id": 99999,
        "name": "Islamabad Campus",
        "latitude": 33.6840,
        "longitude": 73.0475,
        "country": "Pakistan",
    }
    ok, msg = temp_storage.add_saved_city(dup_city)
    assert ok is True
    assert "already in your cities list" in msg


def test_max_saved_cities_limit(temp_storage):
    # Fill up to MAX_SAVED_CITIES
    for i in range(10):
        new_city = {
            "id": 20000 + i,
            "name": f"TestCity_{i}",
            "latitude": 10.0 + i,
            "longitude": 10.0 + i,
            "country": "Country",
        }
        temp_storage.add_saved_city(new_city)

    cities = temp_storage.get_saved_cities()
    assert len(cities) == MAX_SAVED_CITIES

    # Attempt adding one more
    overflow_city = {
        "id": 99999,
        "name": "Overflow City",
        "latitude": 80.0,
        "longitude": 80.0,
    }
    ok, msg = temp_storage.add_saved_city(overflow_city)
    assert ok is False
    assert "Maximum city limit reached" in msg


def test_remove_last_city_blocked(temp_storage):
    cities = temp_storage.get_saved_cities()
    # Remove until 1 remains
    while len(cities) > 1:
        temp_storage.remove_saved_city(cities[0])
        cities = temp_storage.get_saved_cities()

    assert len(cities) == 1
    ok, msg, next_active = temp_storage.remove_saved_city(cities[0])
    assert ok is False
    assert "Cannot remove the last remaining city" in msg


def test_remove_active_city_switches_neighbor(temp_storage):
    cities = temp_storage.get_saved_cities()
    active = temp_storage.get_last_active_city()
    assert active["name"] == cities[0]["name"]

    ok, msg, next_active = temp_storage.remove_saved_city(active)
    assert ok is True
    assert next_active is not None
    assert next_active["name"] != active["name"]


def test_corrupt_store_recovery(temp_storage):
    # Write invalid json
    with open(temp_storage.filepath, "w", encoding="utf-8") as f:
        f.write("{invalid_json: true")

    cities = temp_storage.get_saved_cities()
    assert len(cities) == len(DEFAULT_CITIES)
    assert cities[0]["name"] == "Islamabad"
