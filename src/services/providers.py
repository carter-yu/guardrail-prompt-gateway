"""Live provider factory. Slice 1: stubs only. Vendor SDKs lazy-imported later."""

from __future__ import annotations

import os

from lib.llm import LLMClient, LLMRequest, LLMResult
from schemas.gateway import ErrorType, ProviderEnum

DEFAULT_MODELS = {
    ProviderEnum.XAI: "grok-4.3",
    ProviderEnum.GOOGLE: "gemini-2.5-flash",
    ProviderEnum.FAKE: "fake",
}

XAI_BASE_URL = "https://api.x.ai/v1"


class ProviderStubError(Exception):
    """Non-timeout live-path stub. complete_llm must not retry this."""

    def __init__(self, error_type: ErrorType, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type


class StubLLMClient:
    """Slice 1 live inner client. complete() raises ProviderStubError."""

    def __init__(self, provider: ProviderEnum, error_type: ErrorType, message: str) -> None:
        self.provider = provider.value
        self.error_type = error_type
        self.message = message

    def complete(self, req: LLMRequest) -> LLMResult:
        del req
        raise ProviderStubError(self.error_type, self.message)


def default_model_id(provider: ProviderEnum, model_id: str | None = None) -> str:
    if model_id:
        return model_id
    return DEFAULT_MODELS[provider]


def live_or_stub(provider: ProviderEnum, model_id: str | None = None) -> LLMClient:
    """No vendor SDK body in Slice 1. Missing key → MISSING_CREDENTIALS."""
    del model_id
    if provider is ProviderEnum.XAI:
        if not (os.environ.get("XAI_API_KEY") or "").strip():
            return StubLLMClient(
                provider,
                ErrorType.MISSING_CREDENTIALS,
                "XAI_API_KEY is not set",
            )
        return StubLLMClient(
            provider,
            ErrorType.NOT_IMPLEMENTED,
            "live xAI adapter is a later slice",
        )
    if provider is ProviderEnum.GOOGLE:
        if not (os.environ.get("GOOGLE_API_KEY") or "").strip():
            return StubLLMClient(
                provider,
                ErrorType.MISSING_CREDENTIALS,
                "GOOGLE_API_KEY is not set",
            )
        return StubLLMClient(
            provider,
            ErrorType.NOT_IMPLEMENTED,
            "live Gemini adapter is a later slice",
        )
    return StubLLMClient(
        ProviderEnum.FAKE,
        ErrorType.NOT_IMPLEMENTED,
        "unknown provider",
    )
