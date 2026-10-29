"""Repeatable synthetic seed data on databases created through Alembic."""

import json
import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from mortgage_pricing.config import Settings
from mortgage_pricing.persistence.database import create_database_engine, create_session_factory
from mortgage_pricing.persistence.models import (
    MortgageApplication,
    PricingRequest,
    Role,
    User,
    UserRoleMembership,
)
from mortgage_pricing.seed import (
    APPLICATIONS,
    USERS,
    SeedConflictError,
    seed_database,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def migrated_database(tmp_path: Path) -> Iterator[tuple[Settings, sessionmaker[Session]]]:
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'seed.db').as_posix()}",
    )
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["settings"] = settings
    command.upgrade(config, "head")
    engine: Engine = create_database_engine(settings)
    try:
        yield settings, create_session_factory(engine)
    finally:
        engine.dispose()


def count(session: Session, model: type[object]) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def test_seed_is_repeatable_and_reserves_a_clean_demo_application(
    migrated_database: tuple[Settings, sessionmaker[Session]],
) -> None:
    settings, sessions = migrated_database
    first = seed_database(settings)
    second = seed_database(settings)
    assert first.users_created == len(USERS)
    assert first.applications_created == len(APPLICATIONS)
    assert second.users_created == second.applications_created == 0

    with sessions() as session:
        assert count(session, User) == len(USERS)
        assert count(session, UserRoleMembership) == 4
        assert count(session, MortgageApplication) == len(APPLICATIONS)
        assert count(session, PricingRequest) == 0
        demo = session.get(MortgageApplication, APPLICATIONS[0].id)
        assert demo is not None
        assert demo.reference == "SYN-MORTGAGE-DEMO-CLEAN"


def test_seed_preserves_unrelated_existing_records(
    migrated_database: tuple[Settings, sessionmaker[Session]],
) -> None:
    settings, sessions = migrated_database
    with sessions.begin() as session:
        existing = User(id=uuid4(), login="existing.manager", display_name="Existing Manager")
        existing.role_memberships.append(UserRoleMembership(role=Role.RELATIONSHIP_MANAGER))
        session.add(existing)

    seed_database(settings)
    second = seed_database(settings)
    assert second.users_created == second.applications_created == 0
    with sessions() as session:
        existing = session.scalar(select(User).where(User.login == "existing.manager"))
        assert existing is not None and existing.display_name == "Existing Manager"
        assert count(session, User) == len(USERS) + 1


def test_seed_conflict_rolls_back_without_overwriting_existing_data(
    migrated_database: tuple[Settings, sessionmaker[Session]],
) -> None:
    settings, sessions = migrated_database
    with sessions.begin() as session:
        manager = User(id=uuid4(), login="other.manager", display_name="Other Manager")
        manager.role_memberships.append(UserRoleMembership(role=Role.RELATIONSHIP_MANAGER))
        session.add(manager)
        session.flush()
        session.add(
            MortgageApplication(
                id=uuid4(),
                reference=APPLICATIONS[0].reference,
                manager_id=manager.id,
            )
        )

    with pytest.raises(SeedConflictError, match="Seed application identifier"):
        seed_database(settings)

    with sessions() as session:
        assert count(session, User) == 1
        assert count(session, MortgageApplication) == 1


def test_seed_requires_an_applied_migration(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'unmigrated.db').as_posix()}",
    )
    with pytest.raises(OperationalError):
        seed_database(settings)


def test_seed_module_command_emits_a_safe_summary(
    migrated_database: tuple[Settings, sessionmaker[Session]],
) -> None:
    settings, _ = migrated_database
    environment = os.environ | {"DATABASE_URL": settings.database_url}
    completed = subprocess.run(
        [sys.executable, "-m", "mortgage_pricing.seed"],
        check=False,
        capture_output=True,
        cwd=ROOT,
        env=environment,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0
    entry = json.loads(completed.stdout)
    assert entry["event"] == "database_seed_completed"
    assert entry["outcome"] == "success"
    assert "SYN-MORTGAGE" not in completed.stdout
