# SkyDeck — Weather Intelligence Dashboard ⛅

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Tests](https://img.shields.io/badge/pytest-25%20passed-brightgreen.svg)]()

**SkyDeck** is an interactive, production-grade meteorological intelligence dashboard built in Python and Streamlit. It delivers hyper-local current observations, high-resolution 16-day forecasts, atmospheric air quality telemetry, rule-based safety advisories, and outdoor activity suitability analytics powered by Open-Meteo APIs.

---

## ⚡ 5-Minute Quickstart

### 1. Prerequisites
Ensure you have Python 3.10+ installed on your computer.

### 2. Clone / Open Directory
```bash
cd "weather Dashboard"
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch the Dashboard
```bash
streamlit run app.py
```
Your browser will open automatically at `http://localhost:8501`.

### 5. Run the Automated Test Suite
```bash
pytest -v
```
All 25 unit, contract, failure, and UI smoke tests will execute in under 3 seconds.

---

## 🌟 Key Features

1. **Precision Geocoding & Disambiguation:** Instant search for global cities with multi-match disambiguation (e.g. *London, UK* vs *London, Canada*).
2. **Current Observations & Hero Card:** Large temperature, condition icons (day/night aware), feels-like index, wind speed/direction, barometric pressure, cloud cover, and UV index.
3. **16-Day & 48-Hour Forecasts:** Selectable forecast windows with daily metric cards and CSV data exports.
4. **6 Interactive Visualizations (Plotly):**
   - 📈 **Hourly Temperature Spline** with automated day/night background shading.
   - 🌧️ **Precipitation Analysis:** Probability (%) bars + volume accumulation line.
   - 🌡️ **Temperature Range Band:** Multi-day high/low confidence area.
   - 🧭 **Polar Wind Rose:** Wind direction distribution and speed intensity.
   - 🍃 **Atmospheric Pollutants & US AQI:** PM2.5, PM10, O₃, NO₂ vs health danger thresholds.
   - 🔥 **Hour-by-Day 24h Heatmap:** Thermal profile across up to 7 days.
5. **Rule-Based Meteorological Advisories:** Flags extreme heat, freeze, gales, heavy precipitation, high UV, thunderstorms, and unhealthy air quality with onset times and mandatory model-derived disclaimers.
6. **Activity Suitability Scoring (0–100):** Algorithmic suitability scoring for *Outdoor Sports*, *Daily Commute*, *Outdoor Clothes Drying (Laundry)*, *Sightseeing Travel*, and *Farming/Field Spraying*, with best 3-hour daylight windows and factor breakdowns (thunderstorms strictly force score to 0).
7. **Multi-Location Benchmark:** Batch query up to 5 cities in a single network call to compare and rank by outdoor activity suitability.
8. **Dual-Mode Reliability Layer:**
   - **🟢 Live API Mode:** Live calls to Open-Meteo with exponential backoff retries and rate limit handling.
   - **🟣 Offline Demo Mode:** Zero-network safety net loading rich pre-recorded datasets for London, New York, Tokyo, and Paris.
   - **🟠 Stale Fallback:** Failed refreshes preserve last good data with an offline warning badge instead of a blank screen.

---

## 🏛️ Project Structure

```
weather Dashboard/
├── app.py                      # Thin application entry point
├── requirements.txt            # Pinned dependencies
├── config/
│   ├── __init__.py
│   └── settings.py             # Config over constants (URLs, thresholds, TTLs, weights)
├── src/skydeck/
│   ├── core/                   # Networking, caching, errors, telemetry
│   │   ├── errors.py           # Custom friendly exception hierarchy
│   │   ├── http_client.py      # Resilient HTTP client with retry & backoff
│   │   ├── cache.py            # Stale-while-revalidate TTL cache
│   │   └── diagnostics.py      # Quota usage and latency tracking
│   ├── domain/                 # Type models & meteorological tables
│   │   ├── models.py           # Pydantic schemas (null-safe)
│   │   ├── units.py            # Metric <-> Imperial conversion utilities
│   │   └── weather_codes.py    # WMO code interpretation & icons
│   ├── providers/              # Data ingestion providers
│   │   ├── base.py             # BaseWeatherProvider abstract interface
│   │   ├── open_meteo.py       # Live REST API implementation
│   │   └── demo_provider.py    # Zero-network offline demo provider
│   ├── services/               # Pure business logic (zero I/O, zero UI)
│   │   ├── advisories.py       # Meteorological advisory detector
│   │   ├── suitability.py      # 0-100 activity suitability engine
│   │   ├── briefing.py         # Conversational briefing generator
│   │   └── compare.py          # Multi-city comparison & ranking
│   ├── storage/
│   │   └── saved_cities.py     # Bookmark storage & last active session
│   └── ui/                     # Presentation layer
│       ├── theme.py            # Glassmorphic CSS design system
│       ├── components.py       # Reusable UI widgets & metric cards
│       ├── charts.py           # 6 Plotly visualization builders
│       └── tabs.py             # Dashboard tab layout views
├── sample_data/                # Real offline JSON responses
├── tests/                      # 25 automated pytest tests
└── docs/                       # Project documentation
    ├── STUDENT_EXPLAINER.md    # Viva questions, glossary, walkthrough scripts
    ├── DECISION_LOG.md         # Architectural Decision Records (ADRs)
    └── ARCHITECTURE.md         # Architectural design & data-flow diagrams
```

---

## ⚖️ Attribution & Compliance
Weather data provided by [Open-Meteo.com](https://open-meteo.com/) under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license.
Modelled atmospheric air quality data provided by Copernicus Atmosphere Monitoring Service (CAMS) / Open-Meteo.
Historical climate context powered by ECMWF ERA5 reanalysis.
This software is developed strictly for educational and non-commercial purposes.
