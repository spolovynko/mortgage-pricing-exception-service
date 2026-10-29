"""Read-only request, version, decision, and history endpoints."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from starlette.responses import JSONResponse

from mortgage_pricing.api_foundation import ActorId
from mortgage_pricing.errors import ErrorResponse, error_response
from mortgage_pricing.persistence.database import create_session_factory
from mortgage_pricing.persistence.models import (
    DecisionOutcome,
    HistoryEventType,
    MortgageApplication,
    PricingDecision,
    PricingRequest,
    RequestHistoryEvent,
    RequestVersion,
    User,
)

router = APIRouter(
    tags=["requests"],
    responses={
        401: {"model": ErrorResponse, "description": "Demo identity required"},
        404: {"model": ErrorResponse, "description": "Request not found"},
        503: {"model": ErrorResponse, "description": "Storage or demo identity unavailable"},
    },
)


class RequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"


class DecisionView(BaseModel):
    outcome: DecisionOutcome
    reviewer_id: UUID
    reviewer_login: str
    decided_at: datetime


class VersionView(BaseModel):
    version_number: int
    discount_bps: int
    reason: str
    submitted_by_id: UUID
    submitted_by_login: str
    submitted_at: datetime
    status: RequestStatus
    decision: DecisionView | None


class RequestSummary(BaseModel):
    request_id: UUID
    application_id: UUID
    application_reference: str
    current_version_number: int
    status: RequestStatus


class RequestDetail(RequestSummary):
    current_version: VersionView


class HistoryEventView(BaseModel):
    event_id: UUID
    version_number: int
    event_type: HistoryEventType
    actor_id: UUID
    actor_login: str
    occurred_at: datetime
    version: VersionView


def _view(session, request: PricingRequest, version: RequestVersion) -> VersionView:
    decision = session.scalar(
        select(PricingDecision).where(
            PricingDecision.request_id == request.id,
            PricingDecision.version_number == version.version_number,
        )
    )
    status = RequestStatus.PENDING if decision is None else RequestStatus(decision.outcome.value)
    decision_view = None
    if decision is not None:
        reviewer = session.get(User, decision.reviewer_id)
        decision_view = DecisionView(
            outcome=decision.outcome,
            reviewer_id=decision.reviewer_id,
            reviewer_login=reviewer.login,
            decided_at=decision.decided_at,
        )
    submitter = session.get(User, version.submitted_by_id)
    return VersionView(
        version_number=version.version_number,
        discount_bps=version.discount_bps,
        reason=version.reason,
        submitted_by_id=version.submitted_by_id,
        submitted_by_login=submitter.login,
        submitted_at=version.submitted_at,
        status=status,
        decision=decision_view,
    )


@router.get("/requests", response_model=list[RequestSummary], summary="List pricing requests")
def list_requests(
    request: Request,
    _actor: ActorId,
    application_id: UUID | None = None,
    status: Annotated[RequestStatus | None, Query()] = None,
) -> list[RequestSummary]:
    with create_session_factory(request.app.state.database_engine)() as session:
        query = select(PricingRequest).order_by(PricingRequest.id)
        if application_id is not None:
            query = query.where(PricingRequest.application_id == application_id)
        requests = session.scalars(query).all()
        summaries = []
        for item in requests:
            version = session.get(RequestVersion, (item.id, item.current_version_number))
            if version is None:
                continue
            view = _view(session, item, version)
            if status is not None and view.status != status:
                continue
            application = session.get(MortgageApplication, item.application_id)
            summaries.append(
                RequestSummary(
                    request_id=item.id,
                    application_id=item.application_id,
                    application_reference=application.reference,
                    current_version_number=version.version_number,
                    status=view.status,
                )
            )
        return summaries


@router.get(
    "/requests/{request_id}",
    response_model=RequestDetail,
    summary="Inspect current request terms and decision",
)
def get_request(
    request_id: UUID, request: Request, _actor: ActorId
) -> RequestDetail | JSONResponse:
    with create_session_factory(request.app.state.database_engine)() as session:
        item = session.get(PricingRequest, request_id)
        if item is None:
            return error_response(
                404,
                "request_not_found",
                "Pricing request was not found.",
                request.state.correlation_id,
            )
        version = session.get(RequestVersion, (item.id, item.current_version_number))
        application = session.get(MortgageApplication, item.application_id)
        current = _view(session, item, version)
        return RequestDetail(
            request_id=item.id,
            application_id=item.application_id,
            application_reference=application.reference,
            current_version_number=version.version_number,
            status=current.status,
            current_version=current,
        )


@router.get(
    "/requests/{request_id}/history",
    response_model=list[HistoryEventView],
    summary="Inspect ordered request history",
)
def get_history(
    request_id: UUID, request: Request, _actor: ActorId
) -> list[HistoryEventView] | JSONResponse:
    with create_session_factory(request.app.state.database_engine)() as session:
        item = session.get(PricingRequest, request_id)
        if item is None:
            return error_response(
                404,
                "request_not_found",
                "Pricing request was not found.",
                request.state.correlation_id,
            )
        events = session.scalars(
            select(RequestHistoryEvent)
            .where(RequestHistoryEvent.request_id == request_id)
            .order_by(RequestHistoryEvent.occurred_at, RequestHistoryEvent.id)
        ).all()
        results = []
        for event in events:
            version = session.get(RequestVersion, (request_id, event.version_number))
            actor = session.get(User, event.actor_id)
            results.append(
                HistoryEventView(
                    event_id=event.id,
                    version_number=event.version_number,
                    event_type=event.event_type,
                    actor_id=event.actor_id,
                    actor_login=actor.login,
                    occurred_at=event.occurred_at,
                    version=_view(session, item, version),
                )
            )
        return results
