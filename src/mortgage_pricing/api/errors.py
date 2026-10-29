"""Safe HTTP error contracts and framework exception handlers."""

from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
    correlation_id: str


def error_response(
    status_code: int,
    code: str,
    message: str,
    correlation_id: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Build the common envelope without serializing exception or request data."""
    response = JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=ErrorDetail(code=code, message=message), correlation_id=correlation_id
        ).model_dump(),
        headers=headers,
    )
    response.headers["X-Correlation-ID"] = correlation_id
    return response


def internal_error_response(correlation_id: str) -> JSONResponse:
    return error_response(500, "internal_error", "An unexpected error occurred.", correlation_id)


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if exc.status_code >= 500:
        return error_response(
            exc.status_code,
            "internal_error",
            "An unexpected error occurred.",
            request.state.correlation_id,
            exc.headers,
        )
    try:
        status = HTTPStatus(exc.status_code)
    except ValueError:
        code, message = "http_error", "The request could not be completed."
    else:
        code, message = status.name.lower(), status.phrase
    return error_response(exc.status_code, code, message, request.state.correlation_id, exc.headers)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Validation errors may contain raw input, custom messages, and attacker-supplied field names.
    return error_response(
        422, "validation_error", "Request validation failed.", request.state.correlation_id
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
