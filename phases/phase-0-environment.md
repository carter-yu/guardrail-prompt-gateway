# Phase 0 – Environment & Foundations

**Inherits (non-waivable for later phases)**  
[Ground rules](../docs/ground-rules.md) (AI/LLM learning constitution). Later phases may narrow **scope**; they may not waive tests, logging, eval gates, or code guardrails.

**Goal**  
Create a reproducible weekend environment so the next slice can be a real prompt-gateway contract (input gate → Fake LLM → output gate), not more scaffolding.

**Time box**  
1–2 hours.

**Version**  
`0.1.0`

## In Scope

- Repo layout from ground-rules §5
- Python 3.12 + `uv` + lock file
- `pytest` + `ruff` + `structlog`
- `hello` proof-of-life with structured log
- Constitution copied to `docs/ground-rules.md`
- Short philosophy + architecture stub + ADR 0001 (tooling)
- `.env.example` (no secrets)
- `PROGRESS.md` + SemVer `0.1.0`

## Out of Scope

Live LLM, LangGraph, RAG, Langfuse exporter, input/output gates, tool allowlist. Those wait for a locked Phase 1.

## Unit test plan (locked)

Offline. No network. No API keys.

| ID | Scenario | Expect |
|----|----------|--------|
| H1 | `setup_logging` | does not raise |
| H2 | `get_logger` | returns a usable logger; can emit `component` |
| H3 | `hello.main` | runs without error |

Non-tests: live xAI, Langfuse, gateway behaviour.

Minimum green bar: 3 tests + ruff.

## Acceptance Criteria

- [x] Structure, uv, pytest 3 tests, ruff, structlog
- [x] `hello` logs a structured line
- [x] Ground rules present; ADR 0001; PROGRESS; README honest limits
- [x] `.env.example` only placeholders
- [x] No live LLM in this slice
