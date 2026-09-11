# ADR 0003: LangGraph state-machine topology

## Status
Accepted

## Context
Slice 3 needs an explicit prompt optimizer. PROJECT_PLAN named this file `0002-langgraph-state-machine-topology.md`; ADR 0002 is already the multi-model provider abstraction, so this is **0003**. See `docs/architecture.md` KD-5.

Constitution rule 8 forbids a hidden supervisor / `create_agent` blob.

## Decision
- Pin **`langgraph` 1.2.x** (lockfile: 1.2.11). Import `StateGraph`, `START`, `END` only. Do not import `langgraph.prebuilt` / `create_agent`.
- Typed Pydantic `OptimizerState`. Named nodes: `refine_prompt` → `execute_prompt`, plus terminal `failed`.
- Nodes call `complete_llm`, never `complete_request` (input gate is not re-run on the optimized prompt).
- Two loop budgets: `recursion_limit=5` on **`invoke`** (LangGraph 1.2 `compile()` does not take this kwarg) and in-graph `step_count >= max_steps` (default 5). After incrementing, a node sets `last_error_type=max_steps_exceeded` even if schema passed.
- Pinned refine template: `prompts/prompt_refiner.v1.md` (`prompt_version=prompt_refiner.v1` on that call). Execute has no pinned file; HTTP `prompt_version` is the execute sentinel `none` (KD-17).
- `build_graph(get_client_fn=..., complete_llm_fn=...)` so pytest injects Fake. Default pytest does not construct live stubs.

## Consequences
`POST /api/v1/generate` runs the input gate then `graph.invoke`. T3.1–T3.3 stay Fake and offline. Slice 4 may add `flight_search` on `execute_prompt` only.
