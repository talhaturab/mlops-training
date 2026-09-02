"""Every request and response body. FastAPI uses these for validation and for /docs."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.ml import features as f

# Literal[tuple(...)] is the same as Literal[a, b, c]: the docs page lists the valid
# values and anything else is rejected with a 422 before our code runs.
EdLevel = Literal[tuple(f.ED_LEVELS)]  # type: ignore[valid-type]
DevType = Literal[tuple(f.DEV_TYPES)]  # type: ignore[valid-type]
RemoteWork = Literal[tuple(f.REMOTE_WORK)]  # type: ignore[valid-type]
AgeBand = Literal[tuple(f.AGE_BANDS)]  # type: ignore[valid-type]
OrgSize = Literal[tuple(f.ORG_SIZES)]  # type: ignore[valid-type]
RelationshipStatus = Literal[tuple(f.RELATIONSHIP_STATUSES)]  # type: ignore[valid-type]


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    llm_configured: bool


class IncomeRequest(BaseModel):
    name: str | None = Field(default=None, max_length=40, description="Shown on the leaderboard")
    country: str = Field(
        max_length=100, description="Free text; unknown countries are grouped as 'Other'"
    )
    years_pro: int = Field(ge=0, le=50, description="Years of professional coding experience")
    ed_level: EdLevel
    dev_type: DevType
    remote_work: RemoteWork
    age_band: AgeBand
    org_size: OrgSize
    languages: list[str] = Field(
        default_factory=list, max_length=30, description="e.g. ['Python', 'SQL']"
    )


class IncomeResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    predicted_income_usd: float
    model_version: str
    disclaimer: str


class MarriageRequest(BaseModel):
    age: int = Field(ge=18, le=100)
    relationship_status: RelationshipStatus
    coffee_cups_per_day: int = Field(ge=0, le=20)
    coding_hours_per_week: int = Field(ge=0, le=100)
    side_projects: int = Field(ge=0, le=50)
    unread_slack_messages: int = Field(ge=0, le=100_000)


class MarriageResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    predicted_date: date
    years_from_now: float
    model_version: str
    disclaimer: str


class HoroscopeResponse(BaseModel):
    sign: str
    message: str


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply: str
    tools_used: list[str]


class LeaderboardEntry(BaseModel):
    name: str
    predicted_income_usd: float


class StatsResponse(BaseModel):
    fortunes_told: int
    leaderboard: list[LeaderboardEntry]


class OptionsResponse(BaseModel):
    countries: list[str]
    ed_levels: list[str]
    dev_types: list[str]
    remote_work: list[str]
    age_bands: list[str]
    org_sizes: list[str]
    languages: list[str]
    relationship_statuses: list[str]
