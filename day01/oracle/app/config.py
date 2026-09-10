from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent


class Settings(BaseSettings):
    """All runtime configuration. Every value can be overridden by an env var of the same name."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=(),
    )

    openrouter_api_key: str | None = None
    llm_model: str = "poolside/laguna-s-2.1:free"
    llm_base_url: str = "https://openrouter.ai/api/v1"
    model_api_url: str = "http://localhost:8000"
    # Reasoning models think before answering; that costs seconds. off | low | medium | high
    llm_reasoning: str = "low"
    # Free-tier providers fail transiently; retry the model call this many times in total.
    llm_max_attempts: int = 3
    artifacts_dir: Path = PROJECT_DIR / "artifacts"

    # Database. Either give DATABASE_URL directly, or the parts (this is what ECS
    # gets on Day 4: host and port from the stack, password from Secrets Manager).
    # With neither, the app keeps its counters in memory, as on Day 1.
    database_url: str | None = None
    db_host: str | None = None
    db_port: int = 5432
    db_name: str = "oracle"
    db_user: str = "oracle"
    db_password: str | None = None

    @property
    def llm_configured(self) -> bool:
        return bool(self.openrouter_api_key)

    @property
    def effective_database_url(self) -> str | None:
        if self.database_url:
            return self.database_url
        if self.db_host and self.db_password:
            return (
                f"postgresql://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
