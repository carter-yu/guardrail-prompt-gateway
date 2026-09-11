"""Slice 1 gateway schemas. ErrorType is extended in later slices, never free-typed."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal, Self

from pydantic import BaseModel, Field, model_validator


class ProviderEnum(StrEnum):
    XAI = "xai"
    GOOGLE = "google"
    FAKE = "fake"


class ErrorType(StrEnum):
    """Never free-typed in nodes. Extend this enum per slice."""

    PII_BLOCKED = "pii_blocked"
    PROMPT_TOO_LONG = "prompt_too_long"
    INJECTION_TOKEN = "injection_token"
    TIMEOUT = "timeout"
    MISSING_CREDENTIALS = "missing_credentials"
    NOT_IMPLEMENTED = "not_implemented"
    PROVIDER_ERROR = "provider_error"
    SCHEMA_INVALID = "schema_invalid"
    MAX_STEPS_EXCEEDED = "max_steps_exceeded"
    TOOL_BLOCKED = "tool_blocked"
    EMPTY_TOOL_RESULT = "empty_tool_result"
    UNKNOWN_CONFIRMATION = "unknown_confirmation"
    ALREADY_EXECUTED = "already_executed"
    EXPIRED_CONFIRMATION = "expired_confirmation"


class GatewayRequest(BaseModel):
    prompt: str = Field(default="", max_length=2000)
    provider: ProviderEnum = ProviderEnum.XAI
    model_id: str | None = None
    confirmed: bool = False
    confirmation_id: str | None = None
    correlation_id: str | None = None

    @model_validator(mode="after")
    def prompt_required_unless_confirming(self) -> Self:
        if self.confirmation_id:
            return self
        if not self.prompt.strip():
            raise ValueError("prompt required unless confirmation_id is set")
        return self


class GatewayResponse(BaseModel):
    outcome: Literal["success", "failure", "skipped"]
    text: str | None = None
    provider: ProviderEnum
    model_id: str
    prompt_version: str
    correlation_id: str
    latency_ms: int = 0
    token_in: int = 0
    token_out: int = 0
    estimated_cost_usd: float = 0.0
    llm_calls: int = 1
    finish_reason: str | None = None
    error_type: ErrorType | None = None
    error_message: str | None = None
    dry_run: bool = False
    tool: str | None = None
    confirmation_id: str | None = None
    proposed_args: dict[str, Any] | None = None
    quotes: list[Any] | None = None
    refined: dict[str, Any] | None = None
