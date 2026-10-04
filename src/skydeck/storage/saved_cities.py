"""
Storage manager for user favorite cities and last-active session state.

Saves pinned cities and the last-inspected location to a lightweight JSON file
so state persists across app reloads. Enforces multi-city bounds, coordinate-based
duplicate checking, index-shift safety, and robust corrupt-store recovery.
"""

import json
import os
from typing import List, Dict, Any, Optional, Tuple
from config.settings import SAVED_CITIES_STORAGE_FILE, DEFAULT_CITIES, DEFAULT_CITY, MAX_SAVED_CITIES


def _are_coordinates_duplicate(c1: Dict[str, Any], c2: Dict[str, Any], threshold: float = 0.05) -> bool:
    """Check if two city dicts refer to the same location by ID or approx lat/lon coordinates."""
    id1, id2 = c1.get("id"), c2.get("id")
    if id1 and id2 and id1 == id2:
        return True

    lat1, lon1 = c1.get("latitude"), c1.get("longitude")
    lat2, lon2 = c2.get("latitude"), c2.get("longitude")
    if lat1 is not None and lat2 is not None and lon1 is not None and lon2 is not None:
        if abs(float(lat1) - float(lat2)) < threshold and abs(float(lon1) - float(lon2)) < threshold:
            return True

    name1 = str(c1.get("name", "")).strip().lower()
    name2 = str(c2.get("name", "")).strip().lower()
    country1 = str(c1.get("country", "")).strip().lower()
    country2 = str(c2.get("country", "")).strip().lower()
    if name1 and name1 == name2 and country1 == country2:
        return True

    return False


class SavedCitiesManager:
    """Manages local JSON persistence for bookmarked cities."""

    def __init__(self, filepath: str = SAVED_CITIES_STORAGE_FILE):
        self.filepath = filepath

    def _default_payload(self) -> Dict[str, Any]:
        return {
            "last_active": DEFAULT_CITY,
            "saved": list(DEFAULT_CITIES),
        }

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(self.filepath):
            return self._default_payload()
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                saved = data.get("saved", [])
                if not isinstance(saved, list) or len(saved) == 0:
                    return self._default_payload()
                last_active = data.get("last_active")
                if not isinstance(last_active, dict) or "name" not in last_active:
                    last_active = saved[0]
                return {"last_active": last_active, "saved": saved}
        except Exception:
            return self._default_payload()

    def _save(self, data: Dict[str, Any]):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def get_saved_cities(self) -> List[Dict[str, Any]]:
        """Return list of saved city dicts."""
        data = self._load()
        return data.get("saved", list(DEFAULT_CITIES))

    def find_duplicate(self, city: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find matching saved city if already bookmarked."""
        for item in self.get_saved_cities():
            if _are_coordinates_duplicate(item, city):
                return item
        return None

    def add_saved_city(self, city: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Add a city to favorites.
        Returns (success: bool, message: str).
        """
        data = self._load()
        saved = data.get("saved", [])

        # Check duplicate
        dup = self.find_duplicate(city)
        if dup:
            data["last_active"] = dup
            self._save(data)
            return True, f"'{dup.get('name')}' is already in your cities list. Activated it!"

        # Check maximum capacity
        if len(saved) >= MAX_SAVED_CITIES:
            return False, f"Maximum city limit reached ({MAX_SAVED_CITIES} cities). Remove a city first."

        saved.append(city)
        data["saved"] = saved
        data["last_active"] = city
        self._save(data)
        return True, f"Added '{city.get('name')}' to Quick Cities."

    def remove_saved_city(self, target_city: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Remove city from favorites. Minimum 1 city enforced.
        Returns (success: bool, message: str, next_active_city: Optional[Dict]).
        """
        data = self._load()
        saved = data.get("saved", [])

        if len(saved) <= 1:
            return False, "Cannot remove the last remaining city. At least 1 city is required.", None

        target_idx = -1
        for idx, item in enumerate(saved):
            if _are_coordinates_duplicate(item, target_city):
                target_idx = idx
                break

        if target_idx == -1:
            return False, "City not found in saved list.", None

        removed_item = saved.pop(target_idx)
        current_active = data.get("last_active", {})

        new_active = current_active
        if _are_coordinates_duplicate(current_active, removed_item):
            # If removing active city, select neighboring city
            next_idx = max(0, min(target_idx, len(saved) - 1))
            new_active = saved[next_idx]

        data["saved"] = saved
        data["last_active"] = new_active
        self._save(data)

        return True, f"Removed '{removed_item.get('name')}' from saved cities.", new_active

    def get_last_active_city(self) -> Dict[str, Any]:
        """Get the last active city, falling back to default."""
        data = self._load()
        return data.get("last_active", DEFAULT_CITY)

    def set_last_active_city(self, city: Dict[str, Any]):
        """Persist the currently selected city."""
        data = self._load()
        data["last_active"] = city
        self._save(data)


# Global storage manager instance
saved_cities_storage = SavedCitiesManager()
