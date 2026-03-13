import logging
from typing import List, Optional
from app.sofascore.session import BASE_URL, safe_get
from app.sofascore.cache import cache, TTL_TOURNAMENTS

logger = logging.getLogger(__name__)


def get_tournaments(category_id: int) -> Optional[List[dict]]:
    """
    Fetch all tournaments (leagues) within a category (country).
    e.g., England → [Premier League, Championship, League One, ...]
    """
    cache_key = f"tournaments:{category_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{BASE_URL}/category/{category_id}/tournaments"
    data = safe_get(url)

    if not data:
        logger.warning(f"No data returned for category_id: {category_id}")
        return None

    raw_tournaments = data.get("groups", [])

    # SofaScore sometimes nests tournaments inside groups
    tournaments = []
    for group in raw_tournaments:
        for t in group.get("uniqueTournaments", []):
            tournaments.append(_shape_tournament(t, category_id))

    # Fallback: flat tournaments list (some sports use this)
    if not tournaments:
        flat = data.get("uniqueTournaments", [])
        tournaments = [_shape_tournament(t, category_id) for t in flat]

    logger.info(f"Fetched {len(tournaments)} tournaments for category: {category_id}")
    cache.set(cache_key, tournaments, ttl_seconds=TTL_TOURNAMENTS)
    return tournaments


def _shape_tournament(t: dict, category_id: int) -> dict:
    """Normalize a tournament object into a clean shape."""
    return {
        "id": t.get("id"),
        "name": t.get("name"),
        "slug": t.get("slug"),
        "category_id": category_id,
        "has_live_events": t.get("hasEventPlayerStatistics", False),
        "logo": f"https://api.sofascore.com/api/v1/unique-tournament/{t.get('id')}/image/dark",
        "primary_color": t.get("primaryColorHex", "#000000"),
        "secondary_color": t.get("secondaryColorHex", "#FFFFFF"),
    }