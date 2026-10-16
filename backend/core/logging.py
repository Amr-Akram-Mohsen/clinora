"""
core/logging.py

Structured JSON logging configuration for Clinora backend.

Responsibilities:
- Configure Python's logging subsystem to emit structured JSON records.
- Ensure correlation/request IDs can be included in log records via context vars.
- Provide a factory function so each module gets a named logger.
- Keep sensitive data out of log output (no passwords, tokens, or PHI).

Non-goals:
- Not an audit system. Audit events are written via AuditRepository at the
  application layer. This module is for operational/diagnostic logging only.

Usage:
    from core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("user_login_attempt", extra={"email": email})
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# ---------------------------------------------------------------------------
# Context variable for propagating correlation/request IDs through async tasks
# ---------------------------------------------------------------------------
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


class _JSONFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects.

    Each record includes:
      - timestamp (ISO-8601 UTC)
      - level
      - logger name
      - message
      - request_id (if set in context)
      - any extra fields passed to the log call
    """

    _EXCLUDED_ATTRS = frozenset(
        {
            "args", "created", "exc_info", "exc_text", "filename", "funcName",
            "levelname", "levelno", "lineno", "message", "module", "msecs",
            "msg", "name", "pathname", "process", "processName", "relativeCreated",
            "stack_info", "taskName", "thread", "threadName",
        }
    )

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()

        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
        }

        # Attach request ID from context if available
        rid = request_id_var.get()
        if rid:
            payload["request_id"] = rid

        # Attach exception info
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Attach any extra fields added by the caller
        for key, value in record.__dict__.items():
            if key not in self._EXCLUDED_ATTRS and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    """
    Set up root logger with JSON formatting to stdout.
    Call once at application startup in api/main.py.
    """
    root = logging.getLogger()
    root.setLevel(level)

    if root.handlers:
        # Avoid duplicate handlers if called multiple times (e.g., in tests)
        root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JSONFormatter())
    root.addHandler(handler)

    # Suppress noisy third-party loggers in production
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Use __name__ as the name convention."""
    return logging.getLogger(name)
