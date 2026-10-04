# SkyDeck — Architectural Decision Log (ADR)

This document records the key architectural choices, library selections, and design tradeoffs made during the development of SkyDeck.

---

## ADR 01: Layered Architecture with Strict Dependency Direction
- **Context:** The implementation plan requires pure logic functions that can be tested in isolation and explained simply by the student during evaluation.
- **Decision:** Adopt a strict 5-layer dependency hierarchy:
  `UI` $\rightarrow$ `Services` & `Storage` $\rightarrow$ `Domain` $\rightarrow$ `Providers` $\rightarrow$ `Core` $\leftarrow$ `Config`
- **Rule:** Lower layers never import higher layers. Logic in `services/` contains zero network calls (`requests`) and zero UI calls (`streamlit`).
- **Consequence:** 100% of business logic (suitability scoring, advisory detection, text briefing) is unit-testable without mocking network or web servers.

---

## ADR 02: Pydantic Domain Schemas for Contract Safety & Null Resilience
- **Context:** External API responses from meteorological services occasionally omit fields or introduce subtle name changes (e.g., legacy `weathercode` vs modern `weather_code`). Unhandled nulls could result in raw Python tracebacks or false zero readings.
- **Decision:** Use Pydantic v2 `BaseModel` for all transfer objects (`GeocodedLocation`, `CurrentConditions`, `HourlyData`, `DailyData`, `AirQualityData`, `WeatherReport`). Missing numeric fields explicitly default to `None` and are formatted as `"—"`, never `0.0`.
- **Consequence:** Strict typing prevents runtime crashes; contract tests on real JSON payloads catch API drift before deployment.

---

## ADR 03: Dual-Mode Provider Strategy (Live Open-Meteo + Zero-Network Demo)
- **Context:** In a viva or live classroom demonstration, network outages, campus firewall blocks, or captive portals can cause live API calls to fail.
- **Decision:** Implement `BaseWeatherProvider` interface with two interchangeable implementations:
  1. `OpenMeteoProvider`: Live REST client with exponential backoff, rate limit handling, and stale cache fallback.
  2. `DemoWeatherProvider`: Completely offline playback engine reading pre-saved real payloads in `sample_data/` for London, New York, Tokyo, and Paris.
- **Consequence:** The student can toggle "Offline Demo Mode" in the sidebar with a single click, guaranteeing a flawless presentation even with Wi-Fi turned off.

---

## ADR 04: Stale-While-Revalidate Caching & Resilient Fallback
- **Context:** Open-Meteo free tier has burst rate limits (600 calls/min) and occasional transient network delays. A failed refresh should never clear a previously rendered screen.
- **Decision:** Implement `SkyDeckCache` with stale fallback support. When a network call times out or throws an error, the provider checks for an expired cached entry. If present, it serves the last known good data accompanied by an explicit `"🟠 Stale Fallback (Offline)"` badge.
- **Consequence:** Eliminates white-screen crashes on failed refreshes.

---

## ADR 05: Multi-Location Single-Batch Requests for City Comparison
- **Context:** Comparing multiple cities could quickly exhaust the API call quota if done sequentially.
- **Decision:** Utilize Open-Meteo's multi-location capability (passing lists of latitudes and longitudes) to retrieve weather data for up to 5 cities in a single HTTP request.
- **Consequence:** API consumption is cut by 80% for the comparison tab.

---

## ADR 06: Plotly for Dynamic, Hardware-Accelerated Visualizations
- **Context:** The dashboard requires 6 distinct visualizations (hourly temperature spline with day/night shading, precipitation probability bars + rain volume line, daily range confidence band, polar wind rose, air quality pollutant bars, and an hour-by-day 24h heatmap).
- **Decision:** Use `plotly.graph_objects` with unified hover modes and transparent backgrounds.
- **Consequence:** Rich interactivity, tooltip inspection, and mobile responsiveness without heavy external dependencies.

---

## ADR 07: Campus Weather Dashboard Redesign & Multi-City State Machine
- **Context:** UI required a modern dark navy redesign matching the campus weather & outdoor activity mockup, Pakistani default cities (Islamabad, Lahore, Karachi, Rawalpindi, Peshawar), and a rock-solid search city state machine.
- **Decision:**
  1. Enforce dark base theme via `.streamlit/config.toml` and custom glassmorphic CSS tokens (`theme.py`).
  2. Implement `SavedCitiesManager` with coordinate duplicate detection (~0.05° radius), active city index shift safety, maximum 8 city limit, minimum 1 city protection, and corrupt file fallback.
  3. Search state machine in sidebar preserving search results in session state with dropdown match picker and "Add to My Cities" button.
  4. Mandatory render-every-page test suite (`test_render_pages.py`) verifying zero exceptions across all pages, unit systems, and offline/live modes.
- **Consequence:** Visual parity with design target, zero white-screen crashes, fully functional multi-city management and reliable city search.

