# SkyDeck — Student Explainer & Viva Preparation Guide

> Comprehensive preparation guide for the project presentation and viva evaluation.
> Covers foundational concepts, architectural flow, scoring formulas, problems & solutions, and module-by-module walkthrough scripts.

---

## 1. Questions & Answers for the Viva Discussion

### Q1: What did I already know before starting this project?
- **Python fundamentals:** Variables, primitive data types (integers, floats, strings, booleans), conditional branching (`if/elif/else`), and loops (`for`, `while`).
- **Data structures:** Standard Python collections, including lists, dictionaries, tuples, and sets.
- **Procedural modularity:** Defining functions with parameters, default arguments, return statements, and basic script organization.

### Q2: What new concepts did I learn while building SkyDeck?
- **Web APIs & HTTP Protocol:** Understanding REST endpoints, GET query parameters, HTTP response status codes (200 OK, 429 Too Many Requests, 5xx Server Errors), and request timeouts.
- **JSON & Data Serialization:** Parsing nested JSON payloads into strongly typed domain models using Pydantic v2.
- **Robust Exception Handling:** Structuring custom exception hierarchies (`SkyDeckError`, `NetworkError`, `RateLimitError`) to guarantee raw Python tracebacks are never exposed to the end user.
- **Resilient Networking:** Implementing exponential backoff retries and respecting HTTP `Retry-After` headers.
- **Caching & Time-to-Live (TTL):** In-memory cache management with stale-while-revalidate capability to protect against network disconnects.
- **Pure Functional Logic:** Separating business logic (scoring, advisories, text briefings) from side effects (network I/O and Streamlit UI rendering).
- **Interactive Visualizations:** Generating dynamic, hardware-accelerated charts using Plotly (splines, polar wind roses, confidence bands, thermal heatmaps).
- **Web Application Architecture:** Structuring reactive UI state with Streamlit `st.session_state` and organizing responsive multi-tab layouts.

### Q3: How does the program retrieve weather data?
1. **User Input:** The user types a city name (e.g., *"London"*) into the sidebar search bar.
2. **Geocoding API:** The query is sent to Open-Meteo's Geocoding API (`https://geocoding-api.open-meteo.com/v1/search`), which resolves the query into geographic coordinates (latitude 51.50853, longitude -0.12574) and administrative region information.
3. **Disambiguation:** If multiple locations share the same name (e.g., London, UK vs London, Ontario, Canada), SkyDeck displays a disambiguation selector for the user to choose their target.
4. **Forecast API:** The coordinates, requested time horizon (16 days), and meteorological variables (`temperature_2m`, `precipitation`, `weather_code`, `wind_speed_10m`, `uv_index`, `air_quality`) are sent to the Forecast and Air Quality endpoints.
5. **Validation & Cache:** The HTTP client validates the JSON payload against Pydantic models and caches the result for 15 minutes to preserve the student's API quota.

```
[ User Search: "London" ]
          │
          ▼
┌──────────────────────────┐
│  Geocoding API (REST)    │ ───▶ Returns [{lat: 51.508, lon: -0.125, name: "London"}]
└──────────────────────────┘
          │
          ▼
┌──────────────────────────┐
│  Forecast & AQ API (REST)│ ───▶ Returns Current, Hourly (384h), Daily (16d), AQ (120h)
└──────────────────────────┘
          │
          ▼
┌──────────────────────────┐
│  Pydantic Validation     │ ───▶ Populates typed WeatherReport object (missing fields -> None)
└──────────────────────────┘
          │
          ▼
┌──────────────────────────┐
│  Pure Logic Services     │ ───▶ Advisories, Suitability Scores (0-100), Daily Briefing
└──────────────────────────┘
          │
          ▼
┌──────────────────────────┐
│  Streamlit UI & Plotly   │ ───▶ Hero Card, 6 Interactive Charts, Metric Cards, Tabs
└──────────────────────────┘
```

### Q4: How does data become an interactive dashboard?
1. The raw JSON is validated into a structured `WeatherReport` containing `CurrentConditions`, `HourlyData`, `DailyData`, and `AirQualityData`.
2. Pure logic services compute derived insights:
   - `services/advisories.py` filters thresholds to flag heat, freeze, gale, or thunderstorm risks.
   - `services/suitability.py` calculates 0–100 suitability scores for 5 outdoor activities and locates optimal 3-hour daylight windows.
   - `services/briefing.py` generates natural-language text summaries for Today and Tomorrow.
3. The UI layer (`src/skydeck/ui/`) converts the structured data into Plotly interactive charts and HTML/CSS metric cards, organizing them across 6 dedicated tabs:
   - **Overview:** Hero card, current metrics, active advisories, 48h temp spline, conversational briefing.
   - **Forecast:** 16-day daily cards, precipitation probability vs volume, wind rose, thermal heatmap, and CSV export.
   - **Air Quality:** US AQI gauge, WHO pollutant breakdown, and health guidance.
   - **Activities:** 0–100 score cards with factor breakdown expanders.
   - **Compare:** Multi-location batch comparison ranked by selected activity.
   - **Diagnostics:** API call telemetry, cache hit ratio, and historical ERA5 climate baseline.

### Q5: What real-world challenges were encountered and how were they solved?
| Challenge | Root Cause | Engineering Solution |
|---|---|---|
| **API Parameter Drift** | Older documentation referenced legacy `weathercode`, newer endpoints expect `weather_code`. | Checked live Open-Meteo REST docs directly using Python network requests before writing domain models. |
| **Missing Data & Nulls** | Certain regional stations do not report visibility or pressure. | Pydantic models default missing values to `None`, and `format_value()` renders them safely as `"—"`, completely preventing fake zeros. |
| **Network Outages on Viva Day** | Campus Wi-Fi disconnects or firewall blocks can cause demo failures. | Built `DemoWeatherProvider` and a sidebar toggle for **Offline Demo Mode**, loading authentic pre-recorded datasets with zero network calls. |
| **Quota Limits** | Free tier is limited to 10,000 calls/day and 600/minute. | Implemented TTL caching, batch multi-city queries in a single HTTP call, and a real-time diagnostics telemetry tracker. |
| **Failed Refreshes Blanking Screen** | If internet drops while clicking Refresh, standard apps show an error and clear previous data. | Implemented stale-while-revalidate fallback: SkyDeck serves the cached data with an orange `"Stale Fallback (Offline)"` badge. |

### Q6: What would I add with an additional week of development?
1. **Forecast Accuracy Tracker:** Continuously record forecast predictions and compare them against actual observations 24 and 48 hours later to generate an empirical reliability score.
2. **Push Notifications & Official Warnings:** Integrate national meteorological alerts (e.g., Met Office / NOAA RSS CAP feeds) alongside the model-derived advisories.
3. **Geographic Radar Overlay:** Integrate PyDeck with Open-Meteo or RainViewer radar tile layers for real-time storm cell tracking.
4. **Cloud Deployment:** Containerize SkyDeck via Docker and deploy to Streamlit Community Cloud with GitHub Actions CI for automated linting, typing, and pytest verification.

---

## 2. Key Terminology Glossary

- **API (Application Programming Interface):** A standardized communication protocol enabling two computer programs to exchange structured data over a network.
- **REST (Representational State Transfer):** An architectural style for networked applications using standard HTTP verbs (`GET`, `POST`) and URL query parameters.
- **Endpoint:** A specific URL location where an API accepts requests to access a resource (e.g., `https://api.open-meteo.com/v1/forecast`).
- **JSON (JavaScript Object Notation):** A lightweight, human-readable data format structured in key-value pairs and arrays.
- **HTTP Status Code:** A 3-digit integer returned by a web server indicating request outcome (`200` = success, `404` = not found, `429` = rate limit exceeded, `500` = server error).
- **TTL (Time-To-Live):** The duration in seconds that cached data remains valid before being refreshed from the upstream API.
- **Geocoding:** The computational process of translating human city/address names into geographical coordinates (latitude and longitude).
- **Pydantic:** A Python data validation and parsing library that enforces type hints at runtime.
- **WMO Code (World Meteorological Organization):** An international standard mapping integer codes (0–99) to standardized weather descriptions.
- **ERA5 Reanalysis:** A global climate dataset produced by ECMWF combining model data with observations from across the world into a coherent historical dataset.

---

## 3. Module-by-Module Walkthrough Script (1–2 Minutes Per File)

### `config/settings.py`
> *"This file is the single configuration authority for the entire application. It implements the 'Config over constants' rule. Here we configure all Open-Meteo endpoints, cache time-to-lives (15 minutes for forecast, 24 hours for geocoding), HTTP timeouts (8 seconds), exponential retry settings, API call budget thresholds, and meteorological advisory triggers. If an instructor wants to change the heat advisory from 35°C to 30°C, we change one line here and zero logic files are touched."*

### `src/skydeck/core/http_client.py` & `errors.py`
> *"These modules implement our resilience layer. `ResilientHttpClient` is the single point responsible for every outgoing network call. It wraps Python `requests` with an exponential backoff retry loop for 5xx errors and timeouts up to 3 times. If Open-Meteo returns HTTP 429, it parses the `Retry-After` header to avoid spamming the server. Any network error is caught and converted into custom `SkyDeckError` types with human-friendly messages so users never see raw tracebacks."*

### `src/skydeck/core/cache.py`
> *"This is our thread-safe in-memory cache with stale fallback support. Each entry tracks its payload, creation timestamp, and TTL. If a user clicks Refresh while their internet is disconnected, the HTTP client fails, but `open_meteo.py` checks our cache with `allow_stale=True`. It immediately recovers the last good result and displays it with a clear 'Stale Fallback' status badge."*

### `src/skydeck/domain/units.py` & `weather_codes.py`
> *"These pure logic modules handle meteorological translations. `units.py` handles bidirectional conversions between Metric and Imperial systems for temperature, wind speed, precipitation, pressure, and visibility. Crucially, its `format_value()` function handles `None` values safely by outputting '—', preventing misleading zeros. `weather_codes.py` maps the 0–99 WMO codes to human descriptions, day/night emoji icons, and thunderstorm flags."*

### `src/skydeck/providers/demo_provider.py`
> *"This is our offline demonstration provider. It adheres to the `BaseWeatherProvider` interface and reads authentic, multi-day pre-recorded JSON responses directly from `sample_data/` for London, New York, Tokyo, and Paris. This guarantees that during an exam, viva, or disconnected grading scenario, the dashboard functions completely with zero network dependencies."*

### `src/skydeck/services/suitability.py`
> *"This is our activity recommendation engine. It takes weather data and computes a 0 to 100 score for Outdoor Sports, Commuting, Laundry, Travel, and Farming. The scoring uses weighted sub-factors for temperature comfort, wind tolerance, precipitation probability, and humidity. It features a critical safety override: if any thunderstorm code (95, 96, 99) occurs, the score is instantly forced to 0 ('Hazardous'). It also scans daytime hours to recommend the best 3-hour window."*

### `src/skydeck/services/advisories.py` & `briefing.py`
> *"`advisories.py` evaluates current and 24-hour forecast data against our config thresholds for extreme heat, freeze, gales, heavy rain, UV, thunderstorms, and poor AQI. It notes onset time, trigger values, and appends the mandatory model-derived disclaimer. `briefing.py` takes the forecast metrics and generates conversational, human-friendly narratives describing today and tomorrow's temperature peak, rain timing, and wind shifts."*

### `src/skydeck/ui/charts.py`
> *"Here we generate all 6 interactive Plotly visualizations: an hourly temperature spline with day/night shading, a combined precipitation probability bar and volume spline, a 16-day high/low temperature confidence band, a polar wind rose showing wind direction distribution, an air quality pollutant breakdown with the US AQI 100 threshold line, and an hour-by-day 24h thermal heatmap."*

### `app.py`
> *"Our application entry point. It is kept thin and declarative: it initializes Streamlit, injects the modern glassmorphic theme, manages sidebar controls (search with disambiguation, saved favorites, unit toggle, and the offline demo switch), and routes verified data into our layout tabs without containing any embedded business logic."*
