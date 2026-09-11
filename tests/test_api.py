"""Slice 2 HTTP API (T2.1, T2.2) — Fake LLM, no network."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient

from app.main import create_app
from lib.llm import FakeLLMClient, TelemetryLLMClient
from schemas.gateway import ProviderEnum


def _fake_factory(provider: ProviderEnum, **kw: object) -> TelemetryLLMClient:
    del provider, kw
    return TelemetryLLMClient(FakeLLMClient())


def test_generate_returns_200_schema() -> None:
    """T2.1: POST /api/v1/generate → 200 + GatewayResponse fields."""
    client = TestClient(create_app(llm_factory=_fake_factory))
    res = client.post(
        "/api/v1/generate",
        json={"prompt": "hello", "provider": "xai"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["outcome"] == "success"
    assert data["provider"] == "xai"
    assert data["text"]
    assert "correlation_id" in data
    assert "latency_ms" in data


def test_skipped_pii_is_400() -> None:
    client = TestClient(create_app(llm_factory=_fake_factory))
    res = client.post(
        "/api/v1/generate",
        json={"prompt": "id A123456(7)", "provider": "xai"},
    )
    assert res.status_code == 400
    assert res.json()["outcome"] == "skipped"


def test_app_starts_without_langfuse_env(monkeypatch) -> None:
    """T2.2: missing Langfuse env does not prevent boot."""
    monkeypatch.delenv("LANGFUSE_ENABLED", raising=False)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    client = TestClient(create_app(llm_factory=_fake_factory))
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["langfuse"] is False
    assert client.get("/").status_code == 200
    assert os.getenv("LANGFUSE_ENABLED") is None
