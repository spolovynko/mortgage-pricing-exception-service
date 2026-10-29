"""Small HTTP boundary for the Streamlit UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import uuid4

import httpx2


class HttpResponse(Protocol):
    status_code: int
    headers: Any

    def json(self) -> Any: ...


class HttpTransport(Protocol):
    def request(self, method: str, url: str, **kwargs: Any) -> HttpResponse: ...


@dataclass(frozen=True)
class ApiError(Exception):
    status_code: int | None
    code: str
    message: str
    correlation_id: str | None

    def __str__(self) -> str:
        suffix = f" (correlation ID: {self.correlation_id})" if self.correlation_id else ""
        return f"{self.message}{suffix}"


class ApiClient:
    """HTTP-only API client; a transport can be injected for AppTest/focused tests."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 10.0,
        transport: HttpTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._transport = transport or httpx2.Client(timeout=timeout_seconds)

    def close(self) -> None:
        close = getattr(self._transport, "close", None)
        if close is not None:
            close()

    def request(self, method: str, path: str, *, login: str, **kwargs: Any) -> Any:
        correlation_id = str(uuid4())
        headers = dict(kwargs.pop("headers", {}) or {})
        headers.update({"X-Demo-User": login, "X-Correlation-ID": correlation_id})
        try:
            response = self._transport.request(
                method,
                f"{self.base_url}/{path.lstrip('/')}",
                headers=headers,
                timeout=self.timeout_seconds,
                **kwargs,
            )
        except (httpx2.TimeoutException, httpx2.NetworkError) as exc:
            raise ApiError(
                None, "backend_unavailable", "The API is unavailable or timed out.", correlation_id
            ) from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise ApiError(
                response.status_code,
                "invalid_response",
                "The API returned an invalid response.",
                response.headers.get("X-Correlation-ID", correlation_id),
            ) from exc
        if response.status_code >= 400:
            envelope = payload.get("error", {}) if isinstance(payload, dict) else {}
            raise ApiError(
                response.status_code,
                envelope.get("code", "api_error"),
                envelope.get("message", "The API request failed."),
                payload.get("correlation_id")
                or response.headers.get("X-Correlation-ID", correlation_id),
            )
        return payload


def configured_client(settings: Any) -> ApiClient:
    """Build a client from the existing immutable application settings."""
    return ApiClient(str(settings.ui_api_url), timeout_seconds=settings.ui_timeout_seconds)
