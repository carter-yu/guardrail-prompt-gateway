"""Fake LLM stub and telemetry wrapper (Slice 0).

Why a Protocol instead of importing LangChain Chat models here
--------------------------------------------------------------
KD-7 / ADR 0002: core code depends on ``LLMClient``. Vendor SDKs
(``langchain_xai.ChatXAI``, Gemini, OpenAI-compatible xAI) live only behind
``services.providers.live_or_stub`` and are lazy-imported. A module-level
LangChain import would pull optional extras at pytest collection time.

Why Fake is dumb and TelemetryLLMClient is the only emitter
-----------------------------------------------------------
KD-14: ``FakeLLMClient`` returns ``LLMResult`` or raises — it does not log.
``TelemetryLLMClient`` wraps *any* inner client and is the sole OBSERVABILITY
HOOK for ``llm_call`` + ``tracer.span_llm``. If Fake logged too, token counts
would double and T0.1 would be untestable.

TOOL GATE contract (KD-15)
--------------------------
A tool proposal exists only if ``LLMResult.tool_calls`` is a list of
``ToolCall`` objects. Text-only JSON in ``text`` is **not** a tool call.
Slice 3 execute still passes ``tools=[]``; Slice 4 will resolve names via a
static dict, never ``eval`` / dynamic import of a model-supplied string.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Callable, Mapping
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

from lib.clock import Clock
from lib.logger import emit_llm_call, telemetry_from_provider
from lib.prices import PriceTable
from lib.tracer import NoOpTracer, Tracer

DEFAULT_FAKE_TEXT = "Hello from Fake LLM. （假模型回覆）"


class Message(BaseModel):
    """One chat turn. Roles are a closed Literal — the model cannot invent ``admin``."""

    role: Literal["system", "developer", "user", "assistant", "tool"]
    content: str


class LLMRequest(BaseModel):
    """Provider-facing payload. Graph nodes stamp ``node`` / ``prompt_version`` here.

    This is *not* ``GatewayRequest``. HTTP has no ``node`` or ``tools``; putting
    those on the HTTP schema would leak graph internals to the family form and
    let a client set the allowlist (KD-10).
    """

    messages: list[Message]
    model_id: str
    # Constitution rule 16: every call records which prompt file/version ran.
    prompt_version: str
    # LangGraph node name (or Slice-0 sentinel ``complete``). Telemetry copies this.
    node: str
    correlation_id: str
    # Extraction / routing default is 0 (rule 16). Logged at DEBUG / Langfuse only.
    temperature: float = 0.0
    max_tokens: int = 1024
    timeout_s: float = 30.0
    # TOOL GATE: allowlist of tool *names* for this node. Empty = no tools may run.
    tools: list[str] = Field(default_factory=list)
    # Set by complete_llm per attempt (0, 1, 2). Wrapper copies onto llm_call.
    retry_count: int = 0


class ToolCall(BaseModel):
    """Structured tool proposal. Never parsed from assistant prose (KD-15).

    ``name`` must still pass the per-node allowlist before anything executes.
    ``args`` is an untrusted dict — Slice 4 validates it with a Pydantic schema
    before the mock ``flight_search`` runs.
    """

    name: str
    id: str
    args: dict[str, Any] = Field(default_factory=dict)


class LLMResult(BaseModel):
    """Normalized provider result. Adapters map vendor payloads into this shape.

    ``provider`` / ``model_id`` here are the *actual* inner client (``fake`` in
    pytest). HTTP ``GatewayResponse`` still echoes the *requested* route (KD-18).
    """

    text: str
    model_id: str
    provider: str
    finish_reason: str
    token_in: int
    token_out: int
    provider_request_id: str | None = None
    # TOOL GATE input: empty means "no tool", even if ``text`` looks like JSON.
    tool_calls: list[ToolCall] = Field(default_factory=list)
    raw_usage: dict[str, Any] = Field(default_factory=dict)


class LLMClient(Protocol):
    """Seam every caller uses. Fake, stub, and future ChatXAI all satisfy this."""

    provider: str

    def complete(self, req: LLMRequest) -> LLMResult: ...


class FakeLLMClient:
    """Dumb stub. No network. No logging.

    Script keys are **node names** (``complete``, ``refine_prompt``,
    ``execute_prompt``), not correlation ids. That keeps tests about graph
    topology rather than request identity. Default refine output is valid
    ``RefinedPromptSchema`` JSON so Slice 3 happy-path tests need no script;
    Osaka is a substring branch for T3.1.

    ``fail_remaining`` exists so T1.4 can prove ``complete_llm`` retries
    timeouts three times — the *wrapper* still emits one ``llm_call`` per try.
    """

    provider = "fake"

    def __init__(
        self,
        script: Mapping[str, LLMResult] | Callable[[LLMRequest], LLMResult] | None = None,
        *,
        fail_next: BaseException | None = None,
        fail_remaining: int = 0,
        fail_with: type[BaseException] = TimeoutError,
    ) -> None:
        self._script = script
        self.fail_next = fail_next
        self.fail_remaining = fail_remaining
        self.fail_with = fail_with

    def complete(self, req: LLMRequest) -> LLMResult:
        if self.fail_remaining > 0:
            self.fail_remaining -= 1
            raise self.fail_with("provider timeout")
        if self.fail_next is not None:
            exc = self.fail_next
            self.fail_next = None
            raise exc
        if callable(self._script):
            return self._script(req)
        if isinstance(self._script, Mapping) and req.node in self._script:
            return self._script[req.node]
        if req.node == "refine_prompt":
            # Default OUTPUT GATE fixture: schema-valid JSON, tokens=0 (T0.1 fake).
            user = next((m.content for m in reversed(req.messages) if m.role == "user"), "Respond")
            payload = {
                "objective": user.strip() or "Respond to the user",
                "origin": None,
                "destination": None,
                "departure_date": None,
                "return_date": None,
                "constraints": [],
                "language": "mixed",
            }
            if "osaka" in user.lower():
                payload.update(
                    {
                        "objective": "Find flights to Osaka",
                        "origin": "HKG",
                        "destination": "KIX",
                        "departure_date": "2026-10-01",
                        "language": "en",
                    }
                )
            return LLMResult(
                text=json.dumps(payload),
                model_id="fake",
                provider="fake",
                finish_reason="stop",
                token_in=0,
                token_out=0,
            )
        return LLMResult(
            text=DEFAULT_FAKE_TEXT,
            model_id="fake",
            provider="fake",
            finish_reason="stop",
            token_in=0,
            token_out=0,
        )


class TelemetryLLMClient:
    """Sole llm_call emitter. Wraps any LLMClient.

    OBSERVABILITY HOOK (KD-14) — this ``complete`` is the only place that:

    1. Measures wall-clock latency around ``inner.complete``
    2. Coerces usage into ``LLMCallTelemetry`` (tokens, latency, cost table)
    3. Emits the structured ``llm_call`` log (constitution §3.1)
    4. Forwards the same payload to ``tracer.span_llm`` (Langfuse or no-op)

    On exception it still emits ``finish_reason=error`` with tokens present
    (0 if unknown) then re-raises so ``complete_llm`` can retry timeouts.
    ``complete_llm`` must not emit — otherwise retry_count 0..2 would double.
    """

    def __init__(
        self,
        inner: LLMClient,
        *,
        tracer: Tracer | None = None,
        clock: Clock | None = None,
        prices: PriceTable | None = None,
    ) -> None:
        self.inner = inner
        self.provider = getattr(inner, "provider", "fake")
        # Default no-op: app runs with LANGFUSE_ENABLED=false (rule 19).
        self.tracer = tracer if tracer is not None else NoOpTracer()
        self.clock = clock if clock is not None else Clock()
        self.prices = prices if prices is not None else PriceTable()

    def complete(self, req: LLMRequest) -> LLMResult:
        started = time.perf_counter()
        try:
            result = self.inner.complete(req)
        except Exception as exc:
            # OBSERVABILITY HOOK — failure path: still count latency + emit + span.
            latency_ms = int((time.perf_counter() - started) * 1000)
            tel = telemetry_from_provider(
                {
                    "outcome": "failure",
                    "finish_reason": "error",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "token_in": 0,
                    "token_out": 0,
                    "latency_ms": latency_ms,
                    "provider": getattr(self.inner, "provider", "fake"),
                    "model_id": "fake",
                },
                node=req.node,
                prompt_version=req.prompt_version,
                correlation_id=req.correlation_id,
                retry_count=req.retry_count,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
                clock=self.clock,
                prices=self.prices,
            )
            emit_llm_call(tel)
            self.tracer.span_llm(tel)
            raise
        # OBSERVABILITY HOOK — success path: tokens from the result, latency here.
        latency_ms = int((time.perf_counter() - started) * 1000)
        tel = telemetry_from_provider(
            {
                "outcome": "success",
                "finish_reason": result.finish_reason,
                "token_in": result.token_in,
                "token_out": result.token_out,
                "latency_ms": latency_ms,
                "provider": result.provider,
                "model_id": result.model_id,
                "provider_request_id": result.provider_request_id,
            },
            node=req.node,
            prompt_version=req.prompt_version,
            correlation_id=req.correlation_id,
            retry_count=req.retry_count,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            clock=self.clock,
            prices=self.prices,
        )
        emit_llm_call(tel)
        self.tracer.span_llm(tel)
        return result


def demo_fake_call() -> None:
    """CLI smoke: one Fake complete with JSON llm_call."""
    from lib.logger import setup_logging

    setup_logging()
    client = TelemetryLLMClient(FakeLLMClient())
    client.complete(
        LLMRequest(
            messages=[Message(role="user", content="hello")],
            model_id="fake",
            prompt_version="none",
            node="complete",
            correlation_id=str(uuid.uuid4()),
        )
    )
