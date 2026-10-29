"""Logical request and submitted-version guarantees on temporary SQLite files."""

from collections.abc import Iterator
from datetime import UTC
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import Engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from mortgage_pricing.config import Settings
from mortgage_pricing.persistence.base import Base
from mortgage_pricing.persistence.database import create_database_engine
from mortgage_pricing.persistence.models import (
    MortgageApplication,
    PricingRequest,
    RequestVersion,
    Role,
    User,
    UserRoleMembership,
)


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    database_engine = create_database_engine(
        Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'versions.db').as_posix()}")
    )
    Base.metadata.create_all(database_engine)
    try:
        yield database_engine
    finally:
        database_engine.dispose()


@pytest.fixture
def sessions(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine)


def add_application(session: Session, reference: str) -> tuple[User, MortgageApplication]:
    manager = User(login=f"manager.{reference}", display_name="Synthetic Manager")
    manager.role_memberships.append(UserRoleMembership(role=Role.RELATIONSHIP_MANAGER))
    session.add(manager)
    session.flush()
    application = MortgageApplication(reference=reference, manager=manager)
    session.add(application)
    session.flush()
    return manager, application


def add_request(session: Session, reference: str) -> tuple[PricingRequest, User]:
    manager, application = add_application(session, reference)
    request = PricingRequest(application=application)
    session.add(request)
    session.flush()
    return request, manager


def test_versions_preserve_terms_and_current_pointer(sessions: sessionmaker[Session]) -> None:
    with sessions.begin() as session:
        request, manager = add_request(session, "MORT-SYN-1")
        request.versions.append(
            RequestVersion(
                version_number=1,
                discount_bps=25,
                reason="Synthetic initial terms",
                submitted_by=manager,
            )
        )
        session.flush()
        request.current_version_number = 1
        request_id = request.id

    with sessions.begin() as session:
        request = session.get(PricingRequest, request_id)
        assert request is not None
        manager = session.scalar(select(User).where(User.login == "manager.MORT-SYN-1"))
        assert manager is not None
        request.versions.append(
            RequestVersion(
                version_number=2,
                discount_bps=40,
                reason="Synthetic revised terms",
                submitted_by=manager,
            )
        )
        session.flush()
        request.current_version_number = 2

    with sessions() as session:
        request = session.get(PricingRequest, request_id)
        assert request is not None
        assert request.current_version_number == 2
        assert [(v.version_number, v.discount_bps, v.reason) for v in request.versions] == [
            (1, 25, "Synthetic initial terms"),
            (2, 40, "Synthetic revised terms"),
        ]
        assert all(v.submitted_at.tzinfo == UTC for v in request.versions)
        assert request.versions[0].submitted_by.login == "manager.MORT-SYN-1"


def test_one_request_per_application_and_unique_version_numbers(
    sessions: sessionmaker[Session],
) -> None:
    with sessions.begin() as session:
        request, manager = add_request(session, "MORT-SYN-1")
        request.versions.append(
            RequestVersion(version_number=1, discount_bps=25, reason="First", submitted_by=manager)
        )
        request_id = request.id
        application_id = request.application_id
        manager_id = manager.id

    with pytest.raises(IntegrityError), sessions.begin() as session:
        session.add(PricingRequest(application_id=application_id))

    with pytest.raises(IntegrityError), sessions.begin() as session:
        session.add(
            RequestVersion(
                request_id=request_id,
                version_number=1,
                discount_bps=30,
                reason="Duplicate number",
                submitted_by_id=manager_id,
            )
        )


def test_current_version_must_belong_to_same_request(sessions: sessionmaker[Session]) -> None:
    with sessions.begin() as session:
        first, manager = add_request(session, "MORT-SYN-1")
        second, _ = add_request(session, "MORT-SYN-2")
        first.versions.append(
            RequestVersion(version_number=1, discount_bps=25, reason="First", submitted_by=manager)
        )
        first_id = first.id
        second_id = second.id

    with pytest.raises(IntegrityError), sessions.begin() as session:
        second = session.get(PricingRequest, second_id)
        assert second is not None
        second.current_version_number = 1

    with pytest.raises(IntegrityError), sessions.begin() as session:
        first = session.get(PricingRequest, first_id)
        assert first is not None
        first.current_version_number = 2


@pytest.mark.parametrize(
    ("number", "discount", "reason"),
    [
        (0, 25, "Valid"),
        (1, 0, "Valid"),
        (1, -5, "Valid"),
        (1, 25, "   "),
        (1, 25, "x" * 2001),
    ],
)
def test_database_rejects_invalid_submitted_terms(
    sessions: sessionmaker[Session], number: int, discount: int, reason: str
) -> None:
    with pytest.raises(IntegrityError), sessions.begin() as session:
        request, manager = add_request(session, "MORT-SYN-1")
        request.versions.append(
            RequestVersion(
                version_number=number,
                discount_bps=discount,
                reason=reason,
                submitted_by=manager,
            )
        )


def test_submitted_actor_must_exist(sessions: sessionmaker[Session]) -> None:
    with pytest.raises(IntegrityError), sessions.begin() as session:
        request, _ = add_request(session, "MORT-SYN-1")
        request.versions.append(
            RequestVersion(
                version_number=1,
                discount_bps=25,
                reason="Synthetic",
                submitted_by_id=uuid4(),
            )
        )


def test_orm_rejects_edits_and_deletion_of_submitted_version(
    sessions: sessionmaker[Session],
) -> None:
    with sessions.begin() as session:
        request, manager = add_request(session, "MORT-SYN-1")
        request.versions.append(
            RequestVersion(version_number=1, discount_bps=25, reason="First", submitted_by=manager)
        )
        request_id = request.id

    with pytest.raises(ValueError, match="cannot be changed"), sessions.begin() as session:
        version = session.get(RequestVersion, (request_id, 1))
        assert version is not None
        version.discount_bps = 40

    with pytest.raises(ValueError, match="cannot be changed"), sessions.begin() as session:
        version = session.get(RequestVersion, (request_id, 1))
        assert version is not None
        session.delete(version)

    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(RequestVersion)) == 1
        version = session.get(RequestVersion, (request_id, 1))
        assert version is not None and version.discount_bps == 25
