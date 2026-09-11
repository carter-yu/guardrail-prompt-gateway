# ADR 0001: Dependency management and tooling

## Status
Accepted

## Context
Weekend 1–2 hour slices need a fast, reproducible Python environment. The constitution ([ground-rules.md](../ground-rules.md) §5) defaults LLM demos to Python + `uv` + `pytest` unless an ADR picks TypeScript.

## Decision
- Python **3.12**
- **`uv`** for deps and the virtualenv
- **`ruff`** for lint
- **`pytest`** for the offline suite
- **`structlog`** for structured logs
- Package layout: `src/guardrail_prompt_gateway` (hatchling)

Live LLM / Langfuse SDKs are **not** added in Phase 0. When a later phase calls a model, default provider is **xAI** (`XAI_API_KEY`, `https://api.x.ai/v1`) behind a Fake-LLM seam; record that in a new ADR.

## Consequences
Same weekend muscle memory as cec-vivisystem. Default `pytest` stays offline and secret-free.
