"""Decision and history constraints against isolated file-backed SQLite."""

from collections.abc import Iterator
from datetime import UTC
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from mortgage_pricing.config import Settings
from mortgage_pricing.persistence.base import Base
from mortgage_pricing.persistence.database import create_database_engine
from mortgage_pricing.persistence.models import (
    DecisionOutcome,
    HistoryEventType,
    MortgageApplication,
    PricingDecision,
    PricingRequest,
    RequestHistoryEvent,
    RequestVersion,
    Role,
    User,
    UserRoleMembership,
)


@pytest.fixture
def sessions(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = create_database_engine(
        Settings(_env_file=None, database_url=f"sqlite:///{(tmp_path / 'decisions.db').as_posix()}")
    )
    Base.metadata.create_all(engine)
    try:
        yield sessionmaker(bind=engine)
    finally:
        engine.dispose()


def prepared_request(sessions: sessionmaker[Session]) -> tuple[UUID, UUID, UUID]:
    with sessions.begin() as session:
        manager = User(login="manager.synthetic", display_name="Synthetic Manager")
        manager.role_memberships.append(UserRoleMembership(role=Role.RELATIONSHIP_MANAGER))
        reviewer = User(login="reviewer.synthetic", display_name="Synthetic Reviewer")
        reviewer.role_memberships.append(UserRoleMembership(role=Role.REVIEWER))
        session.add_all((manager, reviewer))
        session.flush()
        application = MortgageApplication(reference="MORT-SYN-1", manager=manager)
        session.add(application)
        session.flush()
        request = PricingRequest(application=application)
        session.add(request)
        session.flush()
        version = RequestVersion(
            request=request,
            version_number=1,
            discount_bps=25,
            reason="Synthetic terms",
            submitted_by=manager,
        )
        session.add(version)
        session.flush()
        request.current_version_number = 1
        return request.id, manager.id, reviewer.id


def test_decision_and_history_preserve_exact_version_and_actor(
    sessions: sessionmaker[Session],
) -> None:
    request_id, manager_id, reviewer_id = prepared_request(sessions)
    with sessions.begin() as session:
        session.add_all(
            (
                RequestHistoryEvent(
                    request_id=request_id,
                    version_number=1,
                    event_type=HistoryEventType.CREATED,
                    actor_id=manager_id,
                ),
                PricingDecision(
                    request_id=request_id,
                    version_number=1,
                    outcome=DecisionOutcome.APPROVED,
                    reviewer_id=reviewer_id,
                ),
                RequestHistoryEvent(
                    request_id=request_id,
                    version_number=1,
                    event_type=HistoryEventType.APPROVED,
                    actor_id=reviewer_id,
                ),
            )
        )

    with sessions() as session:
        decision = session.scalar(select(PricingDecision))
        assert decision is not None
        assert decision.version.discount_bps == 25
        assert decision.reviewer.login == "reviewer.synthetic"
        assert decision.decided_at.tzinfo == UTC
        events = session.scalars(
            select(RequestHistoryEvent).order_by(RequestHistoryEvent.occurred_at)
        ).all()
        assert [event.event_type for event in events] == [
            HistoryEventType.CREATED,
            HistoryEventType.APPROVED,
        ]
        assert [event.actor_id for event in events] == [manager_id, reviewer_id]
        assert all(event.version.version_number == 1 for event in events)
        assert all(event.occurred_at.tzinfo == UTC for event in events)


def test_database_rejects_second_decision_for_same_version(sessions: sessionmaker[Session]) -> None:
    request_id, _, reviewer_id = prepared_request(sessions)
    with sessions.begin() as session:
        session.add(
            PricingDecision(
                request_id=request_id,
                version_number=1,
                outcome=DecisionOutcome.DECLINED,
                reviewer_id=reviewer_id,
            )
        )
    with pytest.raises(IntegrityError), sessions.begin() as session:
        session.add(
            PricingDecision(
                request_id=request_id,
                version_number=1,
                outcome=DecisionOutcome.APPROVED,
                reviewer_id=reviewer_id,
            )
        )


@pytest.mark.parametrize("record", ["decision", "history"])
def test_database_rejects_missing_version(sessions: sessionmaker[Session], record: str) -> None:
    request_id, manager_id, reviewer_id = prepared_request(sessions)
    with pytest.raises(IntegrityError), sessions.begin() as session:
        if record == "decision":
            session.add(
                PricingDecision(
                    request_id=request_id,
                    version_number=2,
                    outcome=DecisionOutcome.APPROVED,
                    reviewer_id=reviewer_id,
                )
            )
        else:
            session.add(
                RequestHistoryEvent(
                    request_id=request_id,
                    version_number=2,
                    event_type=HistoryEventType.REVISED,
                    actor_id=manager_id,
                )
            )


def test_database_requires_reviewer_membership(sessions: sessionmaker[Session]) -> None:
    request_id, manager_id, _ = prepared_request(sessions)
    with pytest.raises(IntegrityError), sessions.begin() as session:
        session.add(
            PricingDecision(
                request_id=request_id,
                version_number=1,
                outcome=DecisionOutcome.APPROVED,
                reviewer_id=manager_id,
            )
        )


@pytest.mark.parametrize("record", ["decision", "history"])
def test_orm_rejects_update_and_delete(sessions: sessionmaker[Session], record: str) -> None:
    request_id, manager_id, reviewer_id = prepared_request(sessions)
    with sessions.begin() as session:
        if record == "decision":
            item = PricingDecision(
                request_id=request_id,
                version_number=1,
                outcome=DecisionOutcome.APPROVED,
                reviewer_id=reviewer_id,
            )
        else:
            item = RequestHistoryEvent(
                request_id=request_id,
                version_number=1,
                event_type=HistoryEventType.CREATED,
                actor_id=manager_id,
            )
        session.add(item)
        session.flush()
        item_id = item.id

    model = PricingDecision if record == "decision" else RequestHistoryEvent
    with pytest.raises(ValueError, match="cannot be changed"), sessions.begin() as session:
        item = session.get(model, item_id)
        assert item is not None
        if isinstance(item, PricingDecision):
            item.outcome = DecisionOutcome.DECLINED
        else:
            item.event_type = HistoryEventType.REVISED

    with pytest.raises(ValueError, match="cannot be changed"), sessions.begin() as session:
        item = session.get(model, item_id)
        assert item is not None
        session.delete(item)

    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(model)) == 1
