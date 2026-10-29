"""Validated application settings loaded from environment and an optional .env file."""

from typing import Literal

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Immutable configuration shared by application setup and tests."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        frozen=True,
        hide_input_in_errors=True,
    )

    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    database_url: str = Field(default="sqlite:///./data/mortgage_pricing.db", repr=False)
    sqlite_busy_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    demo_identity_mode: Literal["off", "header"] = "off"
    ui_timeout_seconds: float = Field(default=10.0, gt=0, le=120)
    llm_mode: Literal["off", "auto"] = "off"
    llm_base_url: HttpUrl = HttpUrl("http://127.0.0.1:11434/")
    llm_model: str = Field(default="qwen3:4b-instruct-2507-q4_K_M", min_length=1, max_length=128)
    llm_timeout_seconds: float = Field(default=30.0, gt=0, le=120)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.startswith(("sqlite:///", "postgresql://", "postgresql+psycopg://")):
            raise ValueError("must use a supported SQLite or PostgreSQL URL")
        return value


def get_settings() -> Settings:
    """Load settings on demand; callers can inject Settings directly in tests."""
    return Settings()
