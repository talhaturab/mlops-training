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
    llm_model: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    llm_base_url: str = "https://openrouter.ai/api/v1"
    model_api_url: str = "http://localhost:8000"
    artifacts_dir: Path = PROJECT_DIR / "artifacts"

    @property
    def llm_configured(self) -> bool:
        return bool(self.openrouter_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
