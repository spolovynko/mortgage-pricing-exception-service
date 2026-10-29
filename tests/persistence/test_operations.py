"""Atomic lifecycle behavior on separate temporary file-backed SQLite databases."""

from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from mortgage_pricing.config import Settings
from mortgage_pricing.persistence.base import Base
from mortgage_pricing.persistence.database import create_database_engine, create_session_factory
from mortgage_pricing.persistence.models import (
    CreationIdempotencyRecord,
    DecisionOutcome,
    MortgageApplication,
    PricingDecision,
    PricingRequest,
    RequestHistoryEvent,
    RequestVersion,
    Role,
    User,
    UserRoleMembership,
)
from mortgage_pricing.persistence.operations import (
    OperationError,
    create_request,
    decide_request,
    revise_request,
)


@pytest.fixture
def sessions(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = create_database_engine(
        Settings(
            _env_file=None, database_url=f"sqlite:///{(tmp_path / 'operations.db').as_posix()}"
        )
    )
    Base.metadata.create_all(engine)
    try:
        yield create_session_factory(engine)
    finally:
        engine.dispose()


def prepare(sessions: sessionmaker[Session], *, dual_role: bool = False) -> tuple[UUID, UUID, UUID]:
    with sessions.begin() as session:
        manager = User(login="manager.synthetic", display_name="Synthetic Manager")
        manager.role_memberships.append(UserRoleMembership(role=Role.RELATIONSHIP_MANAGER))
        if dual_role:
            manager.role_memberships.append(UserRoleMembership(role=Role.REVIEWER))
        reviewer = User(login="reviewer.synthetic", display_name="Synthetic Reviewer")
        reviewer.role_memberships.append(UserRoleMembership(role=Role.REVIEWER))
        session.add_all((manager, reviewer))
        session.flush()
        application = MortgageApplication(reference="SYN-001", manager_id=manager.id)
        session.add(application)
        session.flush()
        return manager.id, reviewer.id, application.id


def count(session: Session, model: type) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def test_create_replay_conflict_and_original_version(sessions: sessionmaker[Session]) -> None:
    manager, _, application = prepare(sessions)
    args = dict(
        caller_id=manager,
        application_id=application,
        discount_bps=25,
        reason="Synthetic offer",
        idempotency_key="retry-1",
    )
    first = create_request(sessions, **args)
    assert first.version_number == 1 and not first.replayed
    assert create_request(sessions, **args).request_id == first.request_id
    assert create_request(sessions, **args).replayed
    with pytest.raises(OperationError, match="idempotency_conflict"):
        create_request(sessions, **(args | {"discount_bps": 40}))
    with pytest.raises(OperationError, match="request_exists"):
        create_request(sessions, **(args | {"idempotency_key": "retry-2"}))
    revised = revise_request(
        sessions,
        caller_id=manager,
        request_id=first.request_id,
        expected_version=1,
        discount_bps=40,
        reason="Revised synthetic offer",
    )
    assert revised.version_number == 2
    assert create_request(sessions, **args).version_number == 1
    with sessions() as session:
        assert [
            count(session, model)
            for model in (
                PricingRequest,
                RequestVersion,
                RequestHistoryEvent,
                CreationIdempotencyRecord,
            )
        ] == [1, 2, 2, 1]
        assert session.get(PricingRequest, first.request_id).current_version_number == 2
        assert session.get(RequestVersion, (first.request_id, 1)).discount_bps == 25


def test_decision_and_stale_or_duplicate_attempts(sessions: sessionmaker[Session]) -> None:
    manager, reviewer, application = prepare(sessions)
    created = create_request(
        sessions,
        caller_id=manager,
        application_id=application,
        discount_bps=25,
        reason="Synthetic",
        idempotency_key="key",
    )
    decide_request(
        sessions,
        reviewer_id=reviewer,
        request_id=created.request_id,
        expected_version=1,
        outcome=DecisionOutcome.APPROVED,
    )
    with pytest.raises(OperationError, match="already_decided"):
        decide_request(
            sessions,
            reviewer_id=reviewer,
            request_id=created.request_id,
            expected_version=1,
            outcome=DecisionOutcome.DECLINED,
        )
    revise_request(
        sessions,
        caller_id=manager,
        request_id=created.request_id,
        expected_version=1,
        discount_bps=40,
        reason="Changed",
    )
    with pytest.raises(OperationError, match="stale_version"):
        decide_request(
            sessions,
            reviewer_id=reviewer,
            request_id=created.request_id,
            expected_version=1,
            outcome=DecisionOutcome.DECLINED,
        )
    with pytest.raises(OperationError, match="stale_version"):
        revise_request(
            sessions,
            caller_id=manager,
            request_id=created.request_id,
            expected_version=1,
            discount_bps=50,
            reason="Changed again",
        )
    with sessions() as session:
        assert count(session, PricingDecision) == 1
        assert count(session, RequestHistoryEvent) == 3
        assert session.get(RequestVersion, (created.request_id, 1)).discount_bps == 25
        assert session.get(RequestVersion, (created.request_id, 2)).discount_bps == 40


def test_permissions_and_self_review(sessions: sessionmaker[Session]) -> None:
    manager, reviewer, application = prepare(sessions, dual_role=True)
    with pytest.raises(OperationError, match="forbidden"):
        create_request(
            sessions,
            caller_id=reviewer,
            application_id=application,
            discount_bps=25,
            reason="Synthetic",
            idempotency_key="key",
        )
    created = create_request(
        sessions,
        caller_id=manager,
        application_id=application,
        discount_bps=25,
        reason="Synthetic",
        idempotency_key="key",
    )
    with pytest.raises(OperationError, match="self_review"):
        decide_request(
            sessions,
            reviewer_id=manager,
            request_id=created.request_id,
            expected_version=1,
            outcome=DecisionOutcome.APPROVED,
        )
    with pytest.raises(OperationError, match="forbidden"):
        revise_request(
            sessions,
            caller_id=reviewer,
            request_id=created.request_id,
            expected_version=1,
            discount_bps=50,
            reason="Unauthorized",
        )
    with sessions() as session:
        assert count(session, PricingDecision) == 0
        assert count(session, RequestHistoryEvent) == 1


def test_failed_create_rolls_back_all_rows(sessions: sessionmaker[Session]) -> None:
    manager, _, application = prepare(sessions)
    # The event's actor FK fails at commit, after request/version/record are staged.
    from sqlalchemy import event

    @event.listens_for(Session, "before_flush")
    def corrupt_history_actor(session: Session, *_args: object) -> None:
        for obj in session.new:
            if isinstance(obj, RequestHistoryEvent):
                obj.actor_id = UUID(int=0)

    try:
        with pytest.raises(IntegrityError):
            create_request(
                sessions,
                caller_id=manager,
                application_id=application,
                discount_bps=25,
                reason="Synthetic",
                idempotency_key="key",
            )
    finally:
        event.remove(Session, "before_flush", corrupt_history_actor)
    with sessions() as session:
        assert [
            count(session, model)
            for model in (
                PricingRequest,
                RequestVersion,
                RequestHistoryEvent,
                CreationIdempotencyRecord,
            )
        ] == [0, 0, 0, 0]


def test_failed_decision_history_rolls_back_decision(sessions: sessionmaker[Session]) -> None:
    manager, reviewer, application = prepare(sessions)
    created = create_request(
        sessions,
        caller_id=manager,
        application_id=application,
        discount_bps=25,
        reason="Synthetic",
        idempotency_key="key",
    )
    from sqlalchemy import event

    @event.listens_for(Session, "before_flush")
    def corrupt_decision_history(session: Session, *_args: object) -> None:
        for obj in session.new:
            if isinstance(obj, RequestHistoryEvent) and obj.event_type == "approved":
                obj.actor_id = UUID(int=0)

    try:
        with pytest.raises(IntegrityError):
            decide_request(
                sessions,
                reviewer_id=reviewer,
                request_id=created.request_id,
                expected_version=1,
                outcome=DecisionOutcome.APPROVED,
            )
    finally:
        event.remove(Session, "before_flush", corrupt_decision_history)
    with sessions() as session:
        assert count(session, PricingDecision) == 0
        assert count(session, RequestHistoryEvent) == 1


def test_two_connections_serialized_creation(sessions: sessionmaker[Session]) -> None:
    manager, _, application = prepare(sessions)
    with sessions.begin() as blocker:
        blocker.execute(
            MortgageApplication.__table__.update()
            .where(MortgageApplication.id == application)
            .values(reference=MortgageApplication.reference)
        )
        # A competing writer cannot pass the first write and read stale state.
        from sqlalchemy.exc import OperationalError

        with pytest.raises(OperationalError):
            create_request(
                sessions,
                caller_id=manager,
                application_id=application,
                discount_bps=25,
                reason="Synthetic",
                idempotency_key="key",
            )
    result = create_request(
        sessions,
        caller_id=manager,
        application_id=application,
        discount_bps=25,
        reason="Synthetic",
        idempotency_key="key",
    )
    assert result.version_number == 1


def test_competing_decisions_commit_once(sessions: sessionmaker[Session]) -> None:
    manager, reviewer, application = prepare(sessions)
    created = create_request(
        sessions,
        caller_id=manager,
        application_id=application,
        discount_bps=25,
        reason="Synthetic",
        idempotency_key="key",
    )

    def decide(outcome: DecisionOutcome) -> str:
        try:
            decide_request(
                sessions,
                reviewer_id=reviewer,
                request_id=created.request_id,
                expected_version=1,
                outcome=outcome,
            )
            return "committed"
        except OperationError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(decide, (DecisionOutcome.APPROVED, DecisionOutcome.DECLINED)))
    assert sorted(results) == ["already_decided", "committed"]
    with sessions() as session:
        assert count(session, PricingDecision) == 1
        assert count(session, RequestHistoryEvent) == 2


def test_competing_revisions_commit_once(sessions: sessionmaker[Session]) -> None:
    manager, _, application = prepare(sessions)
    created = create_request(
        sessions,
        caller_id=manager,
        application_id=application,
        discount_bps=25,
        reason="Synthetic",
        idempotency_key="key",
    )

    def revise(discount: int) -> str:
        try:
            revise_request(
                sessions,
                caller_id=manager,
                request_id=created.request_id,
                expected_version=1,
                discount_bps=discount,
                reason="Revised",
            )
            return "committed"
        except OperationError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(revise, (40, 50)))
    assert sorted(results) == ["committed", "stale_version"]
    with sessions() as session:
        assert count(session, RequestVersion) == 2
        assert count(session, RequestHistoryEvent) == 2
