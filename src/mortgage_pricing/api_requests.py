"""HTTP creation contract over the existing atomic persistence operation."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import JSONResponse

from mortgage_pricing.api_foundation import ActorId
from mortgage_pricing.errors import ErrorResponse, error_response
from mortgage_pricing.persistence.database import create_session_factory
from mortgage_pricing.persistence.operations import MAX_DISCOUNT_BPS, OperationError, create_request
from mortgage_pricing.request_context import RequestContext

router = APIRouter(tags=["requests"])


class CreateRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: UUID
    discount_bps: int = Field(strict=True, gt=0, le=MAX_DISCOUNT_BPS)
    reason: str = Field(min_length=1, max_length=2000)
    context: RequestContext | None = None


class CreateRequestResult(BaseModel):
    request_id: UUID
    version_number: int
    replayed: bool


CREATE_ERRORS = {
    "application_not_found": (404, "Mortgage application was not found."),
    "forbidden": (403, "The user cannot create a request for this application."),
    "request_exists": (409, "A request already exists for this application."),
    "idempotency_conflict": (409, "The key was already used with different input."),
    "invalid_terms": (422, "Discount and reason must contain valid terms."),
    "invalid_idempotency_key": (422, "Idempotency-Key must contain 1 to 128 characters."),
}


@router.post(
    "/requests",
    response_model=CreateRequestResult,
    status_code=201,
    summary="Create a request or replay its original creation",
    responses={
        200: {"model": CreateRequestResult, "description": "Matching caller/key/input replay"},
        401: {"model": ErrorResponse, "description": "Demo identity required"},
        403: {"model": ErrorResponse, "description": "Caller does not own the application"},
        404: {"model": ErrorResponse, "description": "Application not found"},
        409: {"model": ErrorResponse, "description": "Existing request or key conflict"},
        422: {"model": ErrorResponse, "description": "Invalid body or key"},
        503: {"model": ErrorResponse, "description": "Storage or demo identity unavailable"},
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {
                        "application_id": "00000000-0000-0000-0000-000000000001",
                        "discount_bps": 25,
                        "reason": "Synthetic customer retention request",
                        "context": {
                            "application": {
                                "purpose": "purchase",
                                "rate_type": "fixed",
                                "loan_amount": "250000.00",
                                "property_value": "320000.00",
                                "currency_code": "EUR",
                                "term_months": 300,
                                "standard_rate_bps": 425,
                            },
                            "reason_category": "retention",
                        },
                    }
                }
            }
        },
    },
)
def post_request(
    request: Request,
    response: Response,
    body: CreateRequestBody,
    actor_id: ActorId,
    idempotency_key: Annotated[str, Header(min_length=1, max_length=128)],
) -> CreateRequestResult | JSONResponse:
    try:
        result = create_request(
            create_session_factory(request.app.state.database_engine),
            caller_id=actor_id,
            application_id=body.application_id,
            discount_bps=body.discount_bps,
            reason=body.reason,
            idempotency_key=idempotency_key,
            context=body.context.model_dump(mode="json") if body.context else None,
        )
    except OperationError as exc:
        status, message = CREATE_ERRORS[exc.code]
        return error_response(status, exc.code, message, request.state.correlation_id)
    response.status_code = 200 if result.replayed else 201
    request.app.state.logger.info(
        "request_creation_replayed" if result.replayed else "request_created",
        extra={
            "actor_id": str(actor_id),
            "request_id": str(result.request_id),
            "version_id": result.version_number,
            "outcome": "replayed" if result.replayed else "created",
        },
    )
    return CreateRequestResult(
        request_id=result.request_id,
        version_number=result.version_number,
        replayed=result.replayed,
    )
