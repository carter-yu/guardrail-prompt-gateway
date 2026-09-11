# Slice 0 – Telemetry spine, prices, Fake LLM (v0.1.0)

**Status:** Done (`2a97e85`)

**Inherits** [ground-rules.md](../docs/ground-rules.md) · locked table in [PROJECT_PLAN.md](../docs/PROJECT_PLAN.md) §3 Slice 0 · seams in [architecture.md](../docs/architecture.md)

Hello/uv/pytest (H1–H3) is [phase-0-environment.md](phase-0-environment.md). This slice **completes v0.1.0** with §3.1 `llm_call` telemetry.

## Goal

JSON telemetry on Fake LLM success **and** failure; pinned `eval/prices.yaml`; unknown model → `$0.0`.

## Locked tests

Do not fork. Authoritative table: PROJECT_PLAN T0.1–T0.4.

| ID | Expect |
|----|--------|
| T0.1 | Success fake call emits all §3.1 fields |
| T0.2 | Failure: `finish_reason=error`, tokens/latency present |
| T0.3 | Unknown `model_id` → `estimated_cost_usd=0.0` |
| T0.4 | `telemetry_from_provider` never raises on garbage |

## Shipped

- `src/lib/logger.py`, `prices.py`, `llm.py` (`FakeLLMClient`, `TelemetryLLMClient`), `tracer.py` (`NoOpTracer`)
- `eval/prices.yaml`
- `tests/test_telemetry.py`

## Out of scope

FastAPI, live SDKs, LangGraph, Langfuse exporter.
