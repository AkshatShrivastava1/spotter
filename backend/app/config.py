from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SPOTTER_", extra="ignore")

    database_url: str = "sqlite:///./spotter.db"

    # LLM provider: "anthropic" or "mock". "auto" picks anthropic when a key is present.
    llm_provider: str = "auto"
    anthropic_api_key: str | None = None
    # Cheap/fast model for parsing food text & photos; stronger model for coaching voice.
    parse_model: str = "claude-haiku-4-5-20251001"
    coach_model: str = "claude-sonnet-5-5"

    # Background nudge engine
    scheduler_enabled: bool = True
    nudge_interval_minutes: int = 15

    expo_push_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
