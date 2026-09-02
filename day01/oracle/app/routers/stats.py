from fastapi import APIRouter, Request

from app.ml import features as f
from app.schemas import HealthResponse, OptionsResponse, StatsResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    state = request.app.state
    return HealthResponse(
        status="ok",
        # Always true once we are serving: a missing artifact kills startup instead.
        models_loaded=getattr(state, "models", None) is not None,
        llm_configured=state.settings.llm_configured,
    )


@router.get("/stats", response_model=StatsResponse)
async def stats(request: Request) -> StatsResponse:
    return request.app.state.store.snapshot()


@router.get("/options", response_model=OptionsResponse)
async def options() -> OptionsResponse:
    """Valid values for every dropdown, so the page and the API can never disagree."""
    return OptionsResponse(
        countries=f.COUNTRIES + [f.OTHER_COUNTRY],
        ed_levels=f.ED_LEVELS,
        dev_types=f.DEV_TYPES,
        remote_work=f.REMOTE_WORK,
        age_bands=f.AGE_BANDS,
        org_sizes=f.ORG_SIZES,
        languages=f.LANGUAGES,
        relationship_statuses=f.RELATIONSHIP_STATUSES,
    )
