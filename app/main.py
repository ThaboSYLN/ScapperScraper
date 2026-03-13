import logging
import logging.config
import os
from datetime import date as date_type
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.models import APIResponse, ErrorResponse
from app.sofascore.sports import get_all_sports, get_sport_by_slug, get_live_counts
from app.sofascore.categories import get_categories
from app.sofascore.tournaments import get_tournaments
from app.sofascore.events import (
    get_live_events_by_sport,
    get_live_events_by_tournament,
    get_scheduled_events_by_sport,
)
from app.sofascore.event_details import (
    get_event_details,
    get_event_statistics,
    get_event_incidents,
    get_event_lineups,
    get_match_odds,
)
from app.sofascore.cache import cache

# ── Logging Setup ─────────────────────────────────────────────────────────────

os.makedirs("logs", exist_ok=True)

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "detailed",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "logs/app.log",
            "formatter": "detailed",
            "encoding": "utf-8",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
})

logger = logging.getLogger(__name__)


# ── App Lifecycle ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SofaScore Backend starting up...")
    yield
    logger.info("SofaScore Backend shutting down...")
    cache.clear()


# ── App Init ──────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SofaScore Live Sports API",
    description=(
        "A clean, cached FastAPI backend that proxies SofaScore data. "
        "Hierarchy: Sport -> Categories -> Tournaments -> Live Events -> Match Details."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS (open during dev — lock to your frontend domain before going live) ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ── Utility ───────────────────────────────────────────────────────────────────

def _ok(data, count: bool = True) -> APIResponse:
    """Wrap data in a standard success response."""
    return APIResponse(
        success=True,
        count=len(data) if count and isinstance(data, list) else None,
        data=data,
    )


def _not_found(detail: str):
    raise HTTPException(status_code=404, detail=detail)


def _bad_gateway(detail: str):
    raise HTTPException(status_code=502, detail=detail)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "SofaScore Backend is live"}


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "cache": cache.stats(),
    }


@app.delete("/cache", tags=["Health"])
async def clear_cache():
    cache.clear()
    return {"status": "ok", "message": "Cache cleared"}


# ── Sports ────────────────────────────────────────────────────────────────────

@app.get("/sports", tags=["Sports"], response_model=APIResponse)
async def list_sports():
    """Returns the full list of supported sports. Use the slug in all subsequent calls."""
    sports = get_all_sports()
    return _ok(sports)


@app.get("/sports/live-counts", tags=["Sports"], response_model=APIResponse)
async def sports_live_counts():
    """Returns the number of live events per sport. Use sparingly — makes one request per sport."""
    counts = get_live_counts()
    return _ok(counts, count=False)


# ── Categories ────────────────────────────────────────────────────────────────

@app.get("/sports/{sport_slug}/categories", tags=["Categories"], response_model=APIResponse)
async def list_categories(
    sport_slug: str = Path(..., description="Sport slug e.g. football, basketball")
):
    """Returns all countries/regions for a sport. Football -> England, Spain, Germany..."""
    sport = get_sport_by_slug(sport_slug)
    if not sport:
        _not_found(f"Sport '{sport_slug}' not found. Check /sports for valid slugs.")

    categories = get_categories(sport_slug)
    if categories is None:
        _bad_gateway(f"Could not fetch categories for sport: {sport_slug}")

    return _ok(categories)


# ── Tournaments ───────────────────────────────────────────────────────────────

@app.get("/categories/{category_id}/tournaments", tags=["Tournaments"], response_model=APIResponse)
async def list_tournaments(
    category_id: int = Path(..., description="Category ID from /categories endpoint")
):
    """Returns all tournaments (leagues) in a category. England -> Premier League, Championship..."""
    tournaments = get_tournaments(category_id)
    if tournaments is None:
        _bad_gateway(f"Could not fetch tournaments for category: {category_id}")

    return _ok(tournaments)


# ── Live Events ───────────────────────────────────────────────────────────────

@app.get("/sports/{sport_slug}/events/live", tags=["Events"], response_model=APIResponse)
async def live_events_by_sport(
    sport_slug: str = Path(..., description="Sport slug e.g. football")
):
    """Returns ALL live events for a sport across every tournament. Cached for 30 seconds."""
    sport = get_sport_by_slug(sport_slug)
    if not sport:
        _not_found(f"Sport '{sport_slug}' not found.")

    events = get_live_events_by_sport(sport_slug)
    if events is None:
        _bad_gateway(f"Could not fetch live events for sport: {sport_slug}")

    return _ok(events)


@app.get("/tournaments/{tournament_id}/events/live", tags=["Events"], response_model=APIResponse)
async def live_events_by_tournament(
    tournament_id: int = Path(..., description="Tournament ID from /tournaments endpoint")
):
    """Returns live events filtered to one specific tournament (league)."""
    events = get_live_events_by_tournament(tournament_id)
    if events is None:
        _bad_gateway(f"Could not fetch live events for tournament: {tournament_id}")

    return _ok(events)


@app.get("/sports/{sport_slug}/events/scheduled", tags=["Events"], response_model=APIResponse)
async def scheduled_events(
    sport_slug: str = Path(..., description="Sport slug"),
    date: Optional[str] = Query(
        default=None,
        description="Date in YYYY-MM-DD format. Defaults to today."
    ),
):
    """Returns scheduled (upcoming) events for a sport on a given date."""
    sport = get_sport_by_slug(sport_slug)
    if not sport:
        _not_found(f"Sport '{sport_slug}' not found.")

    target_date = date or str(date_type.today())

    events = get_scheduled_events_by_sport(sport_slug, target_date)
    if events is None:
        _bad_gateway(f"Could not fetch scheduled events for {sport_slug} on {target_date}")

    return _ok(events)


# ── Event Details ─────────────────────────────────────────────────────────────

@app.get("/events/{event_id}", tags=["Event Details"], response_model=APIResponse)
async def event_details(
    event_id: int = Path(..., description="Event ID from the events endpoints")
):
    """Full event details including both teams, venue, and current status."""
    data = get_event_details(event_id)
    if data is None:
        _not_found(f"Event {event_id} not found or unavailable.")
    return _ok(data, count=False)


@app.get("/events/{event_id}/statistics", tags=["Event Details"], response_model=APIResponse)
async def event_statistics(
    event_id: int = Path(..., description="Event ID")
):
    """In-game statistics: possession, shots on target, fouls, corners, etc."""
    data = get_event_statistics(event_id)
    if data is None:
        _not_found(f"Statistics for event {event_id} not available.")
    return _ok(data, count=False)


@app.get("/events/{event_id}/incidents", tags=["Event Details"], response_model=APIResponse)
async def event_incidents(
    event_id: int = Path(..., description="Event ID")
):
    """Match incidents: goals, red/yellow cards, substitutions. Use for match timeline."""
    data = get_event_incidents(event_id)
    if data is None:
        _not_found(f"Incidents for event {event_id} not available.")
    return _ok(data)


@app.get("/events/{event_id}/lineups", tags=["Event Details"], response_model=APIResponse)
async def event_lineups(
    event_id: int = Path(..., description="Event ID")
):
    """Confirmed lineups for both teams."""
    data = get_event_lineups(event_id)
    if data is None:
        _not_found(f"Lineups for event {event_id} not available.")
    return _ok(data, count=False)


@app.get("/events/{event_id}/odds", tags=["Event Details"], response_model=APIResponse)
async def event_odds(
    event_id: int = Path(..., description="Event ID")
):
    """Pre-match odds if available from SofaScore."""
    data = get_match_odds(event_id)
    if data is None:
        _not_found(f"Odds for event {event_id} not available.")
    return _ok(data, count=False)


# ── Exception Handlers ────────────────────────────────────────────────────────

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(success=False, error="Not Found", detail=str(exc.detail)).model_dump()
    )


@app.exception_handler(502)
async def bad_gateway_handler(request, exc):
    return JSONResponse(
        status_code=502,
        content=ErrorResponse(success=False, error="Bad Gateway", detail=str(exc.detail)).model_dump()
    )