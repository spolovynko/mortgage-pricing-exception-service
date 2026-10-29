"""Prepare persistent storage safely, then replace this process with Uvicorn."""

import os
import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

from mortgage_pricing.config import Settings, get_settings
from mortgage_pricing.logging_config import create_logger
from mortgage_pricing.seed import SeedResult, seed_database

APPLICATION_ROOT = Path(
    os.environ.get("MORTGAGE_PRICING_ROOT", Path(__file__).resolve().parents[2])
)


def sqlite_storage_path(settings: Settings) -> Path:
    """Return the configured file-backed SQLite path or reject unsafe startup modes."""
    url = make_url(settings.database_url)
    if url.drivername != "sqlite" or url.database in {None, ":memory:"}:
        raise ValueError("Container startup requires a file-backed SQLite database")
    if url.query.get("mode") == "ro":
        raise ValueError("Container startup requires writable SQLite storage")
    return Path(url.database.removeprefix("file:")).resolve()


def ensure_storage_writable(settings: Settings) -> Path:
    """Create the data directory and verify the runtime user can write within it."""
    database_path = sqlite_storage_path(settings)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=".storage-probe-", dir=database_path.parent):
        pass
    return database_path


def prepare_database(settings: Settings) -> SeedResult:
    """Validate storage, migrate it to head, and insert fixed synthetic seeds."""
    ensure_storage_writable(settings)
    alembic_config = Config(str(APPLICATION_ROOT / "alembic.ini"))
    alembic_config.attributes["settings"] = settings
    command.upgrade(alembic_config, "head")
    return seed_database(settings)


def serve() -> None:
    """Replace the startup process so Uvicorn receives container signals directly."""
    os.execvp(
        "uvicorn",
        [
            "uvicorn",
            "mortgage_pricing.main:create_app",
            "--factory",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--log-config",
            "config/logging.json",
            "--no-access-log",
        ],
    )


def main() -> int:
    """Fail closed on preparation errors; serve only after migration and seeding."""
    bootstrap_logger = create_logger("INFO")
    try:
        settings = get_settings()
        logger = create_logger(settings.log_level)
        result = prepare_database(settings)
    except Exception:
        bootstrap_logger.exception("container_startup_failed", extra={"outcome": "failure"})
        return 1
    logger.info(
        "container_storage_ready",
        extra={
            "outcome": "success",
            "users_created": result.users_created,
            "applications_created": result.applications_created,
        },
    )
    serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
