# Architecture – guardrail-prompt-gateway

## 1. Intent

A **prompt gateway**: user text hits deterministic gates **before** and **after** a pinned LLM call. The graph (when it exists) is explicit. No hidden supervisor.

```
                    ┌─────────────────────────────┐
                    │     External environment     │
                    │  (optional live LLM / traces)│
                    └──────────────┬──────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           ▼                       ▼                       ▼
    ┌─────────────┐       ┌──────────────┐       ┌─────────────────┐
    │ Input gate  │──────▶│  LLM node    │──────▶│ Output gate     │
    │ (schema)    │       │ (fake|live)  │       │ (schema)        │
    └─────────────┘       └──────────────┘       └─────────────────┘
```

Phase 0 is environment only. Gates and the LLM node are **not started**.

## 2. Current state (Phase 0)

- Python 3.12, `uv`, `pytest`, `ruff`, `structlog`
- `hello` proof-of-life
- Constitution: [ground-rules.md](ground-rules.md)
- No graph, no tools, no retrieval, no live model

## 3. Source of truth

Not the model. Grounded facts come from fixtures, user input (schema-validated), and later retrieval. Validated structured output is the only persistable model product.

## 4. Next slice (not this phase)

Lock `phases/phase-1-*.md` first: input schema + Fake LLM + output schema + §3.1 telemetry on fake success and failure.

## 5. Honest limits

This is a weekend learning demo, not production prompt security, not a hosted gateway, not a multi-agent platform.
