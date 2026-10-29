import json
from datetime import datetime
from io import StringIO
from uuid import UUID

import anyio
import pytest
from fastapi.testclient import TestClient
from starlette.types import Message, Receive, Scope, Send

from mortgage_pricing.config import Settings
from mortgage_pricing.logging_config import correlation_id, create_logger
from mortgage_pricing.main import create_app
from mortgage_pricing.request_logging import RequestLoggingMiddleware


def test_request_log_schema_and_correlation_propagation(capsys: pytest.CaptureFixture[str]) -> None:
    app = create_app(Settings(_env_file=None))
    with TestClient(app) as client:
        response = client.get(
            "/health?secret=query-secret", headers={"X-Correlation-ID": "case-123"}
        )

    entry = json.loads(capsys.readouterr().out)
    assert response.headers["X-Correlation-ID"] == "case-123"
    assert entry["correlation_id"] == "case-123"
    assert datetime.fromisoformat(entry["timestamp"]).utcoffset().total_seconds() == 0
    assert entry["level"] == "INFO"
    assert entry["event"] == "request_completed"
    assert entry["outcome"] == "success"
    assert entry["status_code"] == 200
    assert entry["route"] == "/health"
    assert entry["duration"] >= 0
    assert "query-secret" not in json.dumps(entry)


def test_maximum_length_id_is_preserved(capsys: pytest.CaptureFixture[str]) -> None:
    identifier = "x" * 64
    with TestClient(create_app(Settings(_env_file=None))) as client:
        response = client.get("/health", headers={"X-Correlation-ID": identifier})
    assert response.headers["X-Correlation-ID"] == identifier
    assert json.loads(capsys.readouterr().out)["correlation_id"] == identifier


@pytest.mark.parametrize("supplied", [None, "bad id", "x" * 65, "", "not/ascii", "é"])
def test_missing_or_invalid_ids_are_replaced(
    supplied: str | None, capsys: pytest.CaptureFixture[str]
) -> None:
    # Non-ASCII headers use Latin-1 bytes so they reach the ASGI validation boundary.
    headers = [] if supplied is None else [(b"X-Correlation-ID", supplied.encode("latin-1"))]
    with TestClient(create_app(Settings(_env_file=None))) as client:
        response = client.get("/health", headers=headers)

    identifier = response.headers["X-Correlation-ID"]
    assert str(UUID(identifier)) == identifier
    assert json.loads(capsys.readouterr().out)["correlation_id"] == identifier


def test_duplicate_ids_are_replaced(capsys: pytest.CaptureFixture[str]) -> None:
    with TestClient(create_app(Settings(_env_file=None))) as client:
        response = client.get(
            "/health", headers=[("X-Correlation-ID", "one"), ("X-Correlation-ID", "two")]
        )

    identifier = response.headers["X-Correlation-ID"]
    assert str(UUID(identifier)) == identifier
    assert json.loads(capsys.readouterr().out)["correlation_id"] == identifier


def test_request_data_is_excluded_on_failure(capsys: pytest.CaptureFixture[str]) -> None:
    with TestClient(create_app(Settings(_env_file=None))) as client:
        response = client.post(
            "/secret-path?token=query-secret",
            headers={"Authorization": "Bearer header-secret", "X-Correlation-ID": "failure-id"},
            json={"reason": "body-secret"},
        )

    output = capsys.readouterr().out
    entry = json.loads(output)
    assert response.status_code == 404
    assert response.headers["X-Correlation-ID"] == "failure-id"
    assert entry["level"] == "WARNING"
    assert entry["outcome"] == "failure"
    assert entry["route"] is None
    assert all(
        secret not in output
        for secret in ("secret-path", "query-secret", "header-secret", "body-secret")
    )


def test_exception_diagnostics_omit_message_and_reset_context(
    capsys: pytest.CaptureFixture[str],
) -> None:
    app = create_app(Settings(_env_file=None))

    @app.get("/failure")
    def fail() -> None:
        raise RuntimeError("sensitive-exception-message")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/failure", headers={"X-Correlation-ID": "error-id"})

    output = capsys.readouterr().out
    entry = json.loads(output)
    assert response.status_code == 500
    assert entry["correlation_id"] == "error-id"
    assert entry["event"] == "request_failed"
    assert entry["exception_type"] == "RuntimeError"
    assert entry["exception_frames"][-1]["function"] == "fail"
    assert "sensitive-exception-message" not in output
    assert correlation_id.get() is None


def test_app_logging_is_independent_and_respects_level(capsys: pytest.CaptureFixture[str]) -> None:
    first = create_app(Settings(_env_file=None, log_level="WARNING"))
    second = create_app(Settings(_env_file=None))
    with TestClient(first) as client:
        client.get("/health")
    assert capsys.readouterr().out == ""

    with TestClient(second) as client:
        client.get("/health")
    assert len(capsys.readouterr().out.splitlines()) == 1
    assert len(first.state.logger.handlers) == len(second.state.logger.handlers) == 1


def test_formatter_allows_domain_ids_and_excludes_unknown_fields() -> None:
    stream = StringIO()
    logger = create_logger("INFO", stream)
    logger.info(
        "decision_recorded", extra={"request_id": "r1", "version_id": "v1", "body": "secret"}
    )

    entry = json.loads(stream.getvalue())
    assert entry["request_id"] == "r1"
    assert entry["version_id"] == "v1"
    assert entry["correlation_id"] is None
    assert "secret" not in stream.getvalue()


def test_concurrent_requests_keep_context_separate_and_restore_it() -> None:
    stream = StringIO()
    logger = create_logger("INFO", stream)

    async def run() -> None:
        both_started = anyio.Event()
        count = 0

        async def endpoint(scope: Scope, receive: Receive, send: Send) -> None:
            nonlocal count
            count += 1
            if count == 2:
                both_started.set()
            await both_started.wait()
            logger.info(scope["path"])
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})

        middleware = RequestLoggingMiddleware(endpoint, logger)

        async def request(identifier: str) -> None:
            async def receive() -> Message:
                return {"type": "http.request", "body": b""}

            async def send(message: Message) -> None:
                pass

            await middleware(
                {
                    "type": "http",
                    "method": "GET",
                    "path": identifier,
                    "headers": [(b"x-correlation-id", identifier.encode())],
                },
                receive,
                send,
            )
            assert correlation_id.get() is None

        async with anyio.create_task_group() as group:
            group.start_soon(request, "request-a")
            group.start_soon(request, "request-b")

    anyio.run(run)
    events = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert len(events) == 4
    for entry in events:
        if entry["event"] != "request_completed":
            assert entry["event"] == entry["correlation_id"]
