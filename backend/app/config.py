import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_db_url(url: str) -> str:
    """Hosts (Render, Railway, Neon, Supabase) hand out postgres:// URLs; SQLAlchemy needs the psycopg driver named."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


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

    # Shared secret for POST /internal/run-nudges (lets an external cron drive nudges when the
    # in-process scheduler is off, e.g. on hosts that sleep idle servers). Empty = endpoint disabled.
    cron_secret: str = ""

    # Signs login tokens. Must be set (and kept secret) in production.
    jwt_secret: str = ""

    # "production" turns on startup checks (see production_problems). Anything else = local dev.
    env: str = "development"

    @property
    def db_url(self) -> str:
        # Hosts usually inject a plain DATABASE_URL; SPOTTER_DATABASE_URL still wins if set.
        explicit = os.getenv("SPOTTER_DATABASE_URL")
        return normalize_db_url(explicit or os.getenv("DATABASE_URL") or self.database_url)

    def production_problems(self) -> list[str]:
        """Settings that would make a live server insecure or silently broken."""
        problems = []
        if len(self.jwt_secret) < 32:
            problems.append("SPOTTER_JWT_SECRET must be set to a random value of at least 32 characters")
        if self.db_url.startswith("sqlite"):
            problems.append("DATABASE_URL must point at Postgres (SQLite lives on the server's disk, which gets wiped)")
        if not self.scheduler_enabled and not self.cron_secret:
            problems.append("SPOTTER_CRON_SECRET must be set when the scheduler is off, or nudges never run")
        return problems


def check_production(settings: Settings) -> None:
    """Fail at startup, with a clear message, instead of running a misconfigured live server."""
    if settings.env != "production":
        return
    problems = settings.production_problems()
    if problems:
        raise RuntimeError("Refusing to start in production:\n- " + "\n- ".join(problems))


@lru_cache
def get_settings() -> Settings:
    return Settings()
