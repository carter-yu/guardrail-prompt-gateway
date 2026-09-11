"""Typed optimizer state. Reducers are last-write-wins on these fields."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from schemas.gateway import ErrorType, GatewayResponse, ProviderEnum
from schemas.refined import RefinedPromptSchema


class OptimizerState(BaseModel):
    raw_prompt: str
    optimized_prompt: str | None = None
    refined: RefinedPromptSchema | None = None
    model_target: ProviderEnum
    model_id: str
    step_count: int = 0
    max_steps: int = 5
    confirmed: bool = False
    confirmation_id: str | None = None
    correlation_id: str
    graph_run_id: str
    outcome: Literal["success", "failure", "skipped"] | None = None
    last_error_type: ErrorType | None = None
    response: GatewayResponse | None = None
    token_in: int = 0
    token_out: int = 0
    latency_ms: int = 0
    estimated_cost_usd: float = 0.0
    llm_calls: int = 0
    finish_reason: str | None = None
    last_text: str | None = None
    execute_prompt_version: str = "none"
    error_message: str | None = None
