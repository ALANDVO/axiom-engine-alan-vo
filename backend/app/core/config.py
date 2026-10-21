from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "axiom-engine"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    DEMO_MODE: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/axiom.db"

    # Auth (Keycloak OIDC)
    KEYCLOAK_URL: Optional[str] = None
    KEYCLOAK_REALM: Optional[str] = None
    KEYCLOAK_CLIENT_ID: Optional[str] = None
    KEYCLOAK_CLIENT_SECRET: Optional[str] = None

    # LLM
    LLM_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "openai-compatible"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: Optional[str] = None

    # Routing
    DEFAULT_ROUTING_STRATEGY: str = "round_robin"
    HEALTH_CHECK_INTERVAL_SECONDS: int = 60
    PROBE_ENABLED: bool = False

    # Concurrency
    MAX_CONCURRENT_REQUESTS_PER_KEY: Optional[int] = 10
    HEDGE_AFTER_MS: int = 0

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()