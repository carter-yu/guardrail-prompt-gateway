"""Split router: complete_llm (provider+retry) vs complete_request (gate+llm).

Why two functions, not one ``complete(GatewayRequest)``
-------------------------------------------------------
KD-10 / ADR 0002. A single HTTP-shaped complete cannot:

- stamp telemetry ``node`` (graph needs ``refine_prompt`` / ``execute_prompt``)
- pass a per-node tool allowlist (``LLMRequest.tools``)
- avoid re-running the INPUT GATE on the *optimized* prompt
- keep provider-timeout retries separate from graph ``max_steps``

So:

- ``complete_llm`` — provider call + timeout + max 2 retries. No input gate.
  No tools fired. Does **not** emit ``llm_call`` (KD-14).
- ``complete_request`` — INPUT GATE then ``complete_llm`` with Slice-0
  ``node=complete``. Slice 1–2 library/HTTP path. Graph nodes must not call this.

Why ``get_client`` always returns ``TelemetryLLMClient``
-------------------------------------------------------
The wrapper is the sole OBSERVABILITY HOOK (tokens, latency, Langfuse). If a
caller could get a bare Fake/stub, T0.1/T2.2 would miss events and live calls
would be untraced. Tests inject Fake *inside* the wrapper, not instead of it.

Routing is a factory + enum, not a supervisor LLM. ``ProviderEnum`` is a
closed list (xai / google / fake). The model does not choose the vendor.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

from lib.llm import (
    FakeLLMClient,
    LLMClient,
    LLMRequest,
    LLMResult,
    Message,
    TelemetryLLMClient,
)
from lib.logger import SLICE0_NODE, SLICE0_PROMPT_VERSION, get_logger
from lib.tracer import Tracer
from schemas.gateway import ErrorType, GatewayRequest, GatewayResponse, ProviderEnum
from services.input_gate import check_input
from services.providers import (
    ProviderStubError,
    default_model_id,
    live_or_stub,
)

logger = get_logger(__name__)

# Constitution rule 20: retries bounded (max 2) and idempotent. This is the
# *provider* budget. Graph max_steps is a separate ceiling and must not retry
# these timeouts again.
MAX_RETRIES = 2
LLMFactory = Callable[..., LLMClient]


def get_client(
    provider: ProviderEnum,
    *,
    fake: LLMClient | None = None,
    model_id: str | None = None,
    tracer: Tracer | None = None,
) -> LLMClient:
    """Always returns TelemetryLLMClient wrapping Fake, injected fake, or a stub.

    Order is the deterministic route, not an LLM decision:

    1. Explicit ``fake=`` injection (pytest T1.1) — still asked for ``provider``
    2. ``ProviderEnum.FAKE`` — default FakeLLMClient
    3. Live path — ``live_or_stub`` (Slice 1: credentials check then stub)

    Vendor SDKs are lazy-imported behind ``live_or_stub``, never at this
    module's import time (KD-7), so collecting tests does not need langchain-xai.
    """
    if fake is not None:
        inner = fake
    elif provider is ProviderEnum.FAKE:
        inner = FakeLLMClient()
    else:
        inner = live_or_stub(provider, model_id)
    return TelemetryLLMClient(inner, tracer=tracer)


def complete_llm(req: LLMRequest, *, client: LLMClient) -> LLMResult:
    """Timeout + max 2 retries. Does not emit llm_call. Does not run input_gate.

    Retry policy (T1.4 / rule 20):

    - ``TimeoutError`` only — retry up to 2 times (3 attempts: retry_count 0..2)
    - Any other exception — re-raise immediately (no retry storm on 4xx)
    - Each attempt copies ``retry_count`` onto the request so the wrapper's
      ``llm_call`` event records which try this was. This function itself
      must not call ``emit_llm_call`` or counts double (KD-14).

    TOOL GATE is not here: this function never looks at ``req.tools`` to fire
    a tool. Authorization stays in ``execute_prompt`` / a future ``tools/gate``.
    """
    last: BaseException | None = None
    for attempt in range(1 + MAX_RETRIES):
        attempt_req = req.model_copy(update={"retry_count": attempt})
        try:
            return client.complete(attempt_req)
        except TimeoutError as exc:
            last = exc
            continue
        except Exception:
            raise
    assert last is not None
    raise last


def complete_request(
    request: GatewayRequest,
    *,
    client: LLMClient | None = None,
    llm_factory: LLMFactory = get_client,
) -> GatewayResponse:
    """Input gate then complete_llm. Graph nodes must not call this.

    Slice 1–2 library path. After Slice 3, HTTP uses ``graph.invoke`` instead.
    Kept so tests T1.* and any non-graph caller still have a one-shot complete
    that does not pretend to be an optimizer.
    """
    correlation_id = request.correlation_id or str(uuid.uuid4())
    requested_model = default_model_id(request.provider, request.model_id)
    # INPUT GATE: schema/length/PII/injection already enforced in check_input.
    # First failure wins; the provider is never called (llm_calls=0).
    rejected = check_input(request.prompt)
    if rejected is not None:
        return GatewayResponse(
            outcome="skipped",
            text=None,
            provider=request.provider,
            model_id=requested_model,
            prompt_version=SLICE0_PROMPT_VERSION,
            correlation_id=correlation_id,
            llm_calls=0,
            error_type=rejected.error_type,
            error_message=rejected.error_message,
        )

    if client is None:
        client = llm_factory(request.provider, model_id=requested_model)

    req = LLMRequest(
        messages=[Message(role="user", content=request.prompt)],
        model_id=requested_model,
        prompt_version=SLICE0_PROMPT_VERSION,
        node=SLICE0_NODE,
        correlation_id=correlation_id,
    )
    try:
        result = complete_llm(req, client=client)
    except TimeoutError as exc:
        logger.error(
            "complete_request_failed",
            component="router",
            outcome="failure",
            error_type=ErrorType.TIMEOUT.value,
            correlation_id=correlation_id,
        )
        return GatewayResponse(
            outcome="failure",
            text=None,
            provider=request.provider,
            model_id=requested_model,
            prompt_version=SLICE0_PROMPT_VERSION,
            correlation_id=correlation_id,
            llm_calls=1 + MAX_RETRIES,
            error_type=ErrorType.TIMEOUT,
            error_message=str(exc),
        )
    except ProviderStubError as exc:
        logger.error(
            "complete_request_failed",
            component="router",
            outcome="failure",
            error_type=exc.error_type.value,
            correlation_id=correlation_id,
        )
        return GatewayResponse(
            outcome="failure",
            text=None,
            provider=request.provider,
            model_id=requested_model,
            prompt_version=SLICE0_PROMPT_VERSION,
            correlation_id=correlation_id,
            llm_calls=1,
            error_type=exc.error_type,
            error_message=str(exc),
        )
    except Exception as exc:  # noqa: BLE001 — library boundary: map to PROVIDER_ERROR
        logger.error(
            "complete_request_failed",
            component="router",
            outcome="failure",
            error_type=ErrorType.PROVIDER_ERROR.value,
            correlation_id=correlation_id,
        )
        return GatewayResponse(
            outcome="failure",
            text=None,
            provider=request.provider,
            model_id=requested_model,
            prompt_version=SLICE0_PROMPT_VERSION,
            correlation_id=correlation_id,
            llm_calls=1,
            error_type=ErrorType.PROVIDER_ERROR,
            error_message=str(exc),
        )

    # KD-18: response.provider / model_id are the *requested* route. Telemetry
    # on the wrapper records the actual inner client (fake in default pytest).
    return GatewayResponse(
        outcome="success",
        text=result.text,
        provider=request.provider,
        model_id=requested_model,
        prompt_version=SLICE0_PROMPT_VERSION,
        correlation_id=correlation_id,
        latency_ms=0,
        token_in=result.token_in,
        token_out=result.token_out,
        llm_calls=1,
        finish_reason=result.finish_reason,
    )
