"""The Oracle's tools. Each one calls this app's own HTTP API.

On Day 1 the API is the same process, so this is a loopback call. Later in the course the
models move to another container and only API_BASE_URL changes.
"""

import json

import httpx
from langchain_core.tools import tool

from app.config import get_settings
from app.schemas import AgeBand, DevType, EdLevel, OrgSize, RelationshipStatus, RemoteWork

API_BASE_URL = get_settings().model_api_url.rstrip("/")
TIMEOUT_SECONDS = 30


def set_api_base_url(url: str) -> None:
    global API_BASE_URL
    API_BASE_URL = url.rstrip("/")


async def _get(path: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=TIMEOUT_SECONDS) as client:
        r = await client.get(path, params=params)
        r.raise_for_status()
        return r.json()


async def _post(path: str, payload: dict) -> dict:
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=TIMEOUT_SECONDS) as client:
        r = await client.post(path, json=payload)
        r.raise_for_status()
        return r.json()


def _error(exc: Exception) -> str:
    detail = ""
    if isinstance(exc, httpx.HTTPStatusError):
        detail = f" ({exc.response.status_code}: {exc.response.text[:200]})"
    return f"Tool error: {type(exc).__name__}{detail}. Tell the seeker the spirits are busy."


@tool
async def get_horoscope(birthday: str) -> str:
    """Get today's horoscope for a person. birthday must be YYYY-MM-DD."""
    try:
        return json.dumps(await _get("/horoscope", {"birthday": birthday}))
    except Exception as exc:  # noqa: BLE001 - errors go back to the LLM as text
        return _error(exc)


@tool
async def predict_income(
    country: str,
    years_pro: int,
    ed_level: EdLevel,
    dev_type: DevType,
    remote_work: RemoteWork,
    age_band: AgeBand,
    org_size: OrgSize,
    languages: list[str],
    name: str | None = None,
) -> str:
    """Predict yearly income in USD from a developer's profile using the survey model.

    years_pro is years of professional coding experience (0-50). languages is a list such as
    ["Python", "SQL"]. Pass name so the person appears on the leaderboard.
    """
    payload = {
        "name": name,
        "country": country,
        "years_pro": years_pro,
        "ed_level": ed_level,
        "dev_type": dev_type,
        "remote_work": remote_work,
        "age_band": age_band,
        "org_size": org_size,
        "languages": languages,
    }
    try:
        return json.dumps(await _post("/predict/income", payload))
    except Exception as exc:  # noqa: BLE001
        return _error(exc)


@tool
async def predict_marriage_date(
    age: int,
    relationship_status: RelationshipStatus,
    coffee_cups_per_day: int,
    coding_hours_per_week: int,
    side_projects: int,
    unread_slack_messages: int,
) -> str:
    """Predict the date of a person's wedding. This model is a joke trained on invented data."""
    payload = {
        "age": age,
        "relationship_status": relationship_status,
        "coffee_cups_per_day": coffee_cups_per_day,
        "coding_hours_per_week": coding_hours_per_week,
        "side_projects": side_projects,
        "unread_slack_messages": unread_slack_messages,
    }
    try:
        return json.dumps(await _post("/predict/marriage", payload))
    except Exception as exc:  # noqa: BLE001
        return _error(exc)


ORACLE_TOOLS = [get_horoscope, predict_income, predict_marriage_date]
