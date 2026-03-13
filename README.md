# SofaScore Live Sports Backend

A production-grade FastAPI backend that fetches live sports data from SofaScore.
Built for integration with a frontend dashboard and future Google AdSense monetization.

---

## Project Structure

```
sofascore_backend/
│
├── app/
│   ├── main.py                  ← FastAPI app, all routes
│   ├── models.py                ← Pydantic response models
│   └── sofascore/
│         ├── session.py         ← HTTP session + rotating user agents
│         ├── cache.py           ← In-memory TTL cache
│         ├── sports.py          ← Sports list
│         ├── categories.py      ← Countries/regions per sport
│         ├── tournaments.py     ← Leagues per country
│         ├── events.py          ← Live + scheduled events
│         └── event_details.py   ← Stats, incidents, lineups, odds
│
├── logs/                        ← Auto-created on startup
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run locally
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Open interactive docs
```
http://localhost:8000/docs
```

---

## API Flow (How to Use)

```
1. GET /sports                              → List all sports
2. GET /sports/{slug}/categories            → Countries for that sport
3. GET /categories/{id}/tournaments         → Leagues in that country
4. GET /sports/{slug}/events/live           → All live matches for sport
5. GET /tournaments/{id}/events/live        → Live matches in a league
6. GET /events/{id}/statistics              → In-game stats
7. GET /events/{id}/incidents               → Goals, cards, subs
8. GET /events/{id}/lineups                 → Team lineups
```

### Example: Football → England → Live Matches
```bash
# Step 1: Get football categories
GET /sports/football/categories

# Step 2: Find England's category ID (e.g. 1)
GET /categories/1/tournaments

# Step 3: Find Premier League tournament ID (e.g. 17)
GET /tournaments/17/events/live

# Step 4: Get match details
GET /events/{event_id}/statistics
```

---

## Endpoints Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Health + cache stats |
| DELETE | `/cache` | Clear the cache |
| GET | `/sports` | All sports |
| GET | `/sports/live-counts` | Live event count per sport |
| GET | `/sports/{slug}/categories` | Countries for sport |
| GET | `/categories/{id}/tournaments` | Leagues in country |
| GET | `/sports/{slug}/events/live` | All live events for sport |
| GET | `/tournaments/{id}/events/live` | Live events in tournament |
| GET | `/sports/{slug}/events/scheduled` | Scheduled events (date param) |
| GET | `/events/{id}` | Full event details |
| GET | `/events/{id}/statistics` | In-game stats |
| GET | `/events/{id}/incidents` | Goals, cards, subs |
| GET | `/events/{id}/lineups` | Team lineups |
| GET | `/events/{id}/odds` | Pre-match odds |

---

## Caching TTLs

| Data | TTL |
|------|-----|
| Sports list | 60 minutes |
| Categories | 30 minutes |
| Tournaments | 10 minutes |
| Live events | 30 seconds |
| Event details | 20 seconds |

---

## Deployment

### Render (Recommended — free tier available)
1. Push to GitHub
2. Create a new Web Service on Render
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Railway
Same setup — connect GitHub repo, auto-detects FastAPI.

### Fly.io
```bash
fly launch
fly deploy
```

---

## Week-by-Week Plan

| Sprint | Focus |
|--------|-------|
| Week 1 | This backend — all endpoints live |
| Week 2 | Analytics layer — momentum, goal probability, match insights |
| Week 3 | Frontend — React dashboard, sport → league → live match flow |
| Week 4 | Deployment + Google AdSense integration |

---

## Notes
- User agents rotate on every request to avoid Cloudflare detection
- Session is recreated per request (avoids sticky bans)
- All endpoints return `{ success, count, data }` for consistent frontend integration
- CORS is open (`*`) during development — lock it to your frontend domain before launch