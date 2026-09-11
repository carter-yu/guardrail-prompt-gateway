"""Fake LLM stub and telemetry wrapper (Slice 0)."""

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
    role: Literal["system", "developer", "user", "assistant", "tool"]
    content: str


class LLMRequest(BaseModel):
    messages: list[Message]
    model_id: str
    prompt_version: str
    node: str
    correlation_id: str
    temperature: float = 0.0
    max_tokens: int = 1024
    timeout_s: float = 30.0
    tools: list[str] = Field(default_factory=list)
    retry_count: int = 0


class ToolCall(BaseModel):
    name: str
    id: str
    args: dict[str, Any] = Field(default_factory=dict)


class LLMResult(BaseModel):
    text: str
    model_id: str
    provider: str
    finish_reason: str
    token_in: int
    token_out: int
    provider_request_id: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    raw_usage: dict[str, Any] = Field(default_factory=dict)


class LLMClient(Protocol):
    provider: str

    def complete(self, req: LLMRequest) -> LLMResult: ...


class FakeLLMClient:
    """Dumb stub. No network. No logging."""

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
    """Sole llm_call emitter. Wraps any LLMClient."""

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
        self.tracer = tracer if tracer is not None else NoOpTracer()
        self.clock = clock if clock is not None else Clock()
        self.prices = prices if prices is not None else PriceTable()

    def complete(self, req: LLMRequest) -> LLMResult:
        started = time.perf_counter()
        try:
            result = self.inner.complete(req)
        except Exception as exc:
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
