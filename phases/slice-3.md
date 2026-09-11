# Slice 3 – LangGraph prompt optimizer (v0.4.0)

**Status:** Not started

**Inherits** [ground-rules.md](../docs/ground-rules.md) · locked table in [PROJECT_PLAN.md](../docs/PROJECT_PLAN.md) §3 Slice 3 · [architecture.md](../docs/architecture.md) §4.8 · ADR **0003** `docs/decisions/0003-langgraph-state-machine-topology.md` (plan filename 0002 is superseded; see PROJECT_PLAN erratum)

**Do not implement until Slice 2 is green.**

## Goal

Explicit 2-node graph: `refine_prompt` → `execute_prompt`. `recursion_limit=5`. Pinned `prompts/prompt_refiner.v1.md`. Nodes call `complete_llm`, not `complete_request`.

## Locked tests

Authoritative table: PROJECT_PLAN T3.1–T3.3.

| ID | Expect |
|----|--------|
| T3.1 | “find me tickets to Osaka” → structured origin/destination/dates; HTTP counters = sum of two Fake calls |
| T3.2 | `max_steps=1` → `MAX_STEPS_EXCEEDED`, no hang |
| T3.3 | Refine output conforms to `RefinedPromptSchema` |

## Out of scope

Tools / HITL (Slice 4). Hidden supervisor / `create_agent`.
