"""Structured logging for the Dex backend.

Every module should create its own logger via ``get_logger(__name__)``.  The
root ``dex`` logger is configured once at startup through ``setup_logging``.
All output is JSON-formatted so it can be consumed by structured log
aggregators later.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1] is not None:
            payload["exception"] = self.formatException(record.exc_info)
        # Allow extra structured fields passed via ``extra={"data": {...}}``
        if hasattr(record, "data"):
            payload["data"] = record.data  # type: ignore[attr-defined]
        return json.dumps(payload, default=str)


def setup_logging(level: str = "INFO") -> None:
    """Configure the root ``dex`` logger.

    Call this once during application startup.  Subsequent calls are
    safe but will not add duplicate handlers.
    """
    root = logging.getLogger("dex")
    if root.handlers:
        return  # already configured
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root.addHandler(handler)
    root.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ``dex`` namespace.

    Example::

        logger = get_logger(__name__)
        logger.info("Exploration started", extra={"data": {"url": url}})
    """
    prefix = "dex."
    qualified = name if name.startswith(prefix) else f"{prefix}{name}"
    return logging.getLogger(qualified)
