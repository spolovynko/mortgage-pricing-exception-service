"""Business model constraints tested against isolated file-backed SQLite."""

from collections.abc import Iterator
from datetime import UTC
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from mortgage_pricing.config import Settings
from mortgage_pricing.persistence.base import Base
from mortgage_pricing.persistence.database import create_database_engine
from mortgage_pricing.persistence.models import MortgageApplication, Role, User, UserRoleMembership


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    database_engine = create_database_engine(
        Settings(
            _env_file=None,
            database_url=f"sqlite:///{(tmp_path / 'models.db').as_posix()}",
        )
    )
    Base.metadata.create_all(database_engine)
    try:
        yield database_engine
    finally:
        database_engine.dispose()


@pytest.fixture
def sessions(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine)


def create_manager(session: Session, login: str = "manager.ada") -> User:
    manager = User(login=login, display_name="Ada Manager")
    manager.role_memberships.append(UserRoleMembership(role=Role.RELATIONSHIP_MANAGER))
    session.add(manager)
    session.flush()
    return manager


def test_persists_user_memberships_and_manager_ownership(sessions: sessionmaker[Session]) -> None:
    with sessions.begin() as session:
        manager = create_manager(session)
        manager.role_memberships.append(UserRoleMembership(role=Role.REVIEWER))
        application = MortgageApplication(reference="MORT-SYNTHETIC-001", manager=manager)
        session.add(application)

    with sessions() as session:
        stored = session.scalar(
            select(MortgageApplication).where(MortgageApplication.reference == "MORT-SYNTHETIC-001")
        )
        assert stored is not None
        assert stored.manager.login == "manager.ada"
        assert {membership.role for membership in stored.manager.role_memberships} == {
            Role.RELATIONSHIP_MANAGER,
            Role.REVIEWER,
        }
        assert stored.created_at.tzinfo == UTC


def test_rejects_duplicate_login_reference_and_role_membership(
    sessions: sessionmaker[Session],
) -> None:
    with sessions.begin() as session:
        manager = create_manager(session)
        session.add(MortgageApplication(reference="MORT-SYNTHETIC-001", manager=manager))

    with pytest.raises(IntegrityError), sessions.begin() as session:
        session.add(User(login="manager.ada", display_name="Duplicate Manager"))

    with pytest.raises(IntegrityError), sessions.begin() as session:
        manager = session.scalar(select(User).where(User.login == "manager.ada"))
        assert manager is not None
        session.add(MortgageApplication(reference="MORT-SYNTHETIC-001", manager=manager))

    with pytest.raises(IntegrityError), sessions.begin() as session:
        manager = session.scalar(select(User).where(User.login == "manager.ada"))
        assert manager is not None
        session.add(UserRoleMembership(user=manager, role=Role.RELATIONSHIP_MANAGER))


def test_rejects_missing_or_reviewer_only_manager_and_invalid_role(
    sessions: sessionmaker[Session],
) -> None:
    with pytest.raises(IntegrityError), sessions.begin() as session:
        session.add(
            MortgageApplication(
                reference="MORT-SYNTHETIC-404",
                manager_id=uuid4(),
            )
        )

    with pytest.raises(IntegrityError), sessions.begin() as session:
        reviewer = User(login="reviewer.ben", display_name="Ben Reviewer")
        reviewer.role_memberships.append(UserRoleMembership(role=Role.REVIEWER))
        session.add(MortgageApplication(reference="MORT-SYNTHETIC-REVIEWER", manager=reviewer))

    with pytest.raises(IntegrityError), sessions.begin() as session:
        user = User(login="reviewer.ben", display_name="Ben Reviewer")
        session.add(user)
        session.flush()
        session.connection().exec_driver_sql(
            "INSERT INTO user_role_memberships (user_id, role) VALUES (?, ?)",
            (user.id.hex, "unrecognised_role"),
        )


@pytest.mark.parametrize(
    ("login", "display_name", "reference"),
    [
        ("", "Ada Manager", "MORT-SYNTHETIC-001"),
        ("manager.ada", "", "MORT-SYNTHETIC-001"),
        ("manager.ada", "Ada Manager", ""),
    ],
)
def test_rejects_blank_business_identifiers(
    sessions: sessionmaker[Session], login: str, display_name: str, reference: str
) -> None:
    with pytest.raises(IntegrityError), sessions.begin() as session:
        manager = User(login=login, display_name=display_name)
        session.add(manager)
        session.flush()
        session.add(MortgageApplication(reference=reference, manager=manager))
