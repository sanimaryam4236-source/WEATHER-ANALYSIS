"""
SkyDeck Design System & Custom CSS Styling.

Implements modern typography, subtle glassmorphic surfaces, curated color tokens,
and dark theme compatibility tailored for the Campus Weather & Outdoor Activity Dashboard mockup.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Force dark theme root variables */
:root {
    --sky-bg-dark:        #0B132B;
    --sky-card-bg:        rgba(17, 24, 39, 0.85);
    --sky-card-border:    #1E293B;
    --sky-text-primary:   #F8FAFC;
    --sky-text-secondary: #CBD5E1;
    --sky-text-muted:     #94A3B8;
    --sky-accent-blue:    #38BDF8;
    --sky-accent-green:   #22C55E;
    --sky-accent-amber:   #F59E0B;
    --sky-accent-red:     #EF4444;
}

.stApp {
    background-color: #0B132B;
    color: #F8FAFC;
}

/* Custom scrollbars */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: #0B132B;
}
::-webkit-scrollbar-thumb {
    background: #1E293B;
    border-radius: 4px;
}

/* Glassmorphism card surfaces */
.mockup-card {
    background: rgba(17, 24, 39, 0.85);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid #1E293B;
    border-radius: 16px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.35);
}

/* Hero card styling */
.hero-banner {
    background: linear-gradient(135deg, #061838 0%, #0D2B52 50%, #0F3A66 100%);
    border: 1px solid #1E3A8A;
    border-radius: 20px;
    padding: 1.75rem 2rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 12px 36px 0 rgba(0, 0, 0, 0.45);
}

/* Rating Badges / Pills */
.pill-excellent {
    background: rgba(34, 197, 94, 0.2);
    color: #4ADE80;
    border: 1px solid rgba(34, 197, 94, 0.4);
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-weight: 700;
    font-size: 0.82rem;
    display: inline-block;
}

.pill-good {
    background: rgba(16, 185, 129, 0.2);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.4);
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-weight: 700;
    font-size: 0.82rem;
    display: inline-block;
}

.pill-moderate {
    background: rgba(245, 158, 11, 0.2);
    color: #FBBF24;
    border: 1px solid rgba(245, 158, 11, 0.4);
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-weight: 700;
    font-size: 0.82rem;
    display: inline-block;
}

.pill-poor {
    background: rgba(239, 68, 68, 0.2);
    color: #F87171;
    border: 1px solid rgba(239, 68, 68, 0.4);
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-weight: 700;
    font-size: 0.82rem;
    display: inline-block;
}

/* Student Tip strip */
.student-tip-box {
    background: linear-gradient(90deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 182, 212, 0.1) 100%);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    margin-top: 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* Recommendation bar */
.recommendation-bar {
    background: linear-gradient(90deg, rgba(6, 78, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid rgba(34, 197, 94, 0.3);
    border-radius: 16px;
    padding: 1.1rem 1.5rem;
    margin-top: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* Sidebar navigation buttons custom styling */
.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    transition: all 0.2s ease;
}

/* Make stRadio look sleek in sidebar */
div[data-testid="stSidebar"] div[role="radiogroup"] > label {
    padding: 0.5rem 0.75rem;
    border-radius: 8px;
    margin-bottom: 0.2rem;
}
</style>
"""


def apply_theme():
    """Inject safe CSS into Streamlit page."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
