import json
import requests

cities = {
    'new_york': {'name': 'New York', 'lat': 40.7128, 'lon': -74.0060},
    'tokyo': {'name': 'Tokyo', 'lat': 35.6895, 'lon': 139.6917},
    'paris': {'name': 'Paris', 'lat': 48.8566, 'lon': 2.3522}
}

for key, info in cities.items():
    print(f"Fetching {info['name']}...")
    geo = requests.get(
        f"https://geocoding-api.open-meteo.com/v1/search?name={info['name']}&count=5&language=en&format=json"
    ).json()
    with open(f"sample_data/geocoding_{key}.json", "w") as f:
        json.dump(geo, f, indent=2)

    params = {
        'latitude': info['lat'],
        'longitude': info['lon'],
        'current': [
            'temperature_2m', 'relative_humidity_2m', 'apparent_temperature', 
            'is_day', 'precipitation', 'weather_code', 'cloud_cover', 
            'pressure_msl', 'wind_speed_10m', 'wind_direction_10m', 'wind_gusts_10m'
        ],
        'hourly': [
            'temperature_2m', 'relative_humidity_2m', 'dew_point_2m', 
            'apparent_temperature', 'precipitation_probability', 'precipitation', 
            'weather_code', 'pressure_msl', 'cloud_cover', 'visibility', 
            'wind_speed_10m', 'wind_direction_10m', 'wind_gusts_10m', 'uv_index'
        ],
        'daily': [
            'weather_code', 'temperature_2m_max', 'temperature_2m_min', 
            'apparent_temperature_max', 'apparent_temperature_min', 
            'sunrise', 'sunset', 'uv_index_max', 'precipitation_sum', 
            'precipitation_probability_max', 'wind_speed_10m_max', 
            'wind_gusts_10m_max', 'wind_direction_10m_dominant'
        ],
        'timezone': 'auto',
        'forecast_days': 16
    }
    fc = requests.get('https://api.open-meteo.com/v1/forecast', params=params).json()
    with open(f"sample_data/forecast_{key}.json", "w") as f:
        json.dump(fc, f, indent=2)

    aq_params = {
        'latitude': info['lat'],
        'longitude': info['lon'],
        'hourly': ['pm10', 'pm2_5', 'carbon_monoxide', 'nitrogen_dioxide', 'sulphur_dioxide', 'ozone', 'uv_index', 'european_aqi', 'us_aqi'],
        'timezone': 'auto'
    }
    aq = requests.get('https://air-quality-api.open-meteo.com/v1/air-quality', params=aq_params).json()
    with open(f"sample_data/air_quality_{key}.json", "w") as f:
        json.dump(aq, f, indent=2)

print("Saved sample data for New York, Tokyo, Paris!")
