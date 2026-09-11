"""Tracer protocol. Slice 0: no-op only. Langfuse waits for Slice 2."""

from __future__ import annotations

from typing import Any, Protocol


class Tracer(Protocol):
    def span_llm(self, tel: Any, **attrs: Any) -> None: ...

    def span_tool(self, *, tool: str, correlation_id: str, dry_run: bool) -> None: ...


class NoOpTracer:
    def span_llm(self, tel: Any, **attrs: Any) -> None:
        return

    def span_tool(self, **kwargs: Any) -> None:
        return
