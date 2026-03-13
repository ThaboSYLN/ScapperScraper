import logging
from typing import List
from app.sofascore.session import BASE_URL, safe_get
from app.sofascore.cache import cache, TTL_SPORTS

logger = logging.getLogger(__name__)

# Canonical sport slugs as recognised by SofaScore
SUPPORTED_SPORTS = [
    {"id": 1,  "name": "Football",         "slug": "football"},
    {"id": 2,  "name": "Rugby",            "slug": "rugby"},
    {"id": 3,  "name": "Cricket",          "slug": "cricket"},
    {"id": 4,  "name": "Basketball",       "slug": "basketball"},
    {"id": 5,  "name": "Tennis",           "slug": "tennis"},
    {"id": 6,  "name": "Table Tennis",     "slug": "table-tennis"},
    {"id": 7,  "name": "Ice Hockey",       "slug": "ice-hockey"},
    {"id": 8,  "name": "Baseball",         "slug": "baseball"},
    {"id": 9,  "name": "Motorsport",       "slug": "motorsport"},
    {"id": 10, "name": "MMA",              "slug": "mma"},
    {"id": 11, "name": "Darts",            "slug": "darts"},
    {"id": 12, "name": "American Football","slug": "american-football"},
    {"id": 13, "name": "Esports",          "slug": "esports"},
    {"id": 14, "name": "Volleyball",       "slug": "volleyball"},
    {"id": 15, "name": "Futsal",           "slug": "futsal"},
    {"id": 16, "name": "Handball",         "slug": "handball"},
    {"id": 17, "name": "Badminton",        "slug": "badminton"},
    {"id": 18, "name": "Water Polo",       "slug": "water-polo"},
    {"id": 19, "name": "Aussie Rules",     "slug": "aussie-rules"},
    {"id": 20, "name": "Snooker",          "slug": "snooker"},
    {"id": 21, "name": "Beach Volleyball", "slug": "beach-volleyball"},
    {"id": 22, "name": "Floorball",        "slug": "floorball"},
    {"id": 23, "name": "Cycling",          "slug": "cycling"},
    {"id": 24, "name": "Bandy",            "slug": "bandy"},
    {"id": 25, "name": "Minifootball",     "slug": "minifootball"},
]


def get_all_sports() -> List[dict]:
    """Return the master list of supported sports."""
    cache_key = "sports:all"
    cached = cache.get(cache_key)
    if cached:
        return cached

    cache.set(cache_key, SUPPORTED_SPORTS, ttl_seconds=TTL_SPORTS)
    return SUPPORTED_SPORTS


def get_sport_by_slug(slug: str) -> dict | None:
    """Look up a sport by its slug."""
    return next((s for s in SUPPORTED_SPORTS if s["slug"] == slug), None)


def get_live_counts() -> dict:
    """
    Fetch live event counts per sport.
    Useful for the frontend to highlight which sports have active matches.
    """
    cache_key = "sports:live_counts"
    cached = cache.get(cache_key)
    if cached:
        return cached

    counts = {}
    for sport in SUPPORTED_SPORTS:
        url = f"{BASE_URL}/sport/{sport['slug']}/events/live"
        data = safe_get(url)
        if data:
            events = data.get("events", [])
            counts[sport["slug"]] = len(events)
        else:
            counts[sport["slug"]] = 0

    cache.set(cache_key, counts, ttl_seconds=60)
    return counts