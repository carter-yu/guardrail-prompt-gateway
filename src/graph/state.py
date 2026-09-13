"""Typed LangGraph state for the prompt-optimizer graph.

Why a Pydantic model instead of a loose dict or LangChain ``AgentState``
--------------------------------------------------------------------
Constitution rule 8 / §2.4: the graph is an *explicit* state machine, not a
hidden orchestrator. Every field a node may read or write is declared here.
A bag of strings would let a node invent keys; a prebuilt agent state would
hide messages, tool scratchpads, and recursion inside LangGraph.

Payload contract
----------------
HTTP ``GatewayRequest`` is mapped into this object *once*
(``graph.optimizer.initial_state``). Nodes never re-parse the HTTP body and
never call ``complete_request`` (that would re-run the input gate on the
*optimized* prompt — KD-10). Downstream HTTP reads ``response`` plus the
accumulator fields, not model prose.

Reducer policy (last-write-wins, not a hidden add)
--------------------------------------------------
``StateGraph(OptimizerState)`` uses LangGraph's default Pydantic reducer:
**last write wins**. There are no ``Annotated[..., operator.add]`` reducers.
Token / latency / cost sums are therefore computed *inside* the nodes
(``_add_usage`` in ``optimizer.py``) and written back as a single replacement
value. That keeps addition deterministic and unit-testable without hiding it
in a graph-level reducer the reader cannot see.

Topology that consumes this state (ADR 0003)::

    START → refine_prompt → execute_prompt → END
                        ↘     failed     ↗
                              └──── END

``step_count`` vs ``max_steps`` is the in-graph budget, separate from
LangGraph's ``recursion_limit=5`` on ``invoke``. Crossing either budget is a
visible ``failed`` terminal — never a silent loop.

Field comments below are educational only. They are not Pydantic
``Field(description=...)``, so ``model_dump`` / JSON schema stay unchanged.
Field *order* is the original Slice 3 order on purpose (dump stability).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from schemas.gateway import ErrorType, GatewayResponse, ProviderEnum
from schemas.refined import RefinedPromptSchema


class OptimizerState(BaseModel):
    """One typed snapshot per graph run. Nodes return dicts of these fields.

    LangGraph merges each returned dict onto the previous snapshot using
    last-write-wins. Nodes must therefore *replace* accumulators with already
    summed values rather than emitting deltas they expect the graph to add.
    """

    # Untrusted user text. Execute wraps it in <untrusted_user_text>; never treat
    # it as a control-plane instruction (constitution §2.1 injection rule).
    raw_prompt: str
    # OUTPUT GATE product: JSON dump of `refined`. Execute reads this as the task.
    optimized_prompt: str | None = None
    # OUTPUT GATE product: schema-validated refine result. None → route to failed.
    refined: RefinedPromptSchema | None = None
    # Requested route (xai / google / fake). HTTP echo uses this, not the inner client.
    model_target: ProviderEnum
    # Requested model id (e.g. grok-4.3). Telemetry may still record model_id=fake.
    model_id: str
    # In-graph step budget. Nodes increment once per visit; edges compare to max_steps.
    step_count: int = 0
    # Ceiling for step_count (rule 20 / §2.4). Separate from invoke recursion_limit=5.
    max_steps: int = 5
    # Slice 4 HITL flag. Slice 3 carries it unused so the state shape is stable.
    confirmed: bool = False
    # Slice 4 confirm-path id. New prompts leave this None; confirm skips the graph.
    confirmation_id: str | None = None
    # Joins HTTP, llm_call logs, and Langfuse spans for this family request.
    correlation_id: str
    # One id for this invoke (§3.1). Distinct from correlation_id so a retried
    # HTTP request can be distinguished from a new graph run.
    graph_run_id: str
    # Set by execute (success) or failed node. None while still in flight.
    outcome: Literal["success", "failure", "skipped"] | None = None
    # Closed ErrorType enum — nodes must not invent free-typed strings.
    last_error_type: ErrorType | None = None
    # Terminal HTTP body built by execute_prompt (success) or failed_node.
    response: GatewayResponse | None = None
    # Run-level accumulators (KD-17). Nodes replace these with already-summed values
    # because the graph reducer is last-write-wins, not operator.add.
    token_in: int = 0
    token_out: int = 0
    latency_ms: int = 0
    estimated_cost_usd: float = 0.0
    # HTTP badge reads these sums. Per-call detail stays on llm_call log events.
    llm_calls: int = 0
    # Last provider finish_reason. HTTP exposes the last node, not a list.
    finish_reason: str | None = None
    # Last model text (execute success copies this onto GatewayResponse.text).
    last_text: str | None = None
    # Pinned execute prompt id. Slice 3 has no execute template; HTTP reports this
    # sentinel (KD-17). Refine uses prompt_refiner.v1 on the LLM *call*, not here.
    execute_prompt_version: str = "none"
    # Safe, non-PII reason for the UI. Never a raw prompt or completion.
    error_message: str | None = None
