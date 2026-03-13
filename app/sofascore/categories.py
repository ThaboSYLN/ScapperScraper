import logging
from typing import List, Optional
from app.sofascore.session import BASE_URL, safe_get
from app.sofascore.cache import cache, TTL_CATEGORIES

logger = logging.getLogger(__name__)


def get_categories(sport_slug: str) -> Optional[List[dict]]:
    """
    Fetch all categories (countries/regions) for a sport.
    e.g., Football → [England, Spain, Germany, ...]
    """
    cache_key = f"categories:{sport_slug}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{BASE_URL}/sport/{sport_slug}/categories"
    data = safe_get(url)

    if not data:
        logger.warning(f"No data returned for categories of sport: {sport_slug}")
        return None

    raw_categories = data.get("categories", [])

    categories = []
    for cat in raw_categories:
        country = cat.get("country", {})
        categories.append({
            "id": cat.get("id"),
            "name": cat.get("name"),
            "slug": cat.get("slug"),
            "sport": sport_slug,
            "country": {
                "name": country.get("name", cat.get("name")),
                "alpha2": country.get("alpha2", ""),
            },
            "tournament_count": cat.get("tournamentCount", 0),
            "flag": f"https://api.sofascore.com/api/v1/category/{cat.get('id')}/image",
        })

    logger.info(f"Fetched {len(categories)} categories for sport: {sport_slug}")
    cache.set(cache_key, categories, ttl_seconds=TTL_CATEGORIES)
    return categories


def get_category_by_id(sport_slug: str, category_id: int) -> Optional[dict]:
    """Look up a specific category by ID within a sport."""
    categories = get_categories(sport_slug)
    if not categories:
        return None
    return next((c for c in categories if c["id"] == category_id), None)