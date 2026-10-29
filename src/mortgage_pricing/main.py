"""FastAPI application factory and process liveness endpoint."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from mortgage_pricing.config import Settings, get_settings
from mortgage_pricing.logging_config import create_logger
from mortgage_pricing.request_logging import RequestLoggingMiddleware


class HealthResponse(BaseModel):
    """Minimal process liveness response; it does not imply dependency readiness."""

    status: Literal["ok"]


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build an isolated API instance, optionally using caller-supplied settings."""
    app = FastAPI(title="Mortgage Pricing Exception Service", version="0.1.0")
    app.state.settings = settings if settings is not None else get_settings()
    app.state.logger = create_logger(app.state.settings.log_level)
    app.add_middleware(RequestLoggingMiddleware, logger=app.state.logger)

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    return app
