# SkyDeck — Campus Weather & Outdoor Activity Dashboard
## Project Overview, Architecture, APIs, and Implementation Details

---

## 1. Project Overview

**SkyDeck** is an interactive, enterprise-grade weather intelligence and outdoor activity planning dashboard built for university campuses and outdoor enthusiasts. Designed using **Python** and **Streamlit**, SkyDeck delivers real-time weather telemetry, 16-day extended forecasts, specialized outdoor activity suitability scoring, weather advisories, Plotly data visualizations, and multi-city comparative analytics.

The dashboard supports **dual operational modes**:
1. **Live Mode**: Fetches real-time weather, geocoding, air quality, and historical data from the **Open-Meteo REST APIs**.
2. **Offline Demo Mode**: Loads pre-recorded real API responses directly from local JSON datasets (`sample_data/`), allowing zero-network execution for disconnected grading, offline testing, and live demonstrations.

---

## 2. External APIs & Data Sources Used

SkyDeck relies on **Open-Meteo.com** (CC BY 4.0 license) for high-resolution meteorological data:

| API Endpoint | Base URL | Description & Parameters |
| :--- | :--- | :--- |
| **Geocoding API** | `https://geocoding-api.open-meteo.com/v1/search` | Resolves city names to coordinates (latitude, longitude, timezone, country, administrative region). |
| **Forecast API** | `https://api.open-meteo.com/v1/forecast` | Fetches current conditions, 48-hour hourly variables, and 16-day daily forecast breakdowns. |
| **Air Quality API** | `https://air-quality-api.open-meteo.com/v1/air-quality` | Models PM2.5, PM10, Nitrogen Dioxide ($NO_2$), Ozone ($O_3$), and European Air Quality Index (AQI). |
| **Historical Archive API**| `https://archive-api.open-meteo.com/v1/archive` | Historical climate data for multi-year trends and comparative benchmarks. |

### API Response Resiliency & Caching Strategy
- **Resilient HTTP Client** (`ResilientHttpClient`): Handles transient network errors, rate limits (HTTP 429), and server outages (HTTP 5xx) with exponential backoff and retry mechanisms.
- **TTL Caching System** (`SkyDeckCache`):
  - **Geocoding queries**: Cached for 24 hours.
  - **Forecast telemetry**: Cached for 15 minutes.
  - **Air Quality telemetry**: Cached for 30 minutes.
  - **Stale-Fallback Mechanism**: If network requests fail, the application gracefully serves stale cached data with an explicit UI indicator rather than crashing.

---

## 3. System Architecture & Modular Design

The codebase follows clean software architecture principles, strictly separating business logic and domain scoring from UI rendering side effects:

```
weather Dashboard/
├── app.py                      # Main application entry point & router
├── config/                     # Configuration constants & settings
│   └── settings.py
├── src/skydeck/
│   ├── core/                   # Infrastructure: HTTP client, cache, diagnostics, errors
│   │   ├── cache.py
│   │   ├── diagnostics.py
│   │   ├── errors.py
│   │   └── http_client.py
│   ├── domain/                 # Core domain models & pure unit conversions
│   │   ├── models.py           # Pydantic data schemas
│   │   ├── units.py            # Imperial/Metric conversions & formatting
│   │   └── weather_codes.py    # WMO code descriptions & icons
│   ├── providers/              # Data access layer (Live Open-Meteo & Offline Demo)
│   │   ├── base.py             # Abstract BaseWeatherProvider interface
│   │   ├── open_meteo.py       # Live Open-Meteo API provider
│   │   └── demo_provider.py     # Local JSON offline provider
│   ├── services/               # Pure functional business engines
│   │   ├── advisories.py       # Weather alert & safety advisory engine
│   │   ├── briefing.py         # AI-style natural language briefing generator
│   │   ├── compare.py          # Multi-city ranking & suitability matrix
│   │   └── suitability.py      # Outdoor activity scoring engine
│   ├── storage/                # Persistence layer for saved quick cities
│   │   └── saved_cities.py
│   └── ui/                     # Presentation layer (Theme, Components, Charts, Tabs)
│       ├── charts.py           # Plotly visualization generators
│       ├── components.py       # Reusable glassmorphic UI cards & metrics
│       ├── tabs.py             # Tab page renderers
│       └── theme.py            # Dark glassmorphic CSS design system
└── tests/                      # Automated unit, contract, static, and UI render tests
```

---

## 4. Key Features & How They Were Implemented

### A. Outdoor Activity Suitability Engine (`suitability.py`)
Calculates mathematical suitability scores ($0$ to $100$) and ratings (*Excellent, Good, Moderate, Marginal, Poor, Hazardous*) for 6 campus activity types:
1. **Walking & Campus Commute**
2. **Outdoor Sports & Recreation**
3. **Running & Jogging**
4. **Outdoor Photography**
5. **GIS & Environmental Field Work**
6. **Cycling & Micro-Mobility**

- **Penalty-based scoring**: Evaluates temperature comfort bands, wind speed thresholds, precipitation intensity, and humidity.
- **Safety Blocks**: Immediately sets score to $0$ ("Hazardous") if severe weather codes (e.g., thunderstorms, heavy rain, extreme wind, freezing rain) are active.

### B. Severe Weather Advisory System (`advisories.py`)
Monitors real-time and hourly telemetry against critical meteorological thresholds to generate alert cards:
- **Heat Advisory**: Temperatures exceeding $35^\circ\text{C}$ ($95^\circ\text{F}$).
- **Thunderstorm & Lightning Warning**: WMO codes $95, 96, 99$.
- **High Wind Warning**: Sustained winds above $40\text{ km/h}$ or gusts exceeding threshold.
- **Rain & Snow Advisories**: Active precipitation rates above $2.5\text{ mm/h}$.

### C. Multi-City Management & Comparison (`compare.py` & `saved_cities.py`)
- **JSON File Persistence**: Manages quick-access saved cities in `saved_cities.json`.
- **Deduplication Guard**: Prevents adding duplicate locations based on coordinate proximity.
- **City Limit Enforcement**: Enforces a maximum limit of saved cities and prevents removing the last city.
- **Comparative Ranking**: Ranks saved cities side-by-side using Plotly comparative bar charts.

### D. Units System (`units.py`)
Allows instant zero-reload toggle between:
- **Metric**: Celsius ($^\circ\text{C}$), Kilometers per hour ($\text{km/h}$), Millimeters ($\text{mm}$), Hectopascals ($\text{hPa}$).
- **Imperial**: Fahrenheit ($^\circ\text{F}$), Miles per hour ($\text{mph}$), Inches ($\text{in}$), Inches of Mercury ($\text{inHg}$).

---

## 5. UI & Interactive Visualizations

SkyDeck features a custom **Dark Glassmorphic UI Theme** with vibrant accents, responsive cards, micro-animations, and 6 specialized tab views:

1. **🏠 Home Page**:
   - Top header strip with date/time and live data freshness badge.
   - Hero banner with greeting, overall activity rating, and student weather tip.
   - Current conditions grid & outdoor activity recommendation pills.
   - 5-Day forecast cards, temperature trend spline, rain probability donut chart, and active weather alerts.
2. **🌤️ Weather Page**:
   - Detailed meteorological metrics (Feels-like, humidity, dew point, pressure, visibility, UV index).
   - 48-Hour temperature & feels-like spline chart.
   - Detailed natural language morning/afternoon/evening briefings.
3. **📅 5-Day & Extended Forecast Page**:
   - Interactive sliders to toggle hourly window ($24\text{h}$ to $168\text{h}$) and daily window ($7$ to $16$ days).
   - Daily temperature bands chart and precipitation breakdown.
   - **One-click CSV Data Export** for hourly and daily forecast datasets.
4. **🎯 Activity Guide Page**:
   - Complete suitability breakdown, factor scores, limiting weather parameters, and daylight suitability windows.
5. **📊 Interactive Visualizations Page**:
   - **Hourly Spline Chart**: Smooth temperature & feels-like curves.
   - **Precipitation Chart**: Dual-axis bar and line chart for rainfall volume and rain probability.
   - **Wind Rose / Polar Chart**: Wind speed distribution across cardinal directions.
   - **Air Quality Profile**: Multi-pollutant line chart ($PM2.5$, $PM10$, $NO_2$, $O_3$).
   - **Thermal Heatmap**: Hourly vs. daily temperature intensity matrix.
6. **⚙️ Settings & Diagnostics Page**:
   - Multi-city suitability matrix and comparative ranking.
   - Saved cities management (add, switch, delete).
   - Real-time diagnostic metrics (API hit counts, cache hit ratio, average response latency).

---

## 6. Testing & Quality Assurance

The codebase includes an extensive **74-test automated test suite** in `tests/`:

- **Static AST & Import Verification** (`test_static_analysis.py`): Parses all codebase files ensuring zero syntax errors, zero missing imports, and zero undefined symbols (`pyflakes .`).
- **Render-Every-Page Test Suite** (`test_render_pages.py`): Opens every tab page across **Live Mode**, **Demo Mode**, **Metric System**, and **Imperial System** ($6 \text{ pages} \times 2 \text{ modes} \times 2 \text{ unit systems} = 24 \text{ test combinations}$).
- **Unit & Contract Tests**: Covers domain unit conversions, weather code mappings, Pydantic model contract safety, advisory logic, suitability rules, search behavior, and storage file integrity.

---

## 7. How to Run the Project

### Prerequisites
- Python 3.10+
- Streamlit, Pandas, Plotly, Pydantic, Pytest

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit dashboard
streamlit run app.py
```

### Running Tests & Static Checks
```bash
# Run full automated test suite
pytest -v

# Run static linting check
python -m pyflakes .
```
