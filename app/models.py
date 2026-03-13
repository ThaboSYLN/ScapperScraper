from pydantic import BaseModel
from typing import Optional, List, Any


class SportModel(BaseModel):
    id: int
    name: str
    slug: str


class CountryModel(BaseModel):
    name: str
    alpha2: Optional[str] = ""


class CategoryModel(BaseModel):
    id: int
    name: str
    slug: Optional[str] = None
    sport: str
    country: CountryModel
    tournament_count: int
    flag: Optional[str] = None


class TournamentModel(BaseModel):
    id: Optional[int] = None
    name: str
    slug: Optional[str] = None
    category_id: int
    logo: Optional[str] = None
    primary_color: Optional[str] = "#000000"
    secondary_color: Optional[str] = "#FFFFFF"


class TeamModel(BaseModel):
    id: Optional[int] = None
    name: str
    short_name: Optional[str] = None
    logo: Optional[str] = None


class ScorePeriodModel(BaseModel):
    p1: Optional[int] = None
    p2: Optional[int] = None
    p3: Optional[int] = None
    p4: Optional[int] = None
    extra: Optional[int] = None


class ScoreModel(BaseModel):
    home: Optional[int] = None
    away: Optional[int] = None
    home_period: Optional[ScorePeriodModel] = None
    away_period: Optional[ScorePeriodModel] = None


class StatusModel(BaseModel):
    code: Optional[int] = None
    type: Optional[str] = None
    description: Optional[str] = None
    minute: Optional[str] = ""


class EventTournamentModel(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    category: Optional[Any] = None


class EventModel(BaseModel):
    id: int
    slug: Optional[str] = None
    sport: Optional[str] = None
    home_team: TeamModel
    away_team: TeamModel
    score: ScoreModel
    status: StatusModel
    tournament: Optional[EventTournamentModel] = None
    start_timestamp: Optional[int] = None
    round: Optional[int] = None
    best_of: Optional[int] = None


# ── Generic API Response Wrappers ─────────────────────────────────────────────

class APIResponse(BaseModel):
    success: bool
    count: Optional[int] = None
    data: Any
    cached: bool = False


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None