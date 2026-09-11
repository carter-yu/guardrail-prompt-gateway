"""Split router: complete_llm (provider+retry) vs complete_request (gate+llm)."""

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

MAX_RETRIES = 2
LLMFactory = Callable[..., LLMClient]


def get_client(
    provider: ProviderEnum,
    *,
    fake: LLMClient | None = None,
    model_id: str | None = None,
    tracer: Tracer | None = None,
) -> LLMClient:
    """Always returns TelemetryLLMClient wrapping Fake, injected fake, or a stub."""
    if fake is not None:
        inner = fake
    elif provider is ProviderEnum.FAKE:
        inner = FakeLLMClient()
    else:
        inner = live_or_stub(provider, model_id)
    return TelemetryLLMClient(inner, tracer=tracer)


def complete_llm(req: LLMRequest, *, client: LLMClient) -> LLMResult:
    """Timeout + max 2 retries. Does not emit llm_call. Does not run input_gate."""
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
    """Input gate then complete_llm. Graph nodes must not call this."""
    correlation_id = request.correlation_id or str(uuid.uuid4())
    requested_model = default_model_id(request.provider, request.model_id)
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
