"""Application-owned JSON logging without changing global logging handlers."""

import json
import logging
import sys
import traceback
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import TextIO

correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


class JsonFormatter(logging.Formatter):
    """Emit an allowlist of operational metadata and safe exception locations."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
            "correlation_id": correlation_id.get(),
            "outcome": getattr(record, "outcome", None),
            "duration": getattr(record, "duration", None),
        }
        for field in (
            "method",
            "route",
            "status_code",
            "actor_id",
            "request_id",
            "version_id",
            "assessment_id",
            "model_digest",
            "error_code",
            "users_created",
            "applications_created",
        ):
            if hasattr(record, field):
                entry[field] = getattr(record, field)
        if record.exc_info and record.exc_info[0] is not None:
            entry["exception_type"] = record.exc_info[0].__name__
            entry["exception_frames"] = [
                {"file": frame.filename, "line": frame.lineno, "function": frame.name}
                for frame in traceback.extract_tb(record.exc_info[2])
            ]
        return json.dumps(entry, ensure_ascii=True)


def create_logger(level: str, stream: TextIO | None = None) -> logging.Logger:
    """Create one independent logger per app, respecting its configured level."""
    logger = logging.Logger("mortgage_pricing", level=level)
    logger.propagate = False
    handler = logging.StreamHandler(stream if stream is not None else sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger
