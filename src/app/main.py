"""FastAPI app: GET / UI, POST /api/v1/generate (graph.invoke), GET /health."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

from app.i18n import UI
from graph.optimizer import (
    build_graph,
    run_gateway_graph,
    skipped_response,
)
from guardrail_prompt_gateway import __version__
from lib.llm import FakeLLMClient, TelemetryLLMClient
from lib.tracer import get_tracer, langfuse_enabled
from schemas.gateway import ErrorType, GatewayRequest, GatewayResponse, ProviderEnum
from services.input_gate import check_input
from services.providers import default_model_id
from services.router import get_client

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


def _fake_factory(provider: ProviderEnum, **kw: object) -> TelemetryLLMClient:
    del provider, kw
    return TelemetryLLMClient(FakeLLMClient(), tracer=get_tracer())


def create_app(
    *,
    llm_factory=None,
    tracer=None,
    graph=None,
    confirmation_store=None,
) -> FastAPI:
    """Slice 3: llm_factory + tracer + graph. GATEWAY_USE_FAKE=true uses Fake LLM (no keys)."""
    del confirmation_store
    if llm_factory is None:
        if os.getenv("GATEWAY_USE_FAKE", "").lower() in {"1", "true", "yes"}:
            llm_factory = _fake_factory
        else:
            llm_factory = get_client
    app = FastAPI(title="guardrail-prompt-gateway", version=__version__)
    app.state.llm_factory = llm_factory
    app.state.tracer = tracer if tracer is not None else get_tracer()
    app.state.graph = graph if graph is not None else build_graph(get_client_fn=llm_factory)

    @app.exception_handler(RequestValidationError)
    def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        del request
        msg = str(exc.errors())
        error_type = ErrorType.PROMPT_TOO_LONG
        if "prompt" not in msg.lower() and "max_length" not in msg.lower():
            error_type = ErrorType.PROVIDER_ERROR
        body = GatewayResponse(
            outcome="skipped",
            provider=ProviderEnum.XAI,
            model_id=default_model_id(ProviderEnum.XAI),
            prompt_version="none",
            correlation_id="validation",
            llm_calls=0,
            error_type=error_type,
            error_message="request validation failed",
        )
        return JSONResponse(status_code=400, content=body.model_dump(mode="json"))

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        return TEMPLATES.TemplateResponse(request, "index.html", {"ui": UI})

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "version": __version__,
            "langfuse": langfuse_enabled(),
        }

    @app.post("/api/v1/generate")
    def generate(payload: GatewayRequest) -> JSONResponse:
        rejected = check_input(payload.prompt)
        if rejected is not None:
            response = skipped_response(payload, rejected.error_type, rejected.error_message)
        else:
            response = run_gateway_graph(payload, graph=app.state.graph)
        status = 400 if response.outcome == "skipped" else 200
        return JSONResponse(status_code=status, content=response.model_dump(mode="json"))

    return app


app = create_app()
