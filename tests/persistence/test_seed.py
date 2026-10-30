"""Repeatable synthetic seed data on databases created through Alembic."""

import json
import os
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import replace
from decimal import Decimal
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
    DecisionOutcome,
    MortgageApplication,
    PricingRequest,
    Role,
    User,
    UserRoleMembership,
)
from mortgage_pricing.persistence.operations import create_request, decide_request
from mortgage_pricing.seed import (
    APPLICATIONS,
    RETIRED_USERS,
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


@pytest.fixture
def legacy_demo_database(
    migrated_database: tuple[Settings, sessionmaker[Session]],
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Settings, sessionmaker[Session]]:
    settings, _sessions = migrated_database
    legacy_applications = tuple(
        replace(application, manager_id=RETIRED_USERS[0].id)
        if "GRACE" in application.reference
        else application
        for application in APPLICATIONS
    )
    with monkeypatch.context() as previous_seeds:
        previous_seeds.setattr(
            "mortgage_pricing.seed.USERS", (USERS[0], RETIRED_USERS[0], USERS[1], RETIRED_USERS[1])
        )
        previous_seeds.setattr("mortgage_pricing.seed.APPLICATIONS", legacy_applications)
        previous_seeds.setattr("mortgage_pricing.seed.RETIRED_USERS", ())
        seed_database(settings)
    return migrated_database


def test_seed_consolidates_demo_users_and_preserves_existing_cases(
    legacy_demo_database: tuple[Settings, sessionmaker[Session]],
) -> None:
    settings, sessions = legacy_demo_database
    original = create_request(
        sessions,
        caller_id=USERS[0].id,
        application_id=APPLICATIONS[0].id,
        discount_bps=25,
        reason="Synthetic existing case preserved during demo consolidation.",
        idempotency_key="before-user-consolidation",
    )
    decide_request(
        sessions,
        reviewer_id=USERS[1].id,
        request_id=original.request_id,
        expected_version=1,
        outcome=DecisionOutcome.APPROVED,
    )
    protected_tables = [
        table
        for table in MortgageApplication.metadata.tables.values()
        if table.name not in {"users", "user_role_memberships", "mortgage_applications"}
    ]
    with sessions() as session:
        applications_before = session.execute(
            select(
                MortgageApplication.id,
                MortgageApplication.reference,
                MortgageApplication.created_at,
            ).order_by(MortgageApplication.id)
        ).all()
        history_before = {
            table.name: session.execute(table.select().order_by(*table.primary_key.columns)).all()
            for table in protected_tables
        }

    first = seed_database(settings)
    second = seed_database(settings)
    assert first.users_created == first.applications_created == 0
    assert second.users_created == second.applications_created == 0
    with sessions() as session:
        assert set(session.scalars(select(User.login))) == {user.login for user in USERS}
        assert count(session, UserRoleMembership) == 2
        assert set(session.scalars(select(MortgageApplication.manager_id))) == {USERS[0].id}
        assert (
            session.execute(
                select(
                    MortgageApplication.id,
                    MortgageApplication.reference,
                    MortgageApplication.created_at,
                ).order_by(MortgageApplication.id)
            ).all()
            == applications_before
        )
        for table in protected_tables:
            assert (
                session.execute(table.select().order_by(*table.primary_key.columns)).all()
                == history_before[table.name]
            )


@pytest.mark.parametrize("historical_actor", ["manager", "reviewer"])
def test_seed_refuses_to_remove_historical_actors_and_rolls_back(
    legacy_demo_database: tuple[Settings, sessionmaker[Session]], historical_actor: str
) -> None:
    settings, sessions = legacy_demo_database
    manager_history = historical_actor == "manager"
    original = create_request(
        sessions,
        caller_id=RETIRED_USERS[0].id if manager_history else USERS[0].id,
        application_id=APPLICATIONS[2 if manager_history else 0].id,
        discount_bps=25,
        reason="Synthetic historical actor must remain unchanged.",
        idempotency_key="historical-actor",
    )
    if not manager_history:
        decide_request(
            sessions,
            reviewer_id=RETIRED_USERS[1].id,
            request_id=original.request_id,
            expected_version=1,
            outcome=DecisionOutcome.APPROVED,
        )
    tables = MortgageApplication.metadata.tables.values()
    with sessions() as session:
        before = {
            table.name: session.execute(table.select().order_by(*table.primary_key.columns)).all()
            for table in tables
        }
    with pytest.raises(SeedConflictError, match="history must be preserved"):
        seed_database(settings)
    with sessions() as session:
        for table in tables:
            assert (
                session.execute(table.select().order_by(*table.primary_key.columns)).all()
                == before[table.name]
            )


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
        assert count(session, UserRoleMembership) == len(USERS)
        assert count(session, MortgageApplication) == len(APPLICATIONS)
        assert count(session, PricingRequest) == 0
        demo = session.get(MortgageApplication, APPLICATIONS[0].id)
        assert demo is not None
        assert demo.reference == "SYN-MORTGAGE-DEMO-CLEAN"


def test_expanding_existing_seeds_preserves_applications_and_approval_history(
    migrated_database: tuple[Settings, sessionmaker[Session]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings, sessions = migrated_database
    with monkeypatch.context() as previous_seeds:
        previous_seeds.setattr("mortgage_pricing.seed.APPLICATIONS", APPLICATIONS[:3])
        assert seed_database(settings).applications_created == 3

    original = create_request(
        sessions,
        caller_id=USERS[0].id,
        application_id=APPLICATIONS[1].id,
        discount_bps=25,
        reason="Synthetic approved request predating seed expansion.",
        idempotency_key="before-seed-expansion",
    )
    decide_request(
        sessions,
        reviewer_id=USERS[1].id,
        request_id=original.request_id,
        expected_version=1,
        outcome=DecisionOutcome.APPROVED,
    )
    tables = MortgageApplication.metadata.tables.values()
    with sessions() as session:
        original_rows = {table.name: session.execute(table.select()).all() for table in tables}

    expanded = seed_database(settings)
    repeated = seed_database(settings)
    assert expanded.users_created == 0
    assert expanded.applications_created == len(APPLICATIONS) - 3
    assert repeated.users_created == repeated.applications_created == 0
    with sessions() as session:
        assert count(session, MortgageApplication) == len(APPLICATIONS) >= 10
        for table in tables:
            current_rows = session.execute(table.select()).all()
            assert all(row in current_rows for row in original_rows[table.name]), table.name


def test_seed_backfills_application_financials_without_overwriting_saved_values(
    migrated_database: tuple[Settings, sessionmaker[Session]],
) -> None:
    settings, sessions = migrated_database
    seed_database(settings)
    with sessions.begin() as session:
        application = session.get_one(MortgageApplication, APPLICATIONS[0].id)
        application.loan_amount = Decimal("245123.45")
        application.property_value = None
        application.standard_rate_bps = 0
        application.term_months = None

    result = seed_database(settings)
    assert result.users_created == result.applications_created == 0
    with sessions() as session:
        application = session.get_one(MortgageApplication, APPLICATIONS[0].id)
        assert application.loan_amount == Decimal("245123.45")
        assert application.property_value == APPLICATIONS[0].property_value
        assert application.standard_rate_bps == 0
        assert application.term_months == APPLICATIONS[0].term_months
        for application in session.scalars(select(MortgageApplication)):
            assert application.loan_amount is not None
            assert application.property_value is not None
            assert application.standard_rate_bps is not None
            assert application.term_months is not None


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
