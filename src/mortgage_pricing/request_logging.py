"""ASGI request tracing that preserves context across asynchronous calls."""

import logging
import re
from time import perf_counter
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from mortgage_pricing.logging_config import correlation_id

_CORRELATION_ID = re.compile(rb"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp, logger: logging.Logger) -> None:
        self.app = app
        self.logger = logger

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        supplied = [value for key, value in scope["headers"] if key.lower() == b"x-correlation-id"]
        identifier = (
            supplied[0].decode("ascii")
            if len(supplied) == 1 and _CORRELATION_ID.fullmatch(supplied[0])
            else str(uuid4())
        )
        scope.setdefault("state", {})["correlation_id"] = identifier
        token = correlation_id.set(identifier)
        started = perf_counter()
        status_code = 500

        async def send_response(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                MutableHeaders(scope=message)["X-Correlation-ID"] = identifier
            await send(message)

        def metadata() -> dict[str, object]:
            route = scope.get("route")
            return {
                "method": scope["method"],
                "route": getattr(route, "path", None),
                "status_code": status_code,
                "outcome": "success" if status_code < 400 else "failure",
                "duration": round(perf_counter() - started, 6),
            }

        try:
            await self.app(scope, receive, send_response)
        except Exception:
            details = metadata()
            details["outcome"] = "failure"
            self.logger.exception("request_failed", extra=details)
            raise
        else:
            level = (
                logging.ERROR
                if status_code >= 500
                else logging.WARNING
                if status_code >= 400
                else logging.INFO
            )
            self.logger.log(level, "request_completed", extra=metadata())
        finally:
            correlation_id.reset(token)
