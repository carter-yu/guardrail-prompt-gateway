"""Tracer protocol. Slice 2: get_tracer() no-ops unless LANGFUSE_ENABLED.

OBSERVABILITY HOOK (constitution rule 19 / KD-14)
-------------------------------------------------
Langfuse is **observability**, not source of truth. The app must boot if the
SDK, keys, or host are missing (T2.2). ``TelemetryLLMClient`` type-depends on
this protocol, **not** on the Langfuse package — Slice 0 shipped ``NoOpTracer``
only; Slice 2 added ``get_tracer()`` with a lazy import.

Span attributes reuse §3.1 field names so logs and traces join on
``correlation_id``. A real exporter is still a stub in Slices 0–4: even when
the SDK imports, we return ``NoOpTracer`` plus a WARNING rather than failing
the family demo because the dashboard is down.
"""

from __future__ import annotations

import os
from typing import Any, Protocol

import structlog

logger = structlog.get_logger(__name__)


class Tracer(Protocol):
    """Lifecycle hooks the LLM wrapper and (later) tool gate call.

    ``span_llm`` receives the already-built ``LLMCallTelemetry`` so exporters
    do not re-parse vendor dicts. ``span_tool`` is the Slice 4 HITL/dry-run
    hook; Slice 3 does not call it because the tool allowlist is empty.
    """

    def span_llm(self, tel: Any, **attrs: Any) -> None: ...

    def span_tool(self, *, tool: str, correlation_id: str, dry_run: bool) -> None: ...


class NoOpTracer:
    """Default tracer. Drop-in so tests and Mini demos need no Langfuse env."""

    def span_llm(self, tel: Any, **attrs: Any) -> None:
        return

    def span_tool(self, **kwargs: Any) -> None:
        return


def langfuse_enabled() -> bool:
    """Closed boolean from env. Anything other than 1/true/yes is off."""
    return os.getenv("LANGFUSE_ENABLED", "false").lower() in {"1", "true", "yes"}


def get_tracer() -> Tracer:
    """No-op when unset/false or when the SDK/keys fail. Never blocks boot.

    OBSERVABILITY HOOK — factory. HTTP ``GET /health`` reports
    ``langfuse_enabled()`` (the *intent* flag), not whether an exporter is
    wired. That keeps T2.2 honest: the process starts either way.
    """
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
