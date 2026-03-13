import logging
from typing import Optional
from app.sofascore.session import BASE_URL, safe_get
from app.sofascore.cache import cache, TTL_EVENT_DETAILS

logger = logging.getLogger(__name__)


def get_event_details(event_id: int) -> Optional[dict]:
    """Full match details including both teams and current status."""
    cache_key = f"event:detail:{event_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{BASE_URL}/event/{event_id}"
    data = safe_get(url)
    if not data:
        return None

    result = data.get("event", {})
    cache.set(cache_key, result, ttl_seconds=TTL_EVENT_DETAILS)
    return result


def get_event_statistics(event_id: int) -> Optional[dict]:
    """
    Fetch in-game stats: possession, shots, fouls, corners, etc.
    These are the stats that make your platform valuable.
    """
    cache_key = f"event:stats:{event_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{BASE_URL}/event/{event_id}/statistics"
    data = safe_get(url)
    if not data:
        return None

    raw_stats = data.get("statistics", [])
    shaped = _shape_statistics(raw_stats)

    cache.set(cache_key, shaped, ttl_seconds=TTL_EVENT_DETAILS)
    return shaped


def get_event_incidents(event_id: int) -> Optional[list]:
    """
    Fetch match incidents: goals, red cards, yellow cards, substitutions.
    Essential for match timeline display.
    """
    cache_key = f"event:incidents:{event_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{BASE_URL}/event/{event_id}/incidents"
    data = safe_get(url)
    if not data:
        return None

    incidents = data.get("incidents", [])
    shaped = [_shape_incident(i) for i in incidents]

    cache.set(cache_key, shaped, ttl_seconds=TTL_EVENT_DETAILS)
    return shaped


def get_event_lineups(event_id: int) -> Optional[dict]:
    """Fetch confirmed lineups for both teams."""
    cache_key = f"event:lineups:{event_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{BASE_URL}/event/{event_id}/lineups"
    data = safe_get(url)
    if not data:
        return None

    cache.set(cache_key, data, ttl_seconds=300)
    return data


def get_match_odds(event_id: int) -> Optional[dict]:
    """Fetch pre-match odds if available."""
    cache_key = f"event:odds:{event_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{BASE_URL}/event/{event_id}/odds/1/all"
    data = safe_get(url)
    if not data:
        return None

    cache.set(cache_key, data, ttl_seconds=120)
    return data


# ── Shapers ───────────────────────────────────────────────────────────────────

def _shape_statistics(raw_stats: list) -> dict:
    """Flatten nested stats periods into a clean dict."""
    result = {}
    for period in raw_stats:
        period_name = period.get("period", "ALL")
        groups = period.get("groups", [])
        period_data = {}
        for group in groups:
            for stat in group.get("statisticsItems", []):
                key = stat.get("key", stat.get("name", "unknown"))
                period_data[key] = {
                    "name": stat.get("name"),
                    "home": stat.get("home"),
                    "away": stat.get("away"),
                    "home_value": stat.get("homeValue"),
                    "away_value": stat.get("awayValue"),
                    "render_type": stat.get("renderType"),
                }
        result[period_name] = period_data
    return result


def _shape_incident(i: dict) -> dict:
    """Normalize an incident into a clean format."""
    return {
        "id": i.get("id"),
        "type": i.get("incidentType"),
        "time": i.get("time"),
        "added_time": i.get("addedTime"),
        "team": "home" if i.get("isHome") else "away",
        "description": i.get("incidentClass"),
        "player": {
            "id": i.get("player", {}).get("id"),
            "name": i.get("player", {}).get("name"),
        } if i.get("player") else None,
        "assist": {
            "id": i.get("assist1", {}).get("id"),
            "name": i.get("assist1", {}).get("name"),
        } if i.get("assist1") else None,
        "substitute_in": {
            "id": i.get("playerIn", {}).get("id"),
            "name": i.get("playerIn", {}).get("name"),
        } if i.get("playerIn") else None,
    }