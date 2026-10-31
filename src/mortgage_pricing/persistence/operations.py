"""Atomic SQLite writes for the core request lifecycle, without HTTP contracts."""

import json
from dataclasses import dataclass
from hashlib import sha256
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from mortgage_pricing.persistence.models import (
    AssessmentStatus,
    CreationIdempotencyRecord,
    DecisionOutcome,
    HistoryEventType,
    MortgageApplication,
    PricingAssessment,
    PricingDecision,
    PricingRequest,
    RequestHistoryEvent,
    RequestVersion,
    Role,
    UserRoleMembership,
)

MAX_DISCOUNT_BPS = 2**63 - 1  # SQLite signed integer storage limit, not a policy threshold.


class OperationError(Exception):
    """Expected business failure; the later HTTP layer translates ``code``."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class VersionResult:
    request_id: UUID
    version_number: int
    replayed: bool = False


@dataclass(frozen=True)
class AssessmentSnapshot:
    request_id: UUID
    version_number: int
    submitted_by_id: UUID
    discount_bps: int
    reason: str
    context: dict[str, object] | None


@dataclass(frozen=True)
class StoredAssessment:
    id: UUID
    status: AssessmentStatus
    result: dict[str, object] | None = None


def find_assessment_by_key(
    sessions: sessionmaker[Session], *, idempotency_key: str
) -> StoredAssessment | None:
    """Return a completed report for the exact canonical assessment inputs, if present."""
    with sessions() as session:
        row = session.scalar(
            select(PricingAssessment).where(
                PricingAssessment.idempotency_key == idempotency_key,
                PricingAssessment.status == AssessmentStatus.COMPLETED,
            )
        )
        return StoredAssessment(row.id, row.status, row.result) if row is not None else None


def capture_assessment_snapshot(
    sessions: sessionmaker[Session], *, reviewer_id: UUID, request_id: UUID, expected_version: int
) -> AssessmentSnapshot:
    """Authorize and copy the exact current version; no DB transaction spans inference."""
    with sessions() as session:
        _require_role(session, reviewer_id, Role.REVIEWER)
        request = session.get(PricingRequest, request_id)
        if request is None:
            raise OperationError("request_not_found")
        if request.current_version_number != expected_version:
            raise OperationError("stale_version")
        version = session.get(RequestVersion, (request_id, expected_version))
        if version is None:
            raise OperationError("stale_version")
        if reviewer_id in (request.application.manager_id, version.submitted_by_id):
            raise OperationError("self_review")
        return AssessmentSnapshot(
            request_id,
            expected_version,
            version.submitted_by_id,
            version.discount_bps,
            version.reason,
            version.context,
        )


def store_assessment_if_current(
    sessions: sessionmaker[Session],
    *,
    reviewer_id: UUID,
    snapshot: AssessmentSnapshot,
    model_identity: str,
    prompt_version: str,
    idempotency_key: str | None = None,
    result: dict[str, object] | None,
) -> StoredAssessment:
    """Persist separately from decisions; raced revisions/decisions are recorded stale."""
    with sessions.begin() as session:
        _require_role(session, reviewer_id, Role.REVIEWER)
        existing = (
            session.scalar(
                select(PricingAssessment).where(
                    PricingAssessment.idempotency_key == idempotency_key
                )
            )
            if idempotency_key is not None
            else None
        )
        if existing is not None:
            return StoredAssessment(existing.id, existing.status, existing.result)
        request = _lock_request(session, snapshot.request_id)
        if reviewer_id in (request.application.manager_id, snapshot.submitted_by_id):
            raise OperationError("self_review")
        status = (
            AssessmentStatus.COMPLETED
            if request.current_version_number == snapshot.version_number
            and session.scalar(
                select(PricingDecision.id).where(
                    PricingDecision.request_id == snapshot.request_id,
                    PricingDecision.version_number == snapshot.version_number,
                )
            )
            is None
            else AssessmentStatus.STALE
        )
        assessment = PricingAssessment(
            request_id=snapshot.request_id,
            version_number=snapshot.version_number,
            model_identity=model_identity,
            prompt_version=prompt_version,
            idempotency_key=idempotency_key,
            status=status,
            result=result if status == AssessmentStatus.COMPLETED else None,
        )
        session.add(assessment)
        session.flush()
        stored = StoredAssessment(assessment.id, assessment.status, assessment.result)
    return stored


def _require_role(session: Session, actor_id: UUID, role: Role) -> None:
    if session.get(UserRoleMembership, (actor_id, role)) is None:
        raise OperationError("forbidden")


def _lock_application(session: Session, application_id: UUID) -> MortgageApplication:
    # First statement is a write. SQLite serializes writers before any state read.
    result = session.execute(
        update(MortgageApplication)
        .where(MortgageApplication.id == application_id)
        .values(reference=MortgageApplication.reference)
    )
    if result.rowcount != 1:
        raise OperationError("application_not_found")
    return session.get_one(MortgageApplication, application_id)


def _lock_request(session: Session, request_id: UUID) -> PricingRequest:
    result = session.execute(
        update(PricingRequest)
        .where(PricingRequest.id == request_id)
        .values(current_version_number=PricingRequest.current_version_number)
    )
    if result.rowcount != 1:
        raise OperationError("request_not_found")
    return session.get_one(PricingRequest, request_id)


def _validate_terms(discount_bps: int, reason: str) -> None:
    if (
        type(discount_bps) is not int
        or discount_bps <= 0
        or discount_bps > MAX_DISCOUNT_BPS
        or not isinstance(reason, str)
        or not reason.strip()
        or len(reason) > 2000
    ):
        raise OperationError("invalid_terms")


def _fingerprint(
    application_id: UUID,
    discount_bps: int,
    reason: str,
    context: dict[str, object] | None,
) -> str:
    payload: dict[str, object] = {
        "application_id": str(application_id),
        "discount_bps": discount_bps,
        "reason": reason,
    }
    if context is not None:
        payload["context"] = context
    canonical = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def create_request(
    sessions: sessionmaker[Session],
    *,
    caller_id: UUID,
    application_id: UUID,
    discount_bps: int,
    reason: str,
    idempotency_key: str,
    context: dict[str, object] | None = None,
) -> VersionResult:
    """Create version 1 once per application; replay only identical caller/key/input."""
    _validate_terms(discount_bps, reason)
    if not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key.strip()) <= 128:
        raise OperationError("invalid_idempotency_key")
    fingerprint = _fingerprint(application_id, discount_bps, reason, context)
    with sessions.begin() as session:
        application = _lock_application(session, application_id)
        _require_role(session, caller_id, Role.RELATIONSHIP_MANAGER)
        if application.manager_id != caller_id:
            raise OperationError("forbidden")
        prior = session.get(CreationIdempotencyRecord, (caller_id, idempotency_key))
        if prior is not None:
            if prior.input_fingerprint != fingerprint:
                raise OperationError("idempotency_conflict")
            return VersionResult(prior.request_id, prior.version_number, replayed=True)
        if (
            session.scalar(
                select(PricingRequest.id).where(PricingRequest.application_id == application_id)
            )
            is not None
        ):
            raise OperationError("request_exists")
        request = PricingRequest(application_id=application_id)
        session.add(request)
        session.flush()
        session.add(
            RequestVersion(
                request_id=request.id,
                version_number=1,
                discount_bps=discount_bps,
                reason=reason,
                context=context,
                submitted_by_id=caller_id,
            )
        )
        session.flush()
        request.current_version_number = 1
        session.add_all(
            (
                RequestHistoryEvent(
                    request_id=request.id,
                    version_number=1,
                    event_type=HistoryEventType.CREATED,
                    actor_id=caller_id,
                ),
                CreationIdempotencyRecord(
                    caller_id=caller_id,
                    key=idempotency_key,
                    input_fingerprint=fingerprint,
                    request_id=request.id,
                    version_number=1,
                ),
            )
        )
        return VersionResult(request.id, 1)


def revise_request(
    sessions: sessionmaker[Session],
    *,
    caller_id: UUID,
    request_id: UUID,
    expected_version: int,
    discount_bps: int,
    reason: str,
    context: dict[str, object] | None = None,
) -> VersionResult:
    """Append a version and history only when the caller saw the current version."""
    _validate_terms(discount_bps, reason)
    with sessions.begin() as session:
        request = _lock_request(session, request_id)
        _require_role(session, caller_id, Role.RELATIONSHIP_MANAGER)
        if request.application.manager_id != caller_id:
            raise OperationError("forbidden")
        if request.current_version_number != expected_version:
            raise OperationError("stale_version")
        number = expected_version + 1
        session.add(
            RequestVersion(
                request_id=request_id,
                version_number=number,
                discount_bps=discount_bps,
                reason=reason,
                context=context,
                submitted_by_id=caller_id,
            )
        )
        session.flush()
        request.current_version_number = number
        session.add(
            RequestHistoryEvent(
                request_id=request_id,
                version_number=number,
                event_type=HistoryEventType.REVISED,
                actor_id=caller_id,
            )
        )
        return VersionResult(request_id, number)


def decide_request(
    sessions: sessionmaker[Session],
    *,
    reviewer_id: UUID,
    request_id: UUID,
    expected_version: int,
    outcome: DecisionOutcome,
) -> VersionResult:
    """Decide exactly the current version, with its history in one transaction."""
    if not isinstance(outcome, DecisionOutcome):
        raise OperationError("invalid_outcome")
    with sessions.begin() as session:
        request = _lock_request(session, request_id)
        _require_role(session, reviewer_id, Role.REVIEWER)
        if request.current_version_number != expected_version:
            raise OperationError("stale_version")
        version = session.get_one(RequestVersion, (request_id, expected_version))
        if reviewer_id in (request.application.manager_id, version.submitted_by_id):
            raise OperationError("self_review")
        if (
            session.scalar(
                select(PricingDecision.id).where(
                    PricingDecision.request_id == request_id,
                    PricingDecision.version_number == expected_version,
                )
            )
            is not None
        ):
            raise OperationError("already_decided")
        session.add_all(
            (
                PricingDecision(
                    request_id=request_id,
                    version_number=expected_version,
                    outcome=outcome,
                    reviewer_id=reviewer_id,
                ),
                RequestHistoryEvent(
                    request_id=request_id,
                    version_number=expected_version,
                    event_type=(
                        HistoryEventType.APPROVED
                        if outcome == DecisionOutcome.APPROVED
                        else HistoryEventType.DECLINED
                    ),
                    actor_id=reviewer_id,
                ),
            )
        )
        return VersionResult(request_id, expected_version)
