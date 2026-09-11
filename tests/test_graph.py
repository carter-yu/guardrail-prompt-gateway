"""Slice 3 LangGraph optimizer (T3.1–T3.3) — Fake LLM, no network."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.main import create_app
from graph.optimizer import build_graph, initial_state
from graph.state import OptimizerState
from lib.llm import DEFAULT_FAKE_TEXT, FakeLLMClient, LLMResult, TelemetryLLMClient
from schemas.gateway import ErrorType, GatewayRequest, ProviderEnum
from schemas.refined import RefinedPromptSchema
from services.providers import default_model_id

OSAKA = "find me tickets to Osaka"
REFINE_JSON = {
    "objective": "Find flights to Osaka",
    "origin": "HKG",
    "destination": "KIX",
    "departure_date": "2026-10-01",
    "return_date": None,
    "constraints": [],
    "language": "en",
}


def _result(text: str, *, token_in: int, token_out: int) -> LLMResult:
    return LLMResult(
        text=text,
        model_id="fake",
        provider="fake",
        finish_reason="stop",
        token_in=token_in,
        token_out=token_out,
    )


def _osaka_factory(**kw: object) -> TelemetryLLMClient:
    del kw
    return TelemetryLLMClient(
        FakeLLMClient(
            script={
                "refine_prompt": _result(json.dumps(REFINE_JSON), token_in=11, token_out=22),
                "execute_prompt": _result(DEFAULT_FAKE_TEXT, token_in=33, token_out=44),
            }
        )
    )


def test_osaka_expands_and_http_counters_sum() -> None:
    """T3.1: Osaka → origin/destination/dates; HTTP counters = sum of two Fake calls."""
    client = TestClient(create_app(llm_factory=lambda provider, **kw: _osaka_factory()))
    res = client.post(
        "/api/v1/generate",
        json={"prompt": OSAKA, "provider": "xai"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["outcome"] == "success"
    assert data["provider"] == "xai"
    assert data["model_id"] == default_model_id(ProviderEnum.XAI)
    assert data["llm_calls"] == 2
    assert data["token_in"] == 11 + 33
    assert data["token_out"] == 22 + 44
    refined = data["refined"]
    assert refined["origin"] == "HKG"
    assert refined["destination"] == "KIX"
    assert refined["departure_date"] == "2026-10-01"
    assert data["text"] == DEFAULT_FAKE_TEXT


def test_max_steps_one_fails_without_hang() -> None:
    """T3.2: max_steps=1 → MAX_STEPS_EXCEEDED, no hang."""
    graph = build_graph(get_client_fn=lambda provider, **kw: _osaka_factory())
    request = GatewayRequest(prompt=OSAKA, provider=ProviderEnum.XAI, correlation_id="t32")
    state = initial_state(request, max_steps=1)
    final = graph.invoke(state)
    out = OptimizerState.model_validate(final)
    assert out.outcome == "failure"
    assert out.last_error_type == ErrorType.MAX_STEPS_EXCEEDED
    assert out.response is not None
    assert out.response.outcome == "failure"
    assert out.response.error_type == ErrorType.MAX_STEPS_EXCEEDED
    assert out.step_count == 1
    assert out.refined is not None  # schema passed; budget stopped execute


def test_refine_output_conforms_to_schema() -> None:
    """T3.3: refine node output is RefinedPromptSchema; garbage → SCHEMA_INVALID."""
    graph = build_graph(get_client_fn=lambda provider, **kw: _osaka_factory())
    request = GatewayRequest(prompt=OSAKA, provider=ProviderEnum.XAI, correlation_id="t33")
    final = graph.invoke(initial_state(request))
    out = OptimizerState.model_validate(final)
    assert out.refined is not None
    parsed = RefinedPromptSchema.model_validate(out.refined.model_dump())
    assert parsed.origin == "HKG"
    assert parsed.destination == "KIX"
    assert parsed.departure_date is not None

    bad = TelemetryLLMClient(FakeLLMClient(script={"refine_prompt": _result("not-json", token_in=1, token_out=1)}))
    bad_graph = build_graph(get_client_fn=lambda provider, **kw: bad)
    failed = OptimizerState.model_validate(bad_graph.invoke(initial_state(request)))
    assert failed.outcome == "failure"
    assert failed.last_error_type == ErrorType.SCHEMA_INVALID
    assert failed.refined is None
    assert failed.llm_calls == 2  # one schema retry
