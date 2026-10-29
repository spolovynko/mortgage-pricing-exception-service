import json
from uuid import UUID

import anyio
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError
from starlette.types import Message, Receive, Scope, Send

from mortgage_pricing.config import Settings
from mortgage_pricing.main import create_app
from mortgage_pricing.observability.request_logging import RequestLoggingMiddleware


@pytest.mark.parametrize(
    ("method", "path", "status", "code", "message"),
    [
        ("GET", "/missing", 404, "not_found", "Not Found"),
        ("POST", "/health", 405, "method_not_allowed", "Method Not Allowed"),
    ],
)
def test_framework_errors_use_common_envelope(
    method: str,
    path: str,
    status: int,
    code: str,
    message: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with TestClient(create_app(Settings(_env_file=None))) as client:
        response = client.request(method, path, headers={"X-Correlation-ID": "framework-error"})
    assert response.status_code == status
    assert response.json() == {
        "error": {"code": code, "message": message},
        "correlation_id": "framework-error",
    }
    assert response.headers["X-Correlation-ID"] == "framework-error"
    if status == 405:
        assert "GET" in response.headers["Allow"]
    assert json.loads(capsys.readouterr().out)["correlation_id"] == "framework-error"


@pytest.mark.parametrize("status", [401, 403, 409, 429, 503])
def test_http_exception_details_are_hidden_and_headers_preserved(
    status: int, capsys: pytest.CaptureFixture[str]
) -> None:
    app = create_app(Settings(_env_file=None))

    @app.get("/expected-error")
    def expected_error() -> None:
        raise HTTPException(
            status,
            detail={"private": "exception-secret"},
            headers={"Retry-After": "5", "WWW-Authenticate": "Bearer"},
        )

    with TestClient(app) as client:
        response = client.get("/expected-error")
    identifier = response.headers["X-Correlation-ID"]
    assert str(UUID(identifier)) == identifier
    assert response.json()["correlation_id"] == identifier
    assert response.status_code == status
    assert response.headers["Retry-After"] == "5"
    assert response.headers["WWW-Authenticate"] == "Bearer"
    output = capsys.readouterr().out
    assert "exception-secret" not in response.text + output
    if status >= 500:
        assert response.json()["error"]["code"] == "internal_error"


class ExampleInput(BaseModel):
    count: int


@pytest.mark.parametrize("body", ['{"count":"body-secret"}', '{"malformed-secret"'])
def test_invalid_input_is_not_reflected_in_response_or_logs(
    body: str, capsys: pytest.CaptureFixture[str]
) -> None:
    app = create_app(Settings(_env_file=None))

    @app.post("/validate")
    def validate(payload: ExampleInput) -> None:
        pass

    with TestClient(app) as client:
        response = client.post(
            "/validate", content=body, headers={"Content-Type": "application/json"}
        )
    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "validation_error", "message": "Request validation failed."},
        "correlation_id": response.headers["X-Correlation-ID"],
    }
    output = capsys.readouterr().out
    assert "secret" not in response.text + output
    assert len(output.splitlines()) == 1


def test_unexpected_failure_is_safe_correlated_and_logged_once(
    capsys: pytest.CaptureFixture[str],
) -> None:
    app = create_app(Settings(_env_file=None))

    @app.get("/failure")
    def failure() -> None:
        raise RuntimeError("private-exception-secret")

    # Default TestClient rethrows uncaught exceptions, so this exercises our error boundary.
    with TestClient(app) as client:
        response = client.get("/failure", headers={"X-Correlation-ID": "failure-123"})
        recovery = client.get("/health", headers={"X-Correlation-ID": "recovery-123"})
    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "An unexpected error occurred."},
        "correlation_id": "failure-123",
    }
    assert response.headers["X-Correlation-ID"] == "failure-123"
    assert recovery.status_code == 200
    entries = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(entries) == 2
    assert entries[0]["event"] == "request_failed"
    assert entries[0]["status_code"] == 500
    assert entries[0]["correlation_id"] == "failure-123"
    assert entries[0]["exception_type"] == "RuntimeError"
    assert entries[1]["correlation_id"] == "recovery-123"
    assert "private-exception-secret" not in response.text + json.dumps(entries)


def test_stream_failure_is_logged_and_rethrown_without_second_response(
    capsys: pytest.CaptureFixture[str],
) -> None:
    app = create_app(Settings(_env_file=None))
    sent: list[Message] = []

    async def stream(scope: Scope, receive: Receive, send: Send) -> None:
        await send({"type": "http.response.start", "status": 200, "headers": []})
        raise RuntimeError("stream-secret")

    async def run() -> None:
        async def receive() -> Message:
            return {"type": "http.request", "body": b""}

        async def send(message: Message) -> None:
            sent.append(message)

        await RequestLoggingMiddleware(stream, app.state.logger)(
            {"type": "http", "method": "GET", "headers": []}, receive, send
        )

    with pytest.raises(RuntimeError, match="stream-secret"):
        anyio.run(run)
    assert len(sent) == 1
    output = capsys.readouterr().out
    assert json.loads(output)["outcome"] == "failure"
    assert "stream-secret" not in output


def test_invalid_settings_fail_at_application_creation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "invalid-log-level")
    with pytest.raises(ValidationError):
        create_app()
