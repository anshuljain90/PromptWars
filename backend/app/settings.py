"""Centralized environment-driven settings.

In dev these come from a local .env file; in production from Google Secret
Manager mounted as environment variables on Cloud Run.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    gemini_api_key: str = Field(default="", description="AI Studio Gemini API key")
    gemini_model: str = Field(default="gemini-2.0-flash-exp")

    google_maps_api_key: str = Field(default="")

    firebase_project_id: str = Field(default="")
    google_application_credentials: str = Field(default="")

    allowed_origins: str = Field(default="http://localhost:3000")

    places_backend: Literal["live", "fixture"] = Field(default="live")
    cache_ttl_seconds: int = Field(default=3600, ge=0)

    rate_limit_per_minute: int = Field(default=30, ge=1)
    external_call_timeout_seconds: float = Field(default=15.0, gt=0)

    log_level: str = Field(default="INFO")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor — call this everywhere instead of constructing."""
    return Settings()
