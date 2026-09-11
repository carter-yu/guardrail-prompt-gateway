"""Structured logging for guardrail-prompt-gateway (Phase 0: stdout).

Boundary fields follow docs/ground-rules.md §3: timestamp, level, component,
event, outcome, duration_ms, error_type / error_message, correlation_id.

File sinks and class-A purge land when a long-running service exists.
Default pytest uses stdout only.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

_configured = False


def setup_logging(level: str = "INFO") -> None:
    """Configure structlog once. Safe to call repeatedly."""
    global _configured
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=numeric)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric),
        cache_logger_on_first_use=True,
    )
    _configured = True


def get_logger(name: str) -> Any:
    """Return a bound structlog logger."""
    if not _configured:
        setup_logging()
    return structlog.get_logger(name)
