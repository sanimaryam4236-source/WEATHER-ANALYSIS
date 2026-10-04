"""
SkyDeck Configuration & Settings Module.

Central source of truth for:
- API URLs & parameters
- Cache time-to-live (TTL) limits
- HTTP timeout and exponential backoff retry policies
- Weather advisory thresholds
- Activity suitability weights and ideal ranges
- Unit defaults and attribution details

Guiding Rule: Config over constants. No hardcoded thresholds or endpoints in logic.
"""

from typing import Dict, Any


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"


# -----------------------------------------------------------------------------
# Attribution & Compliance
# -----------------------------------------------------------------------------
APP_NAME = "SkyDeck"
APP_SUBTITLE = "Smart Weather Intelligence Dashboard"
DATA_ATTRIBUTION = "Weather data provided by Open-Meteo.com (CC BY 4.0)"
ATTRIBUTION_URL = "https://open-meteo.com/"
ADVISORY_DISCLAIMER = (
    "Model-derived advisory, not an official warning. "
    "Check national meteorological agency bulletins for life-safety emergencies."
)
AIR_QUALITY_DISCLAIMER = (
    "Modelled atmospheric composition data (CAMS / Open-Meteo). "
    "Regional ground-level measurements may vary."
)


# -----------------------------------------------------------------------------
# Network & Reliability
# -----------------------------------------------------------------------------
REQUEST_TIMEOUT_SECONDS = 8.0
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0
BACKOFF_FACTOR = 2.0
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]


# -----------------------------------------------------------------------------
# Cache TTLs (in seconds)
# -----------------------------------------------------------------------------
CACHE_TTL_GEOCODING = 86400        # 24 hours (cities rarely move)
CACHE_TTL_FORECAST = 900           # 15 minutes (forecast updates hourly/sub-hourly)
CACHE_TTL_AIR_QUALITY = 1800       # 30 minutes
CACHE_TTL_ARCHIVE = 604800         # 7 days (historical data is static)


# -----------------------------------------------------------------------------
# API Limits & Budgeting
# -----------------------------------------------------------------------------
DAILY_CALL_LIMIT = 10000
HOURLY_CALL_LIMIT = 5000
MINUTE_CALL_LIMIT = 600


# -----------------------------------------------------------------------------
# API Request Parameters
# -----------------------------------------------------------------------------
CURRENT_PARAMS = [
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "is_day",
    "precipitation",
    "weather_code",
    "cloud_cover",
    "pressure_msl",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
]

HOURLY_PARAMS = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "apparent_temperature",
    "precipitation_probability",
    "precipitation",
    "weather_code",
    "pressure_msl",
    "cloud_cover",
    "visibility",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
    "uv_index",
]

DAILY_PARAMS = [
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "sunrise",
    "sunset",
    "uv_index_max",
    "precipitation_sum",
    "precipitation_probability_max",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "wind_direction_10m_dominant",
]

AIR_QUALITY_HOURLY_PARAMS = [
    "pm10",
    "pm2_5",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
    "uv_index",
    "european_aqi",
    "us_aqi",
]


# -----------------------------------------------------------------------------
# Advisory Thresholds
# -----------------------------------------------------------------------------
ADVISORY_THRESHOLDS = {
    "heat": {
        "temp_c": 35.0,
        "title": "Extreme Heat Advisory",
        "description": "High temperatures pose risk of heat exhaustion and dehydration.",
        "severity": "warning",
    },
    "cold": {
        "temp_c": 0.0,
        "title": "Freezing Temperature Advisory",
        "description": "Sub-zero temperatures may cause icy patches and frostbite risk.",
        "severity": "warning",
    },
    "strong_wind": {
        "speed_kmh": 45.0,
        "gust_kmh": 65.0,
        "title": "Strong Wind Advisory",
        "description": "High winds can dislodge loose objects and impede travel.",
        "severity": "warning",
    },
    "heavy_rain": {
        "rate_mm_hr": 5.0,
        "daily_sum_mm": 25.0,
        "title": "Heavy Precipitation Advisory",
        "description": "Heavy rainfall may cause localized pooling and poor visibility.",
        "severity": "warning",
    },
    "high_uv": {
        "uv_index": 7.0,
        "title": "High UV Index Advisory",
        "description": "Very high ultraviolet radiation. Sun protection is essential.",
        "severity": "warning",
    },
    "thunderstorm": {
        "wmo_codes": [95, 96, 99],
        "title": "Thunderstorm Advisory",
        "description": "Convective storm activity with lightning and potential hail.",
        "severity": "danger",
    },
    "poor_air_quality": {
        "us_aqi": 101.0,
        "title": "Unhealthy Air Quality Advisory",
        "description": "Elevated particulate/pollutant levels. Sensitive groups should stay indoors.",
        "severity": "warning",
    },
}


# -----------------------------------------------------------------------------
# Activity Suitability Configuration (Pure scoring parameters)
# -----------------------------------------------------------------------------
SUITABILITY_CONFIG: Dict[str, Dict[str, Any]] = {
    "walking": {
        "label": "Walking Around Campus",
        "ideal_temp": (16.0, 24.0),
        "acceptable_temp": (8.0, 30.0),
        "max_wind": 25.0,
        "max_rain_prob": 30.0,
        "max_rain_rate": 0.2,
        "weights": {"temp": 0.35, "wind": 0.25, "precip": 0.40},
    },
    "sports": {
        "label": "Outdoor Sports",
        "ideal_temp": (14.0, 22.0),
        "acceptable_temp": (8.0, 28.0),
        "max_wind": 25.0,
        "max_rain_prob": 30.0,
        "max_rain_rate": 0.2,
        "weights": {"temp": 0.35, "wind": 0.25, "precip": 0.40},
    },
    "outdoor_sport": {  # Alias for backward compatibility
        "label": "Outdoor Sports",
        "ideal_temp": (14.0, 22.0),
        "acceptable_temp": (8.0, 28.0),
        "max_wind": 25.0,
        "max_rain_prob": 30.0,
        "max_rain_rate": 0.2,
        "weights": {"temp": 0.35, "wind": 0.25, "precip": 0.40},
    },
    "photography": {
        "label": "Photography",
        "ideal_temp": (15.0, 28.0),
        "acceptable_temp": (10.0, 32.0),
        "max_wind": 30.0,
        "max_rain_prob": 20.0,
        "max_rain_rate": 0.1,
        "weights": {"temp": 0.30, "wind": 0.30, "precip": 0.40},
    },
    "gis_fieldwork": {
        "label": "GIS / Fieldwork",
        "ideal_temp": (12.0, 26.0),
        "acceptable_temp": (6.0, 30.0),
        "max_wind": 20.0,
        "max_rain_prob": 20.0,
        "max_rain_rate": 0.1,
        "weights": {"temp": 0.30, "wind": 0.30, "precip": 0.40},
    },
    "running": {
        "label": "Running / Jogging",
        "ideal_temp": (10.0, 20.0),
        "acceptable_temp": (5.0, 25.0),
        "max_wind": 25.0,
        "max_rain_prob": 25.0,
        "max_rain_rate": 0.2,
        "weights": {"temp": 0.40, "wind": 0.20, "precip": 0.40},
    },
    "commute": {
        "label": "Daily Commute & Cycling",
        "ideal_temp": (12.0, 24.0),
        "acceptable_temp": (4.0, 32.0),
        "max_wind": 35.0,
        "max_rain_prob": 40.0,
        "max_rain_rate": 0.5,
        "weights": {"temp": 0.25, "wind": 0.35, "precip": 0.40},
    },
    "laundry": {
        "label": "Outdoor Clothes Drying",
        "ideal_temp": (18.0, 32.0),
        "acceptable_temp": (12.0, 40.0),
        "max_humidity": 65.0,
        "min_wind": 8.0,
        "max_wind": 40.0,
        "max_rain_prob": 15.0,
        "max_rain_rate": 0.0,
        "weights": {"temp": 0.25, "humidity": 0.30, "wind": 0.20, "precip": 0.25},
    },
    "travel": {
        "label": "Sightseeing & Leisure Travel",
        "ideal_temp": (16.0, 26.0),
        "acceptable_temp": (10.0, 32.0),
        "max_wind": 30.0,
        "max_rain_prob": 25.0,
        "max_rain_rate": 0.3,
        "weights": {"temp": 0.35, "wind": 0.20, "precip": 0.45},
    },
    "farming": {
        "label": "Farming & Field Spraying",
        "ideal_temp": (12.0, 24.0),
        "acceptable_temp": (6.0, 30.0),
        "max_wind": 15.0,
        "max_rain_prob": 20.0,
        "max_rain_rate": 0.1,
        "weights": {"temp": 0.20, "wind": 0.50, "precip": 0.30},
    },
}


# -----------------------------------------------------------------------------
# Default Cities & Storage
# -----------------------------------------------------------------------------
DEFAULT_CITIES = [
    {
        "id": 1176615,
        "name": "Islamabad",
        "latitude": 33.6844,
        "longitude": 73.0479,
        "country": "Pakistan",
        "admin1": "Federal Capital Territory",
        "timezone": "Asia/Karachi",
    },
    {
        "id": 1172451,
        "name": "Lahore",
        "latitude": 31.5204,
        "longitude": 74.3587,
        "country": "Pakistan",
        "admin1": "Punjab",
        "timezone": "Asia/Karachi",
    },
    {
        "id": 1174872,
        "name": "Karachi",
        "latitude": 24.8607,
        "longitude": 67.0011,
        "country": "Pakistan",
        "admin1": "Sindh",
        "timezone": "Asia/Karachi",
    },
    {
        "id": 1166993,
        "name": "Rawalpindi",
        "latitude": 33.5986,
        "longitude": 73.0441,
        "country": "Pakistan",
        "admin1": "Punjab",
        "timezone": "Asia/Karachi",
    },
    {
        "id": 1168194,
        "name": "Peshawar",
        "latitude": 34.0151,
        "longitude": 71.5249,
        "country": "Pakistan",
        "admin1": "Khyber Pakhtunkhwa",
        "timezone": "Asia/Karachi",
    },
]

DEFAULT_CITY = DEFAULT_CITIES[0]

SAVED_CITIES_STORAGE_FILE = "saved_cities.json"
MAX_SAVED_CITIES = 8

