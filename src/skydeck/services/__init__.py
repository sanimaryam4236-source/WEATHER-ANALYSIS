"""SkyDeck services layer for business logic: advisories, suitability, briefings, comparisons."""
from src.skydeck.services.advisories import evaluate_advisories
from src.skydeck.services.suitability import calculate_suitability, score_single_activity
from src.skydeck.services.briefing import generate_briefings, generate_daily_briefing
from src.skydeck.services.compare import compare_and_rank_cities

__all__ = [
    "evaluate_advisories",
    "calculate_suitability",
    "score_single_activity",
    "generate_briefings",
    "generate_daily_briefing",
    "compare_and_rank_cities",
]

