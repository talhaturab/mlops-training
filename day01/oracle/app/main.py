from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langgraph.checkpoint.memory import InMemorySaver

from app.agent.graph import build_graph, create_llm
from app.agent.tools import ORACLE_TOOLS, set_api_base_url
from app.config import PROJECT_DIR, Settings, get_settings
from app.ml.predict import LoadedModels
from app.routers import chat, predict, stats
from app.store import StatsStore


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Everything the app needs at runtime is attached to app.state here, once.
        app.state.settings = settings
        app.state.models = LoadedModels(settings.artifacts_dir)
        app.state.store = StatsStore()
        set_api_base_url(settings.model_api_url)
        if settings.llm_configured:
            app.state.graph = build_graph(create_llm(settings), ORACLE_TOOLS, InMemorySaver())
        else:
            app.state.graph = None
        yield

    app = FastAPI(title="The Oracle", version="0.1.0", lifespan=lifespan)
    app.include_router(stats.router)
    app.include_router(predict.router)
    app.include_router(chat.router)

    static_dir = PROJECT_DIR / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    return app


app = create_app()
