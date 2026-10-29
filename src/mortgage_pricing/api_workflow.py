"""HTTP revision and human decision routes over atomic persistence operations."""

from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import JSONResponse

from mortgage_pricing.api_foundation import ActorId
from mortgage_pricing.errors import ErrorResponse, error_response
from mortgage_pricing.persistence.database import create_session_factory
from mortgage_pricing.persistence.models import DecisionOutcome
from mortgage_pricing.persistence.operations import (
    MAX_DISCOUNT_BPS,
    OperationError,
    decide_request,
    revise_request,
)

router = APIRouter(
    tags=["requests"],
    responses={
        401: {"model": ErrorResponse, "description": "Demo identity required"},
        403: {"model": ErrorResponse, "description": "Role, ownership, or self-review denied"},
        404: {"model": ErrorResponse, "description": "Request not found"},
        409: {"model": ErrorResponse, "description": "Version changed or already decided"},
        422: {"model": ErrorResponse, "description": "Invalid input"},
        503: {"model": ErrorResponse, "description": "Storage unavailable"},
    },
)


class RevisionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(strict=True, ge=1)
    discount_bps: int = Field(strict=True, gt=0, le=MAX_DISCOUNT_BPS)
    reason: str = Field(min_length=1, max_length=2000)


class RevisionResult(BaseModel):
    request_id: UUID
    version_number: int
    replayed: bool = False


class DecisionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(strict=True, ge=1)
    outcome: DecisionOutcome


class DecisionResult(BaseModel):
    request_id: UUID
    version_number: int
    outcome: DecisionOutcome


ERRORS = {
    "request_not_found": (404, "Pricing request was not found."),
    "forbidden": (403, "The user is not permitted to perform this operation."),
    "self_review": (403, "A submitter or application owner cannot review these terms."),
    "stale_version": (409, "The current version differs from the reviewed version."),
    "already_decided": (409, "This version already has a final decision."),
    "invalid_terms": (422, "Discount and reason must contain valid terms."),
    "invalid_outcome": (422, "Outcome must be approved or declined."),
}


def _operation_error(request: Request, exc: OperationError) -> JSONResponse:
    status, message = ERRORS[exc.code]
    return error_response(status, exc.code, message, request.state.correlation_id)


@router.post(
    "/requests/{request_id}/revisions",
    response_model=RevisionResult,
    status_code=201,
    summary="Submit a new pending version of the current request",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {
                        "expected_version": 1,
                        "discount_bps": 40,
                        "reason": "Synthetic revised terms",
                    }
                }
            }
        }
    },
)
def post_revision(
    request_id: UUID, body: RevisionBody, request: Request, actor_id: ActorId
) -> RevisionResult | JSONResponse:
    try:
        result = revise_request(
            create_session_factory(request.app.state.database_engine),
            caller_id=actor_id,
            request_id=request_id,
            expected_version=body.expected_version,
            discount_bps=body.discount_bps,
            reason=body.reason,
        )
    except OperationError as exc:
        return _operation_error(request, exc)
    request.app.state.logger.info(
        "request_revised",
        extra={
            "actor_id": str(actor_id),
            "request_id": str(request_id),
            "version_id": result.version_number,
            "outcome": "revised",
        },
    )
    return RevisionResult(request_id=result.request_id, version_number=result.version_number)


@router.post(
    "/requests/{request_id}/decisions",
    response_model=DecisionResult,
    summary="Decide the exact current version without changing its terms",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {"example": {"expected_version": 1, "outcome": "approved"}}
            }
        }
    },
)
def post_decision(
    request_id: UUID, body: DecisionBody, request: Request, actor_id: ActorId
) -> DecisionResult | JSONResponse:
    try:
        result = decide_request(
            create_session_factory(request.app.state.database_engine),
            reviewer_id=actor_id,
            request_id=request_id,
            expected_version=body.expected_version,
            outcome=body.outcome,
        )
    except OperationError as exc:
        return _operation_error(request, exc)
    request.app.state.logger.info(
        "request_decided",
        extra={
            "actor_id": str(actor_id),
            "request_id": str(request_id),
            "version_id": result.version_number,
            "outcome": body.outcome.value,
        },
    )
    return DecisionResult(
        request_id=result.request_id, version_number=result.version_number, outcome=body.outcome
    )
