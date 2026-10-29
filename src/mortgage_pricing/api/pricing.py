"""Return only pricing approved for an application's current request version."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import select
from starlette.responses import JSONResponse

from mortgage_pricing.api.errors import ErrorResponse, error_response
from mortgage_pricing.api.foundation import ActorId
from mortgage_pricing.persistence.database import create_session_factory
from mortgage_pricing.persistence.models import (
    DecisionOutcome,
    MortgageApplication,
    PricingDecision,
    PricingRequest,
    RequestVersion,
)

router = APIRouter(tags=["approved pricing"])


class ApprovedDiscount(BaseModel):
    application_id: UUID
    status: Literal["approved"]
    request_id: UUID
    version_number: int
    discount_bps: int


class NoApprovedDiscount(BaseModel):
    application_id: UUID
    status: Literal["none"]


@router.get(
    "/applications/{application_id}/approved-discount",
    response_model=ApprovedDiscount | NoApprovedDiscount,
    summary="Retrieve usable pricing from the current approved version",
    responses={
        401: {"model": ErrorResponse, "description": "Demo identity required"},
        403: {"model": ErrorResponse, "description": "No internal role"},
        404: {"model": ErrorResponse, "description": "Application not found"},
        422: {"model": ErrorResponse, "description": "Invalid application identifier"},
        503: {"model": ErrorResponse, "description": "Storage or demo identity unavailable"},
    },
)
def get_approved_discount(
    application_id: UUID, request: Request, _actor: ActorId
) -> ApprovedDiscount | NoApprovedDiscount | JSONResponse:
    with create_session_factory(request.app.state.database_engine)() as session:
        application = session.get(MortgageApplication, application_id)
        if application is None:
            return error_response(
                404,
                "application_not_found",
                "Mortgage application was not found.",
                request.state.correlation_id,
            )
        pricing_request = session.scalar(
            select(PricingRequest).where(PricingRequest.application_id == application_id)
        )
        if pricing_request is None or pricing_request.current_version_number is None:
            return NoApprovedDiscount(application_id=application_id, status="none")
        version_number = pricing_request.current_version_number
        decision = session.scalar(
            select(PricingDecision).where(
                PricingDecision.request_id == pricing_request.id,
                PricingDecision.version_number == version_number,
            )
        )
        if decision is None or decision.outcome != DecisionOutcome.APPROVED:
            return NoApprovedDiscount(application_id=application_id, status="none")
        version = session.get_one(RequestVersion, (pricing_request.id, version_number))
        return ApprovedDiscount(
            application_id=application_id,
            status="approved",
            request_id=pricing_request.id,
            version_number=version_number,
            discount_bps=version.discount_bps,
        )
