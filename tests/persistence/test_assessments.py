"""Assessment snapshots and stale-result protection."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker

from mortgage_pricing.config import Settings
from mortgage_pricing.persistence.base import Base
from mortgage_pricing.persistence.database import create_database_engine, create_session_factory
from mortgage_pricing.persistence.models import AssessmentStatus, PricingAssessment
from mortgage_pricing.persistence.operations import (
    OperationError,
    capture_assessment_snapshot,
    store_assessment_if_current,
)
from tests.persistence.test_operations import prepare


@pytest.fixture
def sessions(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = create_database_engine(
        Settings(
            _env_file=None, database_url=f"sqlite:///{(tmp_path / 'assessments.db').as_posix()}"
        )
    )
    Base.metadata.create_all(engine)
    try:
        yield create_session_factory(engine)
    finally:
        engine.dispose()


def test_assessment_is_versioned_and_separate_from_decision(sessions):
    manager, reviewer, application = prepare(sessions)
    from mortgage_pricing.persistence.operations import create_request

    created = create_request(
        sessions,
        caller_id=manager,
        application_id=application,
        discount_bps=25,
        reason="Synthetic",
        idempotency_key="assessment-test",
    )
    snapshot = capture_assessment_snapshot(
        sessions, reviewer_id=reviewer, request_id=created.request_id, expected_version=1
    )
    saved = store_assessment_if_current(
        sessions,
        reviewer_id=reviewer,
        snapshot=snapshot,
        model_identity="fake-model",
        prompt_version="pricing-exception-advisor-v1",
        idempotency_key="f" * 64,
        result={"summary": "Synthetic summary"},
    )
    assert saved.status == AssessmentStatus.COMPLETED
    from mortgage_pricing.persistence.operations import find_assessment_by_key

    cached = find_assessment_by_key(sessions, idempotency_key="f" * 64)
    assert cached is not None and cached.id == saved.id
    with sessions() as session:
        row = session.get(PricingAssessment, saved.id)
        assert row.request_id == created.request_id and row.version_number == 1
        assert row.result == {"summary": "Synthetic summary"}


def test_assessment_snapshot_rejects_stale_version(sessions):
    manager, reviewer, application = prepare(sessions)
    from mortgage_pricing.persistence.operations import create_request

    created = create_request(
        sessions,
        caller_id=manager,
        application_id=application,
        discount_bps=25,
        reason="Synthetic",
        idempotency_key="assessment-stale",
    )
    with pytest.raises(OperationError, match="stale_version"):
        capture_assessment_snapshot(
            sessions, reviewer_id=reviewer, request_id=created.request_id, expected_version=2
        )
