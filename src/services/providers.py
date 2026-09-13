"""Live provider factory. Slice 1: stubs only. Vendor SDKs lazy-imported later.

Why a factory instead of constructing ChatXAI at import
-------------------------------------------------------
KD-7: core code depends on ``lib.llm.LLMClient``. A module-level
``from langchain_xai import ChatXAI`` would run at pytest collection and
require the optional ``[live]`` extra. ``live_or_stub`` is the only place a
vendor SDK may eventually be imported, and even then *inside the function*.

Why stubs, not silent Fake, on the live path
--------------------------------------------
Missing ``XAI_API_KEY`` / ``GOOGLE_API_KEY`` is ``MISSING_CREDENTIALS``.
Key present but adapter body not shipped is ``NOT_IMPLEMENTED``. Both raise
``ProviderStubError``, which ``complete_llm`` must **not** retry (not a
timeout). Visible failure, not a surprise Fake reply that looks like Grok.

Pinned defaults (ADR 0002): xAI ``grok-4.3``, Gemini ``gemini-2.5-flash``.
The LLM does not pick the model id; the route enum + env defaults do.
"""

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
    """Slice 1 live inner client. complete() raises ProviderStubError.

    Implements ``LLMClient`` so ``TelemetryLLMClient`` can wrap it. The wrapper
    still emits ``llm_call`` with ``finish_reason=error`` before the exception
    propagates (T0.2 / KD-14).
    """

    def __init__(self, provider: ProviderEnum, error_type: ErrorType, message: str) -> None:
        self.provider = provider.value
        self.error_type = error_type
        self.message = message

    def complete(self, req: LLMRequest) -> LLMResult:
        del req
        raise ProviderStubError(self.error_type, self.message)


def default_model_id(provider: ProviderEnum, model_id: str | None = None) -> str:
    """Closed lookup. Unknown providers cannot appear: ProviderEnum is the allowlist."""
    if model_id:
        return model_id
    return DEFAULT_MODELS[provider]


def live_or_stub(provider: ProviderEnum, model_id: str | None = None) -> LLMClient:
    """No vendor SDK body in Slice 1. Missing key → MISSING_CREDENTIALS.

    Later live-smoke slice (out of 0–4): lazy-import ChatXAI first, fallback
    ``ChatOpenAI(base_url=https://api.x.ai/v1)``, Gemini via
    ChatGoogleGenerativeAI. ``max_retries=0`` on the vendor client so T1.4
    retry is owned in-process by ``complete_llm``.
    """
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
