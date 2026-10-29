"""End-to-end Phase 02 acceptance scenario using one temporary SQLite database."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from mortgage_pricing.config import Settings
from mortgage_pricing.main import create_app
from mortgage_pricing.persistence.database import create_database_engine, create_session_factory
from mortgage_pricing.persistence.models import MortgageApplication, PricingRequest, User
from mortgage_pricing.seed import APPLICATIONS, USERS, seed_database

ROOT = Path(__file__).resolve().parents[1]


def test_phase_02_migration_seed_restart_and_readiness(tmp_path: Path) -> None:
    """A migrated seeded database remains usable after its first engine is closed."""
    database_path = tmp_path / "phase-02-acceptance.db"
    settings = Settings(_env_file=None, database_url=f"sqlite:///{database_path.as_posix()}")
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["settings"] = settings

    command.upgrade(config, "head")
    command.upgrade(config, "head")
    first_seed = seed_database(settings)
    second_seed = seed_database(settings)

    assert first_seed.users_created == len(USERS)
    assert first_seed.applications_created == len(APPLICATIONS)
    assert second_seed.users_created == second_seed.applications_created == 0

    first_engine = create_database_engine(settings)
    try:
        sessions = create_session_factory(first_engine)
        with sessions() as session:
            assert session.scalar(select(func.count()).select_from(User)) == len(USERS)
            assert session.scalar(select(func.count()).select_from(MortgageApplication)) == len(
                APPLICATIONS
            )
            assert session.scalar(select(func.count()).select_from(PricingRequest)) == 0
    finally:
        first_engine.dispose()

    reopened_engine = create_database_engine(settings)
    try:
        reopened_sessions = create_session_factory(reopened_engine)
        with reopened_sessions() as session:
            assert session.scalar(select(func.count()).select_from(User)) == len(USERS)
    finally:
        reopened_engine.dispose()

    with TestClient(create_app(settings)) as client:
        assert client.get("/ready").json() == {"status": "ready"}
