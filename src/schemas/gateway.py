"""Slice 1 gateway schemas. ErrorType is extended in later slices, never free-typed.

Payload contracts at the HTTP seam
----------------------------------
Constitution rule 7: the LLM is a component, not source of truth. These
Pydantic models are the **request/response contract**. FastAPI validates
``GatewayRequest`` before the INPUT GATE; nodes must not invent extra keys
on the way out.

INPUT GATE (schema half)
------------------------
``prompt`` ``max_length=2000`` is the schema half of the length gate. The
service layer (``check_input``) still logs ``PROMPT_TOO_LONG`` for oversize
that bypasses validation. **Reject, do not truncate** — truncation could
still send a sliced secret to a provider (KD-11 / T1.2).

KD-18: ``GatewayResponse.provider`` / ``model_id`` are the *requested* route.
Telemetry records the actual inner client (``fake`` in default pytest).

KD-17: after Slice 3, token/latency/cost on the response are **graph sums**.
``prompt_version`` is the execute sentinel (``none``), not the refine file.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal, Self

from pydantic import BaseModel, Field, model_validator


class ProviderEnum(StrEnum):
    """Closed route list. The model does not choose the vendor (ADR 0002)."""

    XAI = "xai"
    GOOGLE = "google"
    FAKE = "fake"


class ErrorType(StrEnum):
    """Never free-typed in nodes. Extend this enum per slice.

    A stringly-typed ``error_type`` would let a node invent ``oops`` and break
    the UI/log contract. Tests assert members. Slice 4 names are reserved here
    so the HTTP schema does not churn when HITL lands.
    """

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
    """Family/HTTP inbound. No ``node``, ``tools``, or ``prompt_version``.

    Those live on ``LLMRequest`` so a client cannot set the graph node or the
    tool allowlist (KD-10). Slice 4 confirm is ``confirmation_id`` +
    ``confirmed=true`` with no tool-args field — args load from the store.
    """

    # INPUT GATE: Pydantic length. Service layer still checks and logs skipped.
    prompt: str = Field(default="", max_length=2000)
    provider: ProviderEnum = ProviderEnum.XAI
    model_id: str | None = None
    confirmed: bool = False
    confirmation_id: str | None = None
    correlation_id: str | None = None

    @model_validator(mode="after")
    def prompt_required_unless_confirming(self) -> Self:
        # INPUT GATE: empty prompt is invalid unless this is a Slice 4 confirm.
        if self.confirmation_id:
            return self
        if not self.prompt.strip():
            raise ValueError("prompt required unless confirmation_id is set")
        return self


class GatewayResponse(BaseModel):
    """HTTP outbound. ``outcome`` is a closed Literal — UI branches on it.

    ``failure`` is HTTP 200 with this body (architecture HTTP table): the Mini
    form renders the error on the same card. ``skipped`` is HTTP 400 (input
    gate). Field order is the original Slice 1 order (dump stability).
    """

    outcome: Literal["success", "failure", "skipped"]
    text: str | None = None
    provider: ProviderEnum
    model_id: str
    prompt_version: str
    correlation_id: str
    # KD-17 graph sums (Slice 0–2 were a single call; Slice 3+ add both nodes).
    latency_ms: int = 0
    token_in: int = 0
    token_out: int = 0
    estimated_cost_usd: float = 0.0
    llm_calls: int = 1
    finish_reason: str | None = None
    error_type: ErrorType | None = None
    error_message: str | None = None
    # Slice 4 HITL / tool fields — present now so the JSON shape is stable.
    dry_run: bool = False
    tool: str | None = None
    confirmation_id: str | None = None
    proposed_args: dict[str, Any] | None = None
    quotes: list[Any] | None = None
    # OUTPUT GATE product from refine (Slice 3+). Dict dump, not a live model.
    refined: dict[str, Any] | None = None
