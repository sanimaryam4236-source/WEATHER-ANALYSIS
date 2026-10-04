"""
SkyDeck — Campus Weather & Outdoor Activity Dashboard.

Main application entry point:
- Sets up Streamlit layout and dark glassmorphic styling.
- Renders sidebar navigation (Home, Weather, 5-Day Forecast, Activity Guide, Graphs, Settings).
- Manages Quick Cities list and reliable Search City state machine.
- Delegates layout rendering to modular UI components and tabs.
- Catches all errors gracefully for production safety.
"""

import streamlit as st

from config.settings import APP_NAME
from src.skydeck.core.errors import SkyDeckError, LocationNotFoundError
from src.skydeck.domain.models import GeocodedLocation, WeatherReport
from src.skydeck.domain.units import UnitSystem
from src.skydeck.providers.open_meteo import OpenMeteoProvider
from src.skydeck.providers.demo_provider import DemoWeatherProvider
from src.skydeck.storage.saved_cities import saved_cities_storage
from src.skydeck.ui.theme import apply_theme
from src.skydeck.ui.tabs import (
    render_home_page,
    render_weather_page,
    render_forecast_page,
    render_activity_guide_page,
    render_graphs_page,
    render_settings_and_cities_page,
)

# -----------------------------------------------------------------------------
# Page Configuration & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title=f"{APP_NAME} — Campus Weather & Outdoor Activity Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()


# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "unit_system" not in st.session_state:
    st.session_state.unit_system = UnitSystem.METRIC

if "offline_mode" not in st.session_state:
    st.session_state.offline_mode = False

if "active_location" not in st.session_state:
    last_saved = saved_cities_storage.get_last_active_city()
    st.session_state.active_location = GeocodedLocation(**last_saved)

if "search_results" not in st.session_state:
    st.session_state.search_results = []

if "search_msg" not in st.session_state:
    st.session_state.search_msg = ""

if "nav_selection" not in st.session_state:
    st.session_state.nav_selection = "Home"

if "cached_report" not in st.session_state:
    st.session_state.cached_report = None


# -----------------------------------------------------------------------------
# Providers Setup
# -----------------------------------------------------------------------------
live_provider = OpenMeteoProvider()
demo_provider = DemoWeatherProvider()
provider = demo_provider if st.session_state.offline_mode else live_provider


# -----------------------------------------------------------------------------
# Sidebar Navigation & Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    # 1. Logo & App Title
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; margin-bottom: 1.25rem;">
            <span style="font-size: 2.2rem; margin-right: 0.6rem; color: #F59E0B;">🎓</span>
            <div>
                <h2 style="margin: 0; font-size: 1.5rem; font-weight: 800; color: #F8FAFC;">{APP_NAME}</h2>
                <div style="font-size: 0.78rem; color: #94A3B8;">Campus Weather Intelligence</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Main Navigation Menu
    nav_options = [
        "🏠 Home",
        "🌤️ Weather",
        "📅 5-Day Forecast",
        "🎯 Activity Guide",
        "📊 Graphs",
        "⚙️ Settings",
    ]

    selected_nav = st.radio(
        "Navigation",
        options=nav_options,
        index=0,
        label_visibility="collapsed",
    )
    # Strip icon to get route key
    nav_key = selected_nav.split(" ", 1)[1] if " " in selected_nav else selected_nav
    st.session_state.nav_selection = nav_key

    st.markdown("---")

    # 3. Quick Cities Section
    st.markdown("##### 📍 Quick Cities")
    saved_list = saved_cities_storage.get_saved_cities()

    current_active_id = st.session_state.active_location.id
    current_active_name = st.session_state.active_location.name

    for c in saved_list:
        is_active = (c.get("id") == current_active_id) or (c.get("name") == current_active_name)
        c_name = c.get("name")

        col_city_btn, col_city_del = st.columns([5, 1])

        with col_city_btn:
            btn_style = "primary" if is_active else "secondary"
            btn_label = f"📍 {c_name}" if is_active else c_name
            if st.button(btn_label, key=f"quick_{c_name}_{c.get('id', 0)}", type=btn_style, use_container_width=True):
                st.session_state.active_location = GeocodedLocation(**c)
                st.session_state.cached_report = None
                saved_cities_storage.set_last_active_city(c)
                st.rerun()

        with col_city_del:
            if len(saved_list) > 1:
                if st.button("✕", key=f"quick_del_{c_name}_{c.get('id', 0)}", help=f"Remove {c_name}"):
                    ok, msg, next_active = saved_cities_storage.remove_saved_city(c)
                    if ok and next_active:
                        st.session_state.active_location = GeocodedLocation(**next_active)
                    st.session_state.cached_report = None
                    st.rerun()
            else:
                st.caption("🔒")

    st.markdown("---")

    # 4. Search & Add City State Machine
    st.markdown("##### 🔍 Search & Add City")

    with st.form(key="city_search_form", clear_on_submit=False):
        search_input = st.text_input(
            "Search city name:",
            placeholder="e.g. Islamabad, London, Tokyo...",
            label_visibility="collapsed",
        )
        search_submitted = st.form_submit_button("🔍 Search City", use_container_width=True)

    if search_submitted and search_input:
        query_clean = search_input.strip()
        if len(query_clean) < 3:
            st.warning("⚠️ Enter at least 3 characters to search.")
            st.session_state.search_results = []
        else:
            try:
                with st.spinner(f"Searching for '{query_clean}'..."):
                    results = provider.search_locations(query_clean, count=5)
                    st.session_state.search_results = results
                    st.session_state.search_msg = f"Found {len(results)} match(es)."
            except LocationNotFoundError as e:
                st.warning(e.to_user_message())
                st.session_state.search_results = []
            except SkyDeckError as e:
                st.error(e.to_user_message())
                st.session_state.search_results = []

    # Display dropdown of matches if search results exist
    if st.session_state.search_results:
        options = {
            f"{loc.name}, {loc.admin1 or ''} ({loc.country or ''})": loc
            for loc in st.session_state.search_results
        }
        selected_match_label = st.selectbox(
            "Select Match to Add:",
            options=list(options.keys()),
            key="search_matches_dropdown",
        )
        if st.button("➕ Add to My Cities", type="primary", use_container_width=True):
            chosen_loc = options[selected_match_label]
            ok, msg = saved_cities_storage.add_saved_city(chosen_loc.model_dump())
            if ok:
                st.session_state.active_location = chosen_loc
                st.session_state.cached_report = None
                st.session_state.search_results = []
                st.success(msg)
                st.rerun()
            else:
                st.warning(msg)

    st.markdown("---")

    # 5. Units & Offline Demo Settings
    st.markdown("##### ⚙️ Quick Settings")

    # Units Radio
    _unit_labels = {
        UnitSystem.METRIC: "🌡️ Metric (°C, km/h, mm)",
        UnitSystem.IMPERIAL: "🗽 Imperial (°F, mph, in)",
    }
    unit_choice = st.radio(
        "Units:",
        options=[UnitSystem.METRIC, UnitSystem.IMPERIAL],
        index=0 if st.session_state.unit_system == UnitSystem.METRIC else 1,
        format_func=lambda u: _unit_labels[u],
        label_visibility="collapsed",
    )
    if unit_choice != st.session_state.unit_system:
        st.session_state.unit_system = unit_choice
        st.rerun()

    # Offline Demo Toggle
    demo_toggle = st.toggle(
        "Offline Demo Mode",
        value=st.session_state.offline_mode,
        help="Loads pre-saved real API snapshots from sample_data for zero-network execution.",
    )
    if demo_toggle != st.session_state.offline_mode:
        st.session_state.offline_mode = demo_toggle
        st.session_state.cached_report = None
        st.rerun()

    st.caption("Weather telemetry powered by Open-Meteo.com (CC BY 4.0).")


# -----------------------------------------------------------------------------
# Data Ingestion Pipeline
# -----------------------------------------------------------------------------
report: WeatherReport = None

try:
    if st.session_state.cached_report is None:
        with st.spinner(f"Fetching forecast for {st.session_state.active_location.name}..."):
            report = provider.get_forecast(st.session_state.active_location, forecast_days=16)
            st.session_state.cached_report = report
    else:
        report = st.session_state.cached_report

except SkyDeckError as err:
    st.error(err.to_user_message())
    st.info("💡 Try enabling **Offline Demo Mode** in the sidebar to browse verified sample cities without network access.")
    st.stop()
except Exception as unhandled_err:
    st.error(
        f"⚠️ An unexpected issue occurred while preparing the forecast: {str(unhandled_err)}. "
        "Please check your input or switch to Offline Demo mode."
    )
    st.stop()


# -----------------------------------------------------------------------------
# Main Navigation View Dispatcher
# -----------------------------------------------------------------------------
route = st.session_state.nav_selection

if route == "Home":
    render_home_page(report, st.session_state.unit_system, provider)
elif route == "Weather":
    render_weather_page(report, st.session_state.unit_system)
elif route == "5-Day Forecast":
    render_forecast_page(report, st.session_state.unit_system)
elif route == "Activity Guide":
    render_activity_guide_page(report)
elif route == "Graphs":
    render_graphs_page(report, st.session_state.unit_system)
elif route == "Settings":
    render_settings_and_cities_page(provider, report)
else:
    render_home_page(report, st.session_state.unit_system, provider)
