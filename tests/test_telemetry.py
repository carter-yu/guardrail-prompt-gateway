"""Slice 0 locked tests T0.1–T0.4 (offline Fake LLM)."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from structlog.testing import capture_logs

from lib.clock import Clock
from lib.llm import (
    FakeLLMClient,
    LLMRequest,
    Message,
    TelemetryLLMClient,
)
from lib.logger import (
    LLMCallTelemetry,
    emit_llm_call,
    setup_logging,
    telemetry_from_provider,
)
from lib.prices import PriceTable

FAMILY_TZ = ZoneInfo("Asia/Hong_Kong")
FIXED_NOW = datetime(2026, 9, 11, 12, 0, tzinfo=FAMILY_TZ)

REQUIRED_FIELDS = (
    "provider",
    "model_id",
    "prompt_version",
    "node",
    "latency_ms",
    "token_in",
    "token_out",
    "token_total",
    "finish_reason",
    "estimated_cost_usd",
    "price_table_version",
    "outcome",
    "correlation_id",
)


def _request(**kwargs: object) -> LLMRequest:
    base: dict[str, object] = {
        "messages": [Message(role="user", content="hi")],
        "model_id": "fake",
        "prompt_version": "none",
        "node": "complete",
        "correlation_id": "corr-t0",
    }
    base.update(kwargs)
    return LLMRequest(**base)  # type: ignore[arg-type]


def _assert_telemetry(event: dict, *, outcome: str) -> None:
    assert event.get("event") == "llm_call"
    assert event.get("outcome") == outcome
    for name in REQUIRED_FIELDS:
        assert name in event, f"missing {name}"


@pytest.fixture
def json_logs():
    setup_logging()
    with capture_logs() as cap:
        yield cap


def test_telemetry_success_has_section_3_1_fields(json_logs) -> None:
    """T0.1: logger emits all mandatory §3.1 fields on a successful fake call."""
    client = TelemetryLLMClient(
        FakeLLMClient(),
        clock=Clock(lambda: FIXED_NOW),
        prices=PriceTable(),
    )
    result = client.complete(_request())
    assert result.provider == "fake"
    events = [e for e in json_logs if e.get("event") == "llm_call"]
    assert events
    event = events[-1]
    _assert_telemetry(event, outcome="success")
    assert event["provider"] == "fake"
    assert event["model_id"] == "fake"
    assert event["node"] == "complete"
    assert event["prompt_version"] == "none"
    assert event["finish_reason"] == "stop"
    assert event["token_in"] == 0
    assert event["token_out"] == 0
    assert event["token_total"] == 0


def test_telemetry_failure_records_error_finish_reason(json_logs) -> None:
    """T0.2: failure still logs finish_reason=error and token/latency fields."""
    client = TelemetryLLMClient(
        FakeLLMClient(fail_next=RuntimeError("boom")),
        clock=Clock(lambda: FIXED_NOW),
        prices=PriceTable(),
    )
    with pytest.raises(RuntimeError, match="boom"):
        client.complete(_request())
    events = [e for e in json_logs if e.get("event") == "llm_call"]
    assert events
    event = events[-1]
    _assert_telemetry(event, outcome="failure")
    assert event["finish_reason"] == "error"
    assert event["token_in"] == 0
    assert event["token_out"] == 0
    assert "latency_ms" in event
    assert event["error_type"] == "RuntimeError"


def test_unknown_model_cost_is_zero(json_logs) -> None:
    """T0.3: unknown model_id → estimated_cost_usd=0.0."""
    prices = PriceTable()
    assert prices.estimate(model_id="definitely-not-a-model", token_in=1000, token_out=1000) == 0.0
    tel = telemetry_from_provider(
        {
            "outcome": "success",
            "finish_reason": "stop",
            "model_id": "no-such-model",
            "provider": "fake",
            "token_in": 1000,
            "token_out": 1000,
            "latency_ms": 1,
            "correlation_id": "corr-t03",
        },
        prices=prices,
        clock=Clock(lambda: FIXED_NOW),
    )
    assert tel.estimated_cost_usd == 0.0
    emit_llm_call(tel)
    events = [e for e in json_logs if e.get("event") == "llm_call"]
    assert events[-1]["estimated_cost_usd"] == 0.0


def test_coerce_survives_garbage_payload() -> None:
    """T0.4: telemetry_from_provider never raises on malformed payloads."""
    tel = telemetry_from_provider("not a dict")  # type: ignore[arg-type]
    assert isinstance(tel, LLMCallTelemetry)
    tel2 = telemetry_from_provider(
        {
            "token_in": "nope",
            "finish_reason": "??? ",
            "provider": "martian",
            "outcome": object(),
        }
    )
    assert tel2.token_in == 0
    assert tel2.finish_reason == "error"
    assert tel2.provider == "fake"
