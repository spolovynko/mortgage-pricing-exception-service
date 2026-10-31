"""FastAPI application factory, process liveness, and database readiness."""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles

from mortgage_pricing.api.assessments import router as assessments_router
from mortgage_pricing.api.errors import error_response, register_error_handlers
from mortgage_pricing.api.foundation import DemoError, demo_error_handler
from mortgage_pricing.api.foundation import router as demo_router
from mortgage_pricing.api.pricing import router as pricing_router
from mortgage_pricing.api.reads import router as reads_router
from mortgage_pricing.api.requests import router as requests_router
from mortgage_pricing.api.workflow import router as workflow_router
from mortgage_pricing.config import Settings, get_settings
from mortgage_pricing.observability.logging import create_logger
from mortgage_pricing.observability.request_logging import RequestLoggingMiddleware
from mortgage_pricing.persistence.database import create_database_engine


class HealthResponse(BaseModel):
    """Minimal process liveness response; it does not imply dependency readiness."""

    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    status: Literal["ready"]


SCHEMA_REVISION = "20261031_0005"
APPLICATION_ROOT = Path(
    os.environ.get("MORTGAGE_PRICING_ROOT", Path(__file__).resolve().parents[2])
)
UI_DIRECTORY = APPLICATION_ROOT / "ui"


def database_ready(app: FastAPI) -> bool:
    """Check migrated SQLite storage and prove that a write transaction can start."""
    url = make_url(app.state.settings.database_url)
    if url.drivername != "sqlite":
        return False
    database = url.database
    if database != ":memory:" and database is not None:
        database_path = Path(database.removeprefix("file:"))
        if not database_path.is_file():
            return False
    if app.state.database_engine is None:
        return False
    try:
        with app.state.database_engine.connect() as connection:
            revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one_or_none()
            if revision != SCHEMA_REVISION:
                connection.rollback()
                return False
            connection.execute(
                text(
                    "UPDATE alembic_version SET version_num = version_num "
                    "WHERE version_num = :revision"
                ),
                {"revision": SCHEMA_REVISION},
            )
            connection.rollback()
            return True
    except SQLAlchemyError:
        return False


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build an isolated API instance, optionally using caller-supplied settings."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            yield
        finally:
            if app.state.database_engine is not None:
                app.state.database_engine.dispose()

    app = FastAPI(title="Mortgage Pricing Exception Service", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings if settings is not None else get_settings()
    app.state.logger = create_logger(app.state.settings.log_level)
    app.state.database_engine = (
        create_database_engine(app.state.settings)
        if make_url(app.state.settings.database_url).drivername == "sqlite"
        else None
    )
    app.add_middleware(RequestLoggingMiddleware, logger=app.state.logger)
    register_error_handlers(app)
    app.add_exception_handler(DemoError, demo_error_handler)

    async def storage_error(request: Request, _exc: OperationalError) -> JSONResponse:
        return error_response(
            503, "database_unavailable", "Database is unavailable.", request.state.correlation_id
        )

    app.add_exception_handler(OperationalError, storage_error)
    app.include_router(demo_router)
    app.include_router(requests_router)
    app.include_router(reads_router)
    app.include_router(workflow_router)
    app.include_router(pricing_router)
    app.include_router(assessments_router)

    @app.get("/", include_in_schema=False)
    def user_interface() -> HTMLResponse:
        index = (UI_DIRECTORY / "index.html").read_text(encoding="utf-8")
        timeout_ms = int(app.state.settings.ui_timeout_seconds * 1000)
        return HTMLResponse(index.replace("{{API_TIMEOUT_MS}}", str(timeout_ms)))

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/ready", response_model=ReadinessResponse, tags=["health"])
    def ready(request: Request) -> ReadinessResponse | JSONResponse:
        if database_ready(app):
            return ReadinessResponse(status="ready")
        return error_response(
            503, "database_unavailable", "Database is not ready.", request.state.correlation_id
        )

    app.mount("/ui", StaticFiles(directory=UI_DIRECTORY), name="ui-assets")
    return app
