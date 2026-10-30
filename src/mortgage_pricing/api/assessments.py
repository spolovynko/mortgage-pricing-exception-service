"""Explicitly invoked, optional advisory assessment endpoints."""

from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from starlette.responses import JSONResponse

from mortgage_pricing.ai.ollama import AssessmentFailure, generate_assessment
from mortgage_pricing.api.errors import error_response
from mortgage_pricing.api.foundation import ActorId
from mortgage_pricing.persistence.database import create_session_factory
from mortgage_pricing.persistence.models import PricingAssessment
from mortgage_pricing.persistence.operations import (
    OperationError,
    capture_assessment_snapshot,
    store_assessment_if_current,
)

router = APIRouter(tags=["AI assessments"])


class AssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(strict=True, ge=1)


class AssessmentResponse(BaseModel):
    assessment_id: UUID
    request_id: UUID
    version_number: int
    status: str
    result: dict[str, object] | None


@router.post("/requests/{request_id}/assessments", response_model=AssessmentResponse)
async def create_assessment(
    request_id: UUID, body: AssessmentRequest, request: Request, actor_id: ActorId
) -> AssessmentResponse | JSONResponse:
    correlation_id = request.state.correlation_id
    if request.app.state.settings.llm_mode != "auto":
        return error_response(503, "ai_disabled", "AI assistance is not enabled.", correlation_id)
    sessions = create_session_factory(request.app.state.database_engine)
    try:
        snapshot = capture_assessment_snapshot(
            sessions,
            reviewer_id=actor_id,
            request_id=request_id,
            expected_version=body.expected_version,
        )
    except OperationError as exc:
        status, message = {
            "request_not_found": (404, "Request was not found."),
            "forbidden": (403, "Reviewer permission is required."),
            "self_review": (403, "A submitter or application owner cannot assess this request."),
            "stale_version": (409, "The request version is no longer current."),
        }[exc.code]
        return error_response(status, exc.code, message, correlation_id)
    source = {
        "request_id": str(snapshot.request_id),
        "version_number": snapshot.version_number,
        "discount_bps": snapshot.discount_bps,
        "reason": snapshot.reason,
        "context": snapshot.context,
    }
    settings = request.app.state.settings
    try:
        result = await generate_assessment(
            base_url=str(settings.llm_base_url),
            model=settings.llm_model,
            timeout=settings.llm_timeout_seconds,
            snapshot=source,
        )
    except AssessmentFailure as exc:
        status = 504 if exc.code == "timeout" else 503
        message = (
            "AI assistance timed out."
            if status == 504
            else "AI assistance is unavailable or returned invalid output."
        )
        return error_response(status, exc.code, message, correlation_id)
    try:
        saved = store_assessment_if_current(
            sessions,
            reviewer_id=actor_id,
            snapshot=snapshot,
            model_identity=settings.llm_model,
            prompt_version="pricing-exception-advisor-v1",
            result=result.model_dump(mode="json"),
        )
    except OperationError as exc:
        status = 404 if exc.code == "request_not_found" else 403
        return error_response(status, exc.code, "Assessment could not be stored.", correlation_id)
    return AssessmentResponse(
        assessment_id=saved.id,
        request_id=request_id,
        version_number=snapshot.version_number,
        status=saved.status.value,
        result=result.model_dump(mode="json") if saved.status.value == "completed" else None,
    )


@router.get("/requests/{request_id}/assessments", response_model=list[AssessmentResponse])
def list_assessments(
    request_id: UUID, request: Request, actor_id: ActorId, expected_version: int
) -> list[AssessmentResponse] | JSONResponse:
    sessions = create_session_factory(request.app.state.database_engine)
    try:
        capture_assessment_snapshot(
            sessions, reviewer_id=actor_id, request_id=request_id, expected_version=expected_version
        )
    except OperationError as exc:
        status = (
            404 if exc.code == "request_not_found" else 409 if exc.code == "stale_version" else 403
        )
        return error_response(
            status,
            exc.code,
            "Assessment history is unavailable for this version.",
            request.state.correlation_id,
        )
    with sessions() as session:
        rows = session.scalars(
            select(PricingAssessment)
            .where(
                PricingAssessment.request_id == request_id,
                PricingAssessment.version_number == expected_version,
            )
            .order_by(PricingAssessment.created_at.desc())
        ).all()
        return [
            AssessmentResponse(
                assessment_id=row.id,
                request_id=request_id,
                version_number=row.version_number,
                status=row.status.value,
                result=row.result if row.status.value == "completed" else None,
            )
            for row in rows
        ]
