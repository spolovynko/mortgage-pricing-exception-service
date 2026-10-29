"""Initial Alembic schema migration on isolated file-backed SQLite databases."""

import json
from collections.abc import Iterator
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from mortgage_pricing.config import Settings
from mortgage_pricing.persistence.database import create_database_engine, create_session_factory
from mortgage_pricing.persistence.models import (
    CreationIdempotencyRecord,
    DecisionOutcome,
    PricingDecision,
    RequestHistoryEvent,
    RequestVersion,
)
from mortgage_pricing.persistence.operations import create_request, decide_request
from mortgage_pricing.seed import APPLICATIONS, seed_database
from tests.persistence.test_operations import prepare

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def migrated_database(tmp_path: Path) -> Iterator[tuple[Settings, Engine, sessionmaker[Session]]]:
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'migrated.db').as_posix()}",
    )
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["settings"] = settings
    command.upgrade(config, "head")
    engine = create_database_engine(settings)
    try:
        yield settings, engine, create_session_factory(engine)
    finally:
        engine.dispose()


def test_upgrade_creates_schema_and_second_run_preserves_rows(
    migrated_database: tuple[Settings, Engine, sessionmaker[Session]],
) -> None:
    settings, engine, sessions = migrated_database
    expected_tables = {
        "alembic_version",
        "users",
        "user_role_memberships",
        "mortgage_applications",
        "pricing_requests",
        "request_versions",
        "pricing_decisions",
        "request_history_events",
        "creation_idempotency_records",
    }
    assert expected_tables <= set(inspect(engine).get_table_names())
    manager, _, application = prepare(sessions)
    created = create_request(
        sessions,
        caller_id=manager,
        application_id=application,
        discount_bps=25,
        reason="Synthetic migrated terms",
        idempotency_key="migrated-key",
    )
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["settings"] = settings
    command.upgrade(config, "head")
    with sessions() as session:
        assert session.get(CreationIdempotencyRecord, (manager, "migrated-key")) is not None
        assert created.request_id is not None


def test_context_migration_preserves_existing_request_versions(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'legacy-context.db').as_posix()}",
    )
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["settings"] = settings
    command.upgrade(config, "20261029_0001")
    seed_database(settings)

    request_id = uuid4()
    engine = create_database_engine(settings)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO pricing_requests "
                "(id, application_id, current_version_number, created_at) "
                "VALUES (:id, :application_id, NULL, '2026-10-29 00:00:00.000000')"
            ),
            {"id": request_id.hex, "application_id": APPLICATIONS[0].id.hex},
        )
        connection.execute(
            text(
                "INSERT INTO request_versions "
                "(request_id, version_number, discount_bps, reason, submitted_by_id, submitted_at) "
                "VALUES (:request_id, 1, 25, 'Legacy request', :manager_id, "
                "'2026-10-29 00:00:00.000000')"
            ),
            {"request_id": request_id.hex, "manager_id": APPLICATIONS[0].manager_id.hex},
        )
        connection.execute(
            text("UPDATE pricing_requests SET current_version_number = 1 WHERE id = :id"),
            {"id": request_id.hex},
        )
        canonical = json.dumps(
            {
                "application_id": str(APPLICATIONS[0].id),
                "discount_bps": 25,
                "reason": "Legacy request",
            },
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        connection.execute(
            text(
                "INSERT INTO creation_idempotency_records "
                "(caller_id, key, input_fingerprint, request_id, version_number, created_at) "
                "VALUES (:caller_id, 'legacy-key', :fingerprint, :request_id, 1, "
                "'2026-10-29 00:00:00.000000')"
            ),
            {
                "caller_id": APPLICATIONS[0].manager_id.hex,
                "fingerprint": sha256(canonical.encode("utf-8")).hexdigest(),
                "request_id": request_id.hex,
            },
        )
    engine.dispose()

    command.upgrade(config, "head")
    upgraded_engine = create_database_engine(settings)
    try:
        with create_session_factory(upgraded_engine)() as session:
            legacy_version = session.get(RequestVersion, (request_id, 1))
            assert legacy_version is not None
            assert legacy_version.reason == "Legacy request"
            assert legacy_version.context is None
        replay = create_request(
            create_session_factory(upgraded_engine),
            caller_id=APPLICATIONS[0].manager_id,
            application_id=APPLICATIONS[0].id,
            discount_bps=25,
            reason="Legacy request",
            idempotency_key="legacy-key",
        )
        assert replay.request_id == request_id and replay.replayed
    finally:
        upgraded_engine.dispose()


def test_migration_enforces_foreign_keys_and_direct_sql_immutability(
    migrated_database: tuple[Settings, Engine, sessionmaker[Session]],
) -> None:
    _, engine, sessions = migrated_database
    manager, reviewer, application = prepare(sessions)
    created = create_request(
        sessions,
        caller_id=manager,
        application_id=application,
        discount_bps=25,
        reason="Synthetic migrated terms",
        idempotency_key="migrated-key",
    )
    decide_request(
        sessions,
        reviewer_id=reviewer,
        request_id=created.request_id,
        expected_version=1,
        outcome=DecisionOutcome.APPROVED,
    )
    with sessions() as session:
        decision_id = session.scalar(select(PricingDecision.id))
        history_id = session.scalar(
            select(RequestHistoryEvent.id).where(RequestHistoryEvent.event_type == "approved")
        )
    assert decision_id is not None and history_id is not None

    statements = (
        (
            "request_versions",
            "UPDATE request_versions SET discount_bps = 99, context = '{}' "
            "WHERE request_id = :request_id",
            {"request_id": created.request_id.hex},
            "DELETE FROM request_versions WHERE request_id = :request_id",
        ),
        (
            "pricing_decisions",
            "UPDATE pricing_decisions SET outcome = 'declined' WHERE id = :id",
            {"id": decision_id.hex},
            "DELETE FROM pricing_decisions WHERE id = :id",
        ),
        (
            "request_history_events",
            "UPDATE request_history_events SET event_type = 'revised' WHERE id = :id",
            {"id": history_id.hex},
            "DELETE FROM request_history_events WHERE id = :id",
        ),
        (
            "creation_idempotency_records",
            "UPDATE creation_idempotency_records SET input_fingerprint = :fingerprint "
            "WHERE caller_id = :caller_id",
            {"fingerprint": "b" * 64, "caller_id": manager.hex},
            "DELETE FROM creation_idempotency_records WHERE caller_id = :caller_id",
        ),
    )
    for table, update_sql, parameters, delete_sql in statements:
        with (
            pytest.raises(IntegrityError, match=f"{table} is immutable"),
            engine.begin() as connection,
        ):
            connection.execute(text(update_sql), parameters)
        with (
            pytest.raises(IntegrityError, match=f"{table} is immutable"),
            engine.begin() as connection,
        ):
            connection.execute(text(delete_sql), parameters)

    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO pricing_requests (id, application_id, created_at) "
                "VALUES (:id, :app, :at)"
            ),
            {"id": UUID(int=0).hex, "app": UUID(int=1).hex, "at": "2026-10-29 00:00:00"},
        )


def test_downgrade_and_upgrade_work_on_an_isolated_database(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'downgrade.db').as_posix()}",
    )
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["settings"] = settings
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    engine = create_database_engine(settings)
    try:
        assert inspect(engine).get_table_names() == ["alembic_version"]
    finally:
        engine.dispose()
    command.upgrade(config, "head")
