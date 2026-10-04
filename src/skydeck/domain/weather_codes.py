"""
WMO Weather Code interpretation table.

Provides human-readable descriptions, condition categories, day/night icons,
and severity indicators according to the World Meteorological Organization (WMO) code table 4677.
"""

from typing import Dict, NamedTuple


class WeatherCodeInfo(NamedTuple):
    code: int
    description: str
    day_icon: str
    night_icon: str
    category: str
    is_thunderstorm: bool
    is_severe: bool


# Comprehensive WMO Code Mapping
WMO_CODE_TABLE: Dict[int, WeatherCodeInfo] = {
    0: WeatherCodeInfo(0, "Clear sky", "☀️", "🌙", "clear", False, False),
    1: WeatherCodeInfo(1, "Mainly clear", "🌤️", "🌤️", "clear", False, False),
    2: WeatherCodeInfo(2, "Partly cloudy", "⛅", "⛅", "cloudy", False, False),
    3: WeatherCodeInfo(3, "Overcast", "☁️", "☁️", "cloudy", False, False),
    45: WeatherCodeInfo(45, "Fog", "🌫️", "🌫️", "fog", False, False),
    48: WeatherCodeInfo(48, "Depositing rime fog", "🌫️", "🌫️", "fog", False, False),
    51: WeatherCodeInfo(51, "Light drizzle", "🌦️", "🌧️", "drizzle", False, False),
    53: WeatherCodeInfo(53, "Moderate drizzle", "🌧️", "🌧️", "drizzle", False, False),
    55: WeatherCodeInfo(55, "Dense drizzle", "🌧️", "🌧️", "drizzle", False, False),
    56: WeatherCodeInfo(56, "Light freezing drizzle", "🌧️❄️", "🌧️❄️", "freezing_drizzle", False, True),
    57: WeatherCodeInfo(57, "Dense freezing drizzle", "🌧️❄️", "🌧️❄️", "freezing_drizzle", False, True),
    61: WeatherCodeInfo(61, "Slight rain", "🌦️", "🌧️", "rain", False, False),
    62: WeatherCodeInfo(62, "Moderate rain", "🌧️", "🌧️", "rain", False, False),
    63: WeatherCodeInfo(63, "Moderate rain", "🌧️", "🌧️", "rain", False, False),
    65: WeatherCodeInfo(65, "Heavy rain", "🌧️⚡", "🌧️⚡", "rain", False, True),
    66: WeatherCodeInfo(66, "Light freezing rain", "🌧️❄️", "🌧️❄️", "freezing_rain", False, True),
    67: WeatherCodeInfo(67, "Heavy freezing rain", "🌧️❄️", "🌧️❄️", "freezing_rain", False, True),
    71: WeatherCodeInfo(71, "Slight snow fall", "🌨️", "🌨️", "snow", False, False),
    73: WeatherCodeInfo(73, "Moderate snow fall", "🌨️", "🌨️", "snow", False, False),
    75: WeatherCodeInfo(75, "Heavy snow fall", "❄️❄️", "❄️❄️", "snow", False, True),
    77: WeatherCodeInfo(77, "Snow grains", "❄️", "❄️", "snow", False, False),
    80: WeatherCodeInfo(80, "Slight rain showers", "🌦️", "🌧️", "rain_shower", False, False),
    81: WeatherCodeInfo(81, "Moderate rain showers", "🌧️", "🌧️", "rain_shower", False, False),
    82: WeatherCodeInfo(82, "Violent rain showers", "⛈️", "⛈️", "rain_shower", False, True),
    85: WeatherCodeInfo(85, "Slight snow showers", "🌨️", "🌨️", "snow_shower", False, False),
    86: WeatherCodeInfo(86, "Heavy snow showers", "❄️🌨️", "❄️🌨️", "snow_shower", False, True),
    95: WeatherCodeInfo(95, "Thunderstorm", "⛈️", "⛈️", "thunderstorm", True, True),
    96: WeatherCodeInfo(96, "Thunderstorm with slight hail", "⛈️🌨️", "⛈️🌨️", "thunderstorm", True, True),
    99: WeatherCodeInfo(99, "Thunderstorm with heavy hail", "⛈️❄️", "⛈️❄️", "thunderstorm", True, True),
}


def get_weather_info(code: int, is_day: int = 1) -> WeatherCodeInfo:
    """
    Look up WMO weather information.

    Args:
        code: The integer WMO code.
        is_day: 1 for daytime, 0 for nighttime.

    Returns:
        WeatherCodeInfo tuple with description, icon, category, and flags.
    """
    if code in WMO_CODE_TABLE:
        return WMO_CODE_TABLE[code]
    return WeatherCodeInfo(
        code=code,
        description=f"Unknown weather ({code})",
        day_icon="❓",
        night_icon="❓",
        category="unknown",
        is_thunderstorm=False,
        is_severe=False,
    )


def get_weather_icon(code: int, is_day: int = 1) -> str:
    """Return appropriate emoji icon for code and day/night status."""
    info = get_weather_info(code, is_day)
    return info.day_icon if is_day == 1 else info.night_icon


def get_weather_description(code: int) -> str:
    """Return text description for WMO code."""
    return get_weather_info(code).description


def is_thunderstorm_code(code: int) -> bool:
    """Check if the code indicates a thunderstorm."""
    return get_weather_info(code).is_thunderstorm
