"""Slice 1 router (T1.1, T1.4) — Fake LLM only."""

from __future__ import annotations

import pytest
from structlog.testing import capture_logs

from lib.llm import FakeLLMClient, TelemetryLLMClient
from lib.logger import setup_logging
from schemas.gateway import ErrorType, GatewayRequest, ProviderEnum
from services.providers import default_model_id
from services.router import complete_request, get_client


@pytest.mark.parametrize("provider", [ProviderEnum.XAI, ProviderEnum.GOOGLE])
def test_route_xai_and_google_returns_schema(provider: ProviderEnum) -> None:
    """T1.1: routing to google or xai returns GatewayResponse; provider is requested."""
    asked: list[ProviderEnum] = []

    def factory(p: ProviderEnum, **kw: object) -> TelemetryLLMClient:
        asked.append(p)
        return TelemetryLLMClient(FakeLLMClient())

    response = complete_request(
        GatewayRequest(prompt="hello", provider=provider, correlation_id="c1"),
        llm_factory=factory,
    )
    assert asked == [provider]
    assert response.outcome == "success"
    assert response.provider is provider
    assert response.model_id == default_model_id(provider)
    assert response.text
    assert response.prompt_version == "none"
    assert response.correlation_id == "c1"
    assert response.error_type is None


def test_oversize_prompt_skipped_via_complete_request() -> None:
    """T1.2 via router: bypass Pydantic max_length, still skipped."""
    request = GatewayRequest.model_construct(
        prompt="x" * 2001,
        provider=ProviderEnum.XAI,
        correlation_id="long",
    )
    response = complete_request(
        request,
        llm_factory=lambda provider, **kw: TelemetryLLMClient(FakeLLMClient()),
    )
    assert response.outcome == "skipped"
    assert response.error_type == ErrorType.PROMPT_TOO_LONG
    assert response.llm_calls == 0


def test_timeout_retries_then_failure() -> None:
    """T1.4: TimeoutError retried twice (3 attempts) then outcome=failure."""
    setup_logging()
    inner = FakeLLMClient(fail_remaining=3, fail_with=TimeoutError)
    client = TelemetryLLMClient(inner)
    with capture_logs() as cap:
        response = complete_request(
            GatewayRequest(prompt="hello", provider=ProviderEnum.XAI, correlation_id="t14"),
            client=client,
        )
    assert response.outcome == "failure"
    assert response.error_type == ErrorType.TIMEOUT
    assert response.provider is ProviderEnum.XAI
    events = [e for e in cap if e.get("event") == "llm_call"]
    assert len(events) == 3
    assert [e.get("retry_count") for e in events] == [0, 1, 2]
    assert all(e.get("outcome") == "failure" for e in events)
    assert all(e.get("finish_reason") == "error" for e in events)


def test_get_client_wraps_injected_fake() -> None:
    wrapped = get_client(ProviderEnum.XAI, fake=FakeLLMClient())
    assert isinstance(wrapped, TelemetryLLMClient)
    assert wrapped.inner.provider == "fake"
