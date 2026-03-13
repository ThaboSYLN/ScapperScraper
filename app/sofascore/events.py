import time
import logging
from typing import List, Optional
from app.sofascore.session import BASE_URL, safe_get
from app.sofascore.cache import cache, TTL_LIVE_EVENTS

logger = logging.getLogger(__name__)


# ── Public Functions ──────────────────────────────────────────────────────────

def get_live_events_by_sport(sport_slug: str) -> Optional[List[dict]]:
    """
    Fetch all live events for an entire sport.
    e.g., all live football matches worldwide.
    """
    cache_key = f"live:{sport_slug}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{BASE_URL}/sport/{sport_slug}/events/live"
    data = safe_get(url)

    if not data:
        logger.warning(f"No live events returned for sport: {sport_slug}")
        return None

    events = [_shape_event(e) for e in data.get("events", [])]
    logger.info(f"Fetched {len(events)} live events for sport: {sport_slug}")

    cache.set(cache_key, events, ttl_seconds=TTL_LIVE_EVENTS)
    return events


def get_live_events_by_tournament(tournament_id: int) -> Optional[List[dict]]:
    """
    Fetch live events for a specific tournament (league).
    e.g., only Premier League live matches.
    """
    cache_key = f"live:tournament:{tournament_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{BASE_URL}/unique-tournament/{tournament_id}/events/live"
    data = safe_get(url)

    if not data:
        return None

    events = [_shape_event(e) for e in data.get("events", [])]
    logger.info(f"Fetched {len(events)} live events for tournament: {tournament_id}")

    cache.set(cache_key, events, ttl_seconds=TTL_LIVE_EVENTS)
    return events


def get_scheduled_events_by_sport(sport_slug: str, date: str) -> Optional[List[dict]]:
    """
    Fetch scheduled events for a sport on a specific date.
    date format: YYYY-MM-DD
    """
    cache_key = f"scheduled:{sport_slug}:{date}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{BASE_URL}/sport/{sport_slug}/scheduled-events/{date}"
    data = safe_get(url)

    if not data:
        return None

    events = [_shape_event(e) for e in data.get("events", [])]
    logger.info(f"Fetched {len(events)} scheduled events for {sport_slug} on {date}")

    cache.set(cache_key, events, ttl_seconds=300)
    return events


# ── Internal Helpers ──────────────────────────────────────────────────────────

def _calculate_minute(match: dict) -> str:
    """
    Calculate current match minute across different sports/periods.
    Handles Football, Basketball, Ice Hockey, Tennis etc.
    """
    status = match.get("status", {})
    time_data = match.get("time", {})

    if status.get("type") != "inprogress":
        return ""

    period_start = time_data.get("currentPeriodStartTimestamp")
    if not period_start:
        return ""

    now = int(time.time())
    elapsed = (now - period_start) // 60

    description = status.get("description", "").lower()

    if "2nd half" in description or "2nd" in description:
        elapsed += 45
    elif "extra time" in description or "overtime" in description:
        elapsed += 90
    elif "3rd period" in description:
        elapsed += 40
    elif "4th period" in description or "4th quarter" in description:
        elapsed += 60

    # Cap at reasonable values
    if elapsed > 120:
        elapsed = 120

    return f"{elapsed}'"


def _shape_event(e: dict) -> dict:
    """
    Normalize a raw SofaScore event into a clean, frontend-ready shape.
    """
    status = e.get("status", {})
    home_score = e.get("homeScore", {})
    away_score = e.get("awayScore", {})
    tournament = e.get("tournament", {})
    category = tournament.get("category", {})
    home_team = e.get("homeTeam", {})
    away_team = e.get("awayTeam", {})

    return {
        "id": e.get("id"),
        "slug": e.get("slug"),
        "sport": e.get("sport", {}).get("slug", ""),

        # Teams
        "home_team": {
            "id": home_team.get("id"),
            "name": home_team.get("name"),
            "short_name": home_team.get("shortName", home_team.get("name")),
            "logo": f"https://api.sofascore.com/api/v1/team/{home_team.get('id')}/image",
        },
        "away_team": {
            "id": away_team.get("id"),
            "name": away_team.get("name"),
            "short_name": away_team.get("shortName", away_team.get("name")),
            "logo": f"https://api.sofascore.com/api/v1/team/{away_team.get('id')}/image",
        },

        # Scores
        "score": {
            "home": home_score.get("current"),
            "away": away_score.get("current"),
            "home_period": {
                "p1": home_score.get("period1"),
                "p2": home_score.get("period2"),
                "p3": home_score.get("period3"),
                "p4": home_score.get("period4"),
                "extra": home_score.get("overtime"),
            },
            "away_period": {
                "p1": away_score.get("period1"),
                "p2": away_score.get("period2"),
                "p3": away_score.get("period3"),
                "p4": away_score.get("period4"),
                "extra": away_score.get("overtime"),
            },
        },

        # Status & Time
        "status": {
            "code": status.get("code"),
            "type": status.get("type"),     # inprogress, finished, notstarted
            "description": status.get("description"),
            "minute": _calculate_minute(e),
        },

        # Tournament info
        "tournament": {
            "id": tournament.get("uniqueId") or tournament.get("id"),
            "name": tournament.get("name"),
            "slug": tournament.get("slug"),
            "category": {
                "id": category.get("id"),
                "name": category.get("name"),
                "country_alpha2": category.get("country", {}).get("alpha2", ""),
            },
        },

        # Match metadata
        "start_timestamp": e.get("startTimestamp"),
        "round": e.get("roundInfo", {}).get("round"),
        "best_of": e.get("bestOf"),
    }