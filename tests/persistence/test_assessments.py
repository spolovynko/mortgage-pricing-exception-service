"""Assessment snapshots and stale-result protection."""

from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
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


def test_competing_assessment_saves_replay_one_canonical_result(sessions):
    from mortgage_pricing.persistence.operations import create_request

    manager, reviewer, application = prepare(sessions)
    created = create_request(
        sessions,
        caller_id=manager,
        application_id=application,
        discount_bps=25,
        reason="Synthetic",
        idempotency_key="race-create",
    )
    snapshot = capture_assessment_snapshot(
        sessions, reviewer_id=reviewer, request_id=created.request_id, expected_version=1
    )

    def save(number):
        return store_assessment_if_current(
            sessions,
            reviewer_id=reviewer,
            snapshot=snapshot,
            model_identity="fake",
            prompt_version="test",
            idempotency_key="b" * 64,
            result={"run": number},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = list(pool.map(save, [1, 2]))
    assert first.id == second.id and first.result == second.result


def test_revision_during_inference_marks_result_stale(sessions):
    from mortgage_pricing.persistence.operations import create_request, revise_request

    manager, reviewer, application = prepare(sessions)
    created = create_request(
        sessions,
        caller_id=manager,
        application_id=application,
        discount_bps=25,
        reason="Synthetic",
        idempotency_key="stale-create",
    )
    snapshot = capture_assessment_snapshot(
        sessions, reviewer_id=reviewer, request_id=created.request_id, expected_version=1
    )
    revise_request(
        sessions,
        caller_id=manager,
        request_id=created.request_id,
        expected_version=1,
        discount_bps=30,
        reason="Synthetic revision",
    )
    saved = store_assessment_if_current(
        sessions,
        reviewer_id=reviewer,
        snapshot=snapshot,
        model_identity="fake",
        prompt_version="test",
        idempotency_key="c" * 64,
        result={"explanation": "Old-version opinion"},
    )
    assert saved.status == AssessmentStatus.STALE and saved.result is None
