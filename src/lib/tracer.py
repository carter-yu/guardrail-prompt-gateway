"""Tracer protocol. Slice 2: get_tracer() no-ops unless LANGFUSE_ENABLED."""

from __future__ import annotations

import os
from typing import Any, Protocol

import structlog

logger = structlog.get_logger(__name__)


class Tracer(Protocol):
    def span_llm(self, tel: Any, **attrs: Any) -> None: ...

    def span_tool(self, *, tool: str, correlation_id: str, dry_run: bool) -> None: ...


class NoOpTracer:
    def span_llm(self, tel: Any, **attrs: Any) -> None:
        return

    def span_tool(self, **kwargs: Any) -> None:
        return


def langfuse_enabled() -> bool:
    return os.getenv("LANGFUSE_ENABLED", "false").lower() in {"1", "true", "yes"}


def get_tracer() -> Tracer:
    """No-op when unset/false or when the SDK/keys fail. Never blocks boot."""
    if not langfuse_enabled():
        return NoOpTracer()
    try:
        import langfuse  # noqa: F401
    except Exception as exc:  # noqa: BLE001 — missing SDK is a no-op
        logger.warning(
            "langfuse_unavailable",
            component="tracer",
            outcome="skipped",
            error_type=type(exc).__name__,
        )
        return NoOpTracer()
    logger.warning(
        "langfuse_stub",
        component="tracer",
        outcome="skipped",
        error_message="Langfuse exporter not wired; using no-op",
    )
    return NoOpTracer()
