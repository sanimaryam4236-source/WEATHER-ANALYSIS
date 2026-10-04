"""
Unit system management and conversion utilities.

Pure logic module: Converts meteorological values between Metric and Imperial systems
and formats values safely (returning '—' for missing values without displaying fake zeros).
"""

from enum import Enum
from typing import Optional, Union, Dict


class UnitSystem(str, Enum):
    METRIC = "Metric (°C, km/h, mm)"
    IMPERIAL = "Imperial (°F, mph, in)"


# Unit symbol maps
UNIT_SYMBOLS: Dict[UnitSystem, Dict[str, str]] = {
    UnitSystem.METRIC: {
        "temperature": "°C",
        "wind_speed": "km/h",
        "precipitation": "mm",
        "pressure": "hPa",
        "visibility": "km",
        "uv_index": "",
        "humidity": "%",
        "cloud_cover": "%",
    },
    UnitSystem.IMPERIAL: {
        "temperature": "°F",
        "wind_speed": "mph",
        "precipitation": "in",
        "pressure": "inHg",
        "visibility": "mi",
        "uv_index": "",
        "humidity": "%",
        "cloud_cover": "%",
    },
}


def celsius_to_fahrenheit(celsius: Optional[float]) -> Optional[float]:
    """Convert Celsius to Fahrenheit."""
    if celsius is None:
        return None
    return round((celsius * 9.0 / 5.0) + 32.0, 1)


def fahrenheit_to_celsius(fahrenheit: Optional[float]) -> Optional[float]:
    """Convert Fahrenheit to Celsius."""
    if fahrenheit is None:
        return None
    return round((fahrenheit - 32.0) * 5.0 / 9.0, 1)


def kmh_to_mph(kmh: Optional[float]) -> Optional[float]:
    """Convert kilometers per hour to miles per hour."""
    if kmh is None:
        return None
    return round(kmh * 0.621371, 1)


def mm_to_inches(mm: Optional[float]) -> Optional[float]:
    """Convert millimeters to inches."""
    if mm is None:
        return None
    return round(mm * 0.0393701, 2)


def hpa_to_inhg(hpa: Optional[float]) -> Optional[float]:
    """Convert hectopascals (hPa) to inches of mercury (inHg)."""
    if hpa is None:
        return None
    return round(hpa * 0.02953, 2)


def meters_to_km(meters: Optional[float]) -> Optional[float]:
    """Convert meters to kilometers."""
    if meters is None:
        return None
    return round(meters / 1000.0, 1)


def meters_to_miles(meters: Optional[float]) -> Optional[float]:
    """Convert meters to statute miles."""
    if meters is None:
        return None
    return round(meters * 0.000621371, 1)


def convert_temperature(val_c: Optional[float], system: UnitSystem) -> Optional[float]:
    """Convert base Celsius value to the selected unit system."""
    if val_c is None:
        return None
    return celsius_to_fahrenheit(val_c) if system == UnitSystem.IMPERIAL else round(val_c, 1)


def convert_wind_speed(val_kmh: Optional[float], system: UnitSystem) -> Optional[float]:
    """Convert base km/h wind speed to the selected unit system."""
    if val_kmh is None:
        return None
    return kmh_to_mph(val_kmh) if system == UnitSystem.IMPERIAL else round(val_kmh, 1)


def convert_precipitation(val_mm: Optional[float], system: UnitSystem) -> Optional[float]:
    """Convert base mm precipitation to the selected unit system."""
    if val_mm is None:
        return None
    return mm_to_inches(val_mm) if system == UnitSystem.IMPERIAL else round(val_mm, 1)


def convert_pressure(val_hpa: Optional[float], system: UnitSystem) -> Optional[float]:
    """Convert base hPa pressure to the selected unit system."""
    if val_hpa is None:
        return None
    return hpa_to_inhg(val_hpa) if system == UnitSystem.IMPERIAL else round(val_hpa, 1)


def convert_visibility(val_meters: Optional[float], system: UnitSystem) -> Optional[float]:
    """Convert base meters visibility to km or miles."""
    if val_meters is None:
        return None
    return meters_to_miles(val_meters) if system == UnitSystem.IMPERIAL else meters_to_km(val_meters)


def format_value(
    val: Optional[Union[int, float]],
    unit: str = "",
    precision: int = 1,
    fallback: str = "—"
) -> str:
    """
    Format a meteorological measurement safely.
    Returns fallback ('—') if val is None, avoiding misleading fake zeros.
    """
    if val is None:
        return fallback
    try:
        if precision == 0:
            formatted = f"{int(round(val))}"
        else:
            formatted = f"{val:.{precision}f}"
        return f"{formatted} {unit}".strip() if unit else formatted
    except (ValueError, TypeError):
        return fallback
