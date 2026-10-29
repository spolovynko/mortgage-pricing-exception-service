"""Caller-scoped creation retry records on isolated file-backed SQLite."""

from collections.abc import Iterator
from datetime import UTC
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from mortgage_pricing.config import Settings
from mortgage_pricing.persistence.base import Base
from mortgage_pricing.persistence.database import create_database_engine
from mortgage_pricing.persistence.models import (
    CreationIdempotencyRecord,
    MortgageApplication,
    PricingRequest,
    RequestVersion,
    Role,
    User,
    UserRoleMembership,
)


@pytest.fixture
def sessions(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = create_database_engine(
        Settings(
            _env_file=None, database_url=f"sqlite:///{(tmp_path / 'idempotency.db').as_posix()}"
        )
    )
    Base.metadata.create_all(engine)
    try:
        yield sessionmaker(bind=engine)
    finally:
        engine.dispose()


def prepare(sessions: sessionmaker[Session]) -> tuple[UUID, UUID, UUID]:
    with sessions.begin() as session:
        first = User(login="manager.first", display_name="First Manager")
        second = User(login="manager.second", display_name="Second Manager")
        for manager in (first, second):
            manager.role_memberships.append(UserRoleMembership(role=Role.RELATIONSHIP_MANAGER))
            session.add(manager)
        session.flush()
        application = MortgageApplication(reference="MORT-SYN-1", manager=first)
        session.add(application)
        session.flush()
        request = PricingRequest(application=application)
        session.add(request)
        session.flush()
        session.add(
            RequestVersion(
                request=request,
                version_number=1,
                discount_bps=25,
                reason="Synthetic terms",
                submitted_by=first,
            )
        )
        session.flush()
        request.current_version_number = 1
        return first.id, second.id, request.id


def record(caller_id: UUID, request_id: UUID, *, key: str = "retry-1") -> CreationIdempotencyRecord:
    return CreationIdempotencyRecord(
        caller_id=caller_id,
        key=key,
        input_fingerprint="a" * 64,
        request_id=request_id,
        version_number=1,
    )


def test_same_key_is_scoped_to_caller_and_preserves_original_reference(
    sessions: sessionmaker[Session],
) -> None:
    first_id, second_id, request_id = prepare(sessions)
    with sessions.begin() as session:
        session.add_all((record(first_id, request_id), record(second_id, request_id)))

    with sessions() as session:
        rows = session.scalars(
            select(CreationIdempotencyRecord).order_by(CreationIdempotencyRecord.caller_id)
        ).all()
        assert len(rows) == 2
        assert {row.caller_id for row in rows} == {first_id, second_id}
        assert all(row.key == "retry-1" and row.input_fingerprint == "a" * 64 for row in rows)
        assert all(row.original_version.discount_bps == 25 for row in rows)
        assert all(row.created_at.tzinfo == UTC for row in rows)


def test_duplicate_caller_key_is_rejected_even_with_new_fingerprint(
    sessions: sessionmaker[Session],
) -> None:
    first_id, _, request_id = prepare(sessions)
    with sessions.begin() as session:
        session.add(record(first_id, request_id))

    with pytest.raises(IntegrityError), sessions.begin() as session:
        duplicate = record(first_id, request_id)
        duplicate.input_fingerprint = "b" * 64
        session.add(duplicate)

    with sessions() as session:
        existing = session.get(CreationIdempotencyRecord, (first_id, "retry-1"))
        assert existing is not None and existing.input_fingerprint == "a" * 64


@pytest.mark.parametrize("invalid", ["", "   ", "x" * 129])
def test_rejects_invalid_key(sessions: sessionmaker[Session], invalid: str) -> None:
    first_id, _, request_id = prepare(sessions)
    with pytest.raises(IntegrityError), sessions.begin() as session:
        session.add(record(first_id, request_id, key=invalid))


@pytest.mark.parametrize("invalid", ["short", "G" * 64, "z" * 64])
def test_rejects_invalid_fingerprint(sessions: sessionmaker[Session], invalid: str) -> None:
    first_id, _, request_id = prepare(sessions)
    with pytest.raises(IntegrityError), sessions.begin() as session:
        value = record(first_id, request_id)
        value.input_fingerprint = invalid
        session.add(value)


@pytest.mark.parametrize("missing", ["caller", "request", "version"])
def test_rejects_missing_references(sessions: sessionmaker[Session], missing: str) -> None:
    first_id, _, request_id = prepare(sessions)
    value = record(first_id, request_id)
    if missing == "caller":
        value.caller_id = uuid4()
    elif missing == "request":
        value.request_id = uuid4()
    else:
        value.version_number = 2
    with pytest.raises(IntegrityError), sessions.begin() as session:
        session.add(value)


def test_original_mapping_cannot_change_through_orm(sessions: sessionmaker[Session]) -> None:
    first_id, _, request_id = prepare(sessions)
    with sessions.begin() as session:
        session.add(record(first_id, request_id))

    with pytest.raises(ValueError, match="cannot be changed"), sessions.begin() as session:
        value = session.get(CreationIdempotencyRecord, (first_id, "retry-1"))
        assert value is not None
        value.input_fingerprint = "b" * 64

    with pytest.raises(ValueError, match="cannot be changed"), sessions.begin() as session:
        value = session.get(CreationIdempotencyRecord, (first_id, "retry-1"))
        assert value is not None
        session.delete(value)

    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(CreationIdempotencyRecord)) == 1
