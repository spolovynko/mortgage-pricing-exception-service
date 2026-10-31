"""Explicitly invoked, optional advisory assessment endpoints."""

import hashlib
import json
from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from starlette.responses import JSONResponse, Response, StreamingResponse

from mortgage_pricing.ai.assessment_contract import (
    GENERATION_SETTINGS,
    PROMPT_VERSION,
    REPORT_SCHEMA_VERSION,
    AdvisoryOpinion,
    assemble_report,
    pricing_effect,
)
from mortgage_pricing.ai.ollama import (
    AssessmentFailure,
    generate_assessment,
    resolve_model_digest,
    stream_assessment,
)
from mortgage_pricing.ai.rubric import ChecklistResult, evaluate_checklist
from mortgage_pricing.api.errors import error_response
from mortgage_pricing.api.foundation import ActorId
from mortgage_pricing.persistence.database import create_session_factory
from mortgage_pricing.persistence.models import PricingAssessment
from mortgage_pricing.persistence.operations import (
    OperationError,
    capture_assessment_snapshot,
    find_assessment_by_key,
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


def _source(snapshot) -> dict[str, object]:
    return {
        "request_id": str(snapshot.request_id),
        "version_number": snapshot.version_number,
        "discount_bps": snapshot.discount_bps,
        "reason": snapshot.reason,
        "context": snapshot.context,
    }


def _key(source: dict[str, object], model: str, runtime: str, model_digest: str) -> str:
    payload = {
        "snapshot": source,
        "model": model,
        "model_digest": model_digest,
        "runtime": runtime.rstrip("/"),
        "prompt": PROMPT_VERSION,
        "rubric": evaluate_checklist(source).rubric_version,
        "schema": REPORT_SCHEMA_VERSION,
        "settings": GENERATION_SETTINGS,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _report(saved, request_id: UUID, version: int) -> AssessmentResponse:
    return AssessmentResponse(
        assessment_id=saved.id,
        request_id=request_id,
        version_number=version,
        status=saved.status.value,
        result=saved.result if saved.status.value == "completed" else None,
    )


def _assemble(
    selection: AdvisoryOpinion,
    checklist: ChecklistResult,
    source: dict[str, object],
    model: str,
    model_digest: str,
    metrics: dict[str, object],
) -> dict[str, object]:
    return assemble_report(selection, checklist, source) | {
        "model_identity": model,
        "model_digest": model_digest,
        "generation_metrics": metrics,
        "prompt_version": PROMPT_VERSION,
    }


def _snapshot(request, actor_id, request_id, expected_version):
    sessions = create_session_factory(request.app.state.database_engine)
    snapshot = capture_assessment_snapshot(
        sessions,
        reviewer_id=actor_id,
        request_id=request_id,
        expected_version=expected_version,
    )
    return sessions, snapshot


def _snapshot_error(exc: OperationError, correlation_id: str):
    status, message = {
        "request_not_found": (404, "Request was not found."),
        "forbidden": (403, "Reviewer permission is required."),
        "self_review": (403, "A submitter or application owner cannot assess this request."),
        "stale_version": (409, "The request version is no longer current."),
    }[exc.code]
    return error_response(status, exc.code, message, correlation_id)


def _failure(exc: AssessmentFailure, correlation_id: str):
    status = 504 if exc.code == "timeout" else 503
    message = (
        "AI assistance timed out."
        if status == 504
        else "AI assistance is unavailable or returned invalid output."
    )
    return error_response(status, exc.code, message, correlation_id)


def _audit(request: Request, event: str, request_id: UUID, version: int, **metadata) -> None:
    request.app.state.logger.info(
        event,
        extra={"request_id": str(request_id), "version_id": version, **metadata},
    )


@router.post("/requests/{request_id}/assessments", response_model=AssessmentResponse)
async def create_assessment(
    request_id: UUID, body: AssessmentRequest, request: Request, actor_id: ActorId
) -> AssessmentResponse | JSONResponse:
    correlation_id = request.state.correlation_id
    settings = request.app.state.settings
    if settings.llm_mode != "auto":
        return error_response(503, "ai_disabled", "AI assistance is not enabled.", correlation_id)
    try:
        sessions, snapshot = _snapshot(request, actor_id, request_id, body.expected_version)
    except OperationError as exc:
        return _snapshot_error(exc, correlation_id)
    source = _source(snapshot)
    checklist = evaluate_checklist(source)
    try:
        digest = await resolve_model_digest(
            str(settings.llm_base_url), settings.llm_model, settings.llm_timeout_seconds
        )
    except AssessmentFailure as exc:
        _audit(
            request,
            "ai_assessment_failed",
            request_id,
            snapshot.version_number,
            outcome="failure",
            error_code=exc.code,
        )
        return _failure(exc, correlation_id)
    key = _key(source, settings.llm_model, str(settings.llm_base_url), digest)
    cached = find_assessment_by_key(sessions, idempotency_key=key)
    if cached is not None:
        _audit(
            request,
            "ai_assessment_replayed",
            request_id,
            snapshot.version_number,
            outcome="success",
            model_digest=digest,
            assessment_id=str(cached.id),
        )
        return _report(cached, request_id, snapshot.version_number)
    try:
        narrative, metrics = await generate_assessment(
            base_url=str(settings.llm_base_url),
            model=settings.llm_model,
            timeout=settings.llm_timeout_seconds,
            snapshot=source,
            checklist=checklist.model_dump(mode="json"),
        )
    except AssessmentFailure as exc:
        _audit(
            request,
            "ai_assessment_failed",
            request_id,
            snapshot.version_number,
            outcome="failure",
            error_code=exc.code,
        )
        return _failure(exc, correlation_id)
    result_data = _assemble(narrative, checklist, source, settings.llm_model, digest, metrics)
    try:
        saved = store_assessment_if_current(
            sessions,
            reviewer_id=actor_id,
            snapshot=snapshot,
            model_identity=settings.llm_model,
            prompt_version=PROMPT_VERSION,
            idempotency_key=key,
            result=result_data,
        )
    except OperationError as exc:
        return _snapshot_error(exc, correlation_id)
    _audit(
        request,
        "ai_assessment_completed",
        request_id,
        snapshot.version_number,
        outcome=saved.status.value,
        assessment_id=str(saved.id),
        model_digest=digest,
        duration=metrics.get("total_ms", 0) / 1000,
    )
    return _report(saved, request_id, snapshot.version_number)


@router.post("/requests/{request_id}/assessments/stream")
async def create_assessment_stream(
    request_id: UUID, body: AssessmentRequest, request: Request, actor_id: ActorId
) -> Response:
    correlation_id = request.state.correlation_id
    settings = request.app.state.settings
    if settings.llm_mode != "auto":
        return error_response(503, "ai_disabled", "AI assistance is not enabled.", correlation_id)
    try:
        sessions, snapshot = _snapshot(request, actor_id, request_id, body.expected_version)
    except OperationError as exc:
        return _snapshot_error(exc, correlation_id)
    source = _source(snapshot)
    checklist = evaluate_checklist(source)
    try:
        digest = await resolve_model_digest(
            str(settings.llm_base_url), settings.llm_model, settings.llm_timeout_seconds
        )
    except AssessmentFailure as exc:
        _audit(
            request,
            "ai_assessment_failed",
            request_id,
            snapshot.version_number,
            outcome="failure",
            error_code=exc.code,
        )
        return _failure(exc, correlation_id)
    key = _key(source, settings.llm_model, str(settings.llm_base_url), digest)

    async def events():
        yield (
            "event: context\ndata: "
            + json.dumps(
                {
                    "pricing_effect": pricing_effect(source).get("description"),
                    "model_identity": settings.llm_model,
                    "prompt_version": PROMPT_VERSION,
                    "rubric_version": checklist.rubric_version,
                    "report_schema_version": REPORT_SCHEMA_VERSION,
                }
            )
            + "\n\n"
        )
        cached = find_assessment_by_key(sessions, idempotency_key=key)
        if cached is not None:
            _audit(
                request,
                "ai_assessment_replayed",
                request_id,
                snapshot.version_number,
                outcome="success",
                model_digest=digest,
                assessment_id=str(cached.id),
            )
            yield (
                "event: complete\ndata: "
                + _report(cached, request_id, snapshot.version_number).model_dump_json()
                + "\n\n"
            )
            return
        try:
            async for event in stream_assessment(
                base_url=str(settings.llm_base_url),
                model=settings.llm_model,
                timeout=settings.llm_timeout_seconds,
                snapshot=source,
                checklist=checklist.model_dump(mode="json"),
            ):
                if event["type"] == "reset":
                    yield "event: reset\ndata: {}\n\n"
                    continue
                if event["type"] == "partial":
                    partial_report = event["result"].model_dump(mode="json")
                    yield ("event: partial\ndata: " + json.dumps(partial_report) + "\n\n")
                    continue
                selection: AdvisoryOpinion = event["result"]
                result_data = _assemble(
                    selection,
                    checklist,
                    source,
                    settings.llm_model,
                    digest,
                    event.get("metrics", {}),
                )
                saved = store_assessment_if_current(
                    sessions,
                    reviewer_id=actor_id,
                    snapshot=snapshot,
                    model_identity=settings.llm_model,
                    prompt_version=PROMPT_VERSION,
                    idempotency_key=key,
                    result=result_data,
                )
                _audit(
                    request,
                    "ai_assessment_completed",
                    request_id,
                    snapshot.version_number,
                    outcome=saved.status.value,
                    assessment_id=str(saved.id),
                    model_digest=digest,
                    duration=event.get("metrics", {}).get("total_ms", 0) / 1000,
                )
                metrics = event.get("metrics")
                if isinstance(metrics, dict):
                    yield "event: metrics\ndata: " + json.dumps(metrics) + "\n\n"
                yield (
                    "event: complete\ndata: "
                    + _report(saved, request_id, snapshot.version_number).model_dump_json()
                    + "\n\n"
                )
        except AssessmentFailure as exc:
            _audit(
                request,
                "ai_assessment_failed",
                request_id,
                snapshot.version_number,
                outcome="failure",
                error_code=exc.code,
            )
            yield "event: error\ndata: " + json.dumps({"code": exc.code}) + "\n\n"
        except OperationError as exc:
            yield "event: error\ndata: " + json.dumps({"code": exc.code}) + "\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
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
        return _snapshot_error(exc, request.state.correlation_id)
    with sessions() as session:
        rows = session.scalars(
            select(PricingAssessment)
            .where(
                PricingAssessment.request_id == request_id,
                PricingAssessment.version_number == expected_version,
            )
            .order_by(PricingAssessment.created_at.desc())
        ).all()
        return [_report(row, request_id, row.version_number) for row in rows]
