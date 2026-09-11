"""Slice 0 telemetry: coerce vendor dicts, emit strict llm_call events as JSON."""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import structlog
from pydantic import BaseModel, ValidationError

from lib.clock import Clock
from lib.prices import PriceTable

SLICE0_NODE = "complete"
SLICE0_PROMPT_VERSION = "none"

_configured = False
_clock = Clock()
_prices = PriceTable()


class LLMCallTelemetry(BaseModel):
    timestamp: datetime
    level: Literal["info", "warning", "error"] = "info"
    component: str = "llm_client"
    event: Literal["llm_call"] = "llm_call"
    outcome: Literal["success", "failure", "partial", "skipped"]
    duration_ms: int
    correlation_id: str
    error_type: str | None = None
    error_message: str | None = None
    provider: Literal["xai", "google", "openai", "anthropic", "local", "fake"]
    model_id: str
    prompt_version: str
    node: str
    latency_ms: int
    token_in: int
    token_out: int
    token_total: int
    finish_reason: Literal["stop", "length", "tool_calls", "content_filter", "error"]
    stream: bool = False
    retry_count: int = 0
    provider_request_id: str | None = None
    token_cached: int | None = None
    ttft_ms: int | None = None
    estimated_cost_usd: float = 0.0
    price_table_version: str
    graph_run_id: str | None = None
    step: int | None = None
    tool: str | None = None
    tool_call_id: str | None = None
    validation_outcome: Literal["pass", "retry", "fail"] | None = None
    temperature: float | None = None
    max_tokens: int | None = None


def setup_logging(*, level: str = "INFO", log_dir: Path | None = None) -> None:
    """JSON structlog for llm_call events. Does not configure hello ConsoleRenderer."""
    global _configured
    del log_dir  # file sink waits until Slice 2
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=numeric)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric),
        cache_logger_on_first_use=True,
    )
    _configured = True


def get_logger(name: str) -> Any:
    if not _configured:
        setup_logging()
    return structlog.get_logger(name)


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def telemetry_from_provider(raw: dict[str, Any], **defaults: Any) -> LLMCallTelemetry:
    """The only entry that sees vendor/Fake dicts. Never raises (T0.4)."""
    if not isinstance(raw, dict):
        raw = {}
    merged: dict[str, Any] = {**defaults, **raw}
    prices = defaults.get("prices") or _prices
    if not isinstance(prices, PriceTable):
        prices = _prices
    clock = defaults.get("clock") or _clock
    if not isinstance(clock, Clock):
        clock = _clock

    token_in = _int_or_zero(merged.get("token_in"))
    token_out = _int_or_zero(merged.get("token_out"))
    latency_ms = _int_or_zero(merged.get("latency_ms"))
    model_id = str(merged.get("model_id") or "fake")
    provider = merged.get("provider") or "fake"
    if provider not in ("xai", "google", "openai", "anthropic", "local", "fake"):
        provider = "fake"
    finish = merged.get("finish_reason") or "error"
    if finish not in ("stop", "length", "tool_calls", "content_filter", "error"):
        finish = "error"
    outcome = merged.get("outcome")
    if outcome not in ("success", "failure", "partial", "skipped"):
        outcome = "failure" if finish == "error" else "success"
    level = merged.get("level") or ("error" if outcome == "failure" else "info")
    if level not in ("info", "warning", "error"):
        level = "info"
    correlation_id = str(merged.get("correlation_id") or "unknown")
    prompt_version = str(merged.get("prompt_version") or SLICE0_PROMPT_VERSION)
    node = str(merged.get("node") or SLICE0_NODE)
    timestamp = merged.get("timestamp")
    if not isinstance(timestamp, datetime):
        timestamp = clock.now()
    try:
        return LLMCallTelemetry(
            timestamp=timestamp,
            level=level,
            component=str(merged.get("component") or "llm_client"),
            event="llm_call",
            outcome=outcome,
            duration_ms=_int_or_zero(merged.get("duration_ms")) or latency_ms,
            correlation_id=correlation_id,
            error_type=(
                str(merged["error_type"]) if merged.get("error_type") is not None else None
            ),
            error_message=(
                str(merged["error_message"])
                if merged.get("error_message") is not None
                else None
            ),
            provider=provider,
            model_id=model_id,
            prompt_version=prompt_version,
            node=node,
            latency_ms=latency_ms,
            token_in=token_in,
            token_out=token_out,
            token_total=token_in + token_out,
            finish_reason=finish,
            stream=bool(merged.get("stream") or False),
            retry_count=_int_or_zero(merged.get("retry_count")),
            provider_request_id=(
                str(merged["provider_request_id"])
                if merged.get("provider_request_id")
                else None
            ),
            estimated_cost_usd=prices.estimate(
                model_id=model_id, token_in=token_in, token_out=token_out
            ),
            price_table_version=str(
                merged.get("price_table_version") or prices.version
            ),
            temperature=merged.get("temperature"),
            max_tokens=merged.get("max_tokens"),
        )
    except (ValidationError, TypeError, ValueError):
        return LLMCallTelemetry(
            timestamp=clock.now(),
            level="error",
            outcome="failure",
            duration_ms=0,
            correlation_id=correlation_id,
            provider="fake",
            model_id="fake",
            prompt_version=SLICE0_PROMPT_VERSION,
            node=SLICE0_NODE,
            latency_ms=0,
            token_in=0,
            token_out=0,
            token_total=0,
            finish_reason="error",
            estimated_cost_usd=0.0,
            price_table_version=prices.version,
            error_type="coerce_failed",
        )


def emit_llm_call(tel: LLMCallTelemetry) -> None:
    """Strict. Raises if ``tel`` is not a valid model."""
    if not isinstance(tel, LLMCallTelemetry):
        raise TypeError("emit_llm_call requires LLMCallTelemetry")
    payload = tel.model_dump(mode="json")
    if tel.level != "debug":
        payload.pop("temperature", None)
        payload.pop("max_tokens", None)
    log = get_logger("lib.logger")
    method = getattr(log, tel.level, log.info)
    event_name = payload.pop("event")
    method(event_name, **payload)
