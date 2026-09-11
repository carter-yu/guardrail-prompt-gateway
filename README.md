# guardrail-prompt-gateway

A weekend learning demo: **deterministic prompt gates** (schema, allowlist, validators) around a pinned LLM.

This is **not** production prompt-injection defence, **not** a hosted API gateway, **not** a multi-agent platform, and **not** cec-vivisystem or visa-games. The LLM is a component, never source of truth.

Constitution: [docs/ground-rules.md](docs/ground-rules.md).

**Version:** 0.1.0 (Slice 0 telemetry complete).

## Language
- Demo UI (later): Hong Kong Cantonese + English
- Code, docs, commits, ADRs: English only. Never Simplified Chinese.

## Current status
See [PROGRESS.md](PROGRESS.md). Slice 0: Fake LLM + JSON `llm_call` telemetry + pinned `eval/prices.yaml`. No live LLM. Not a public gateway.

## Quick start

```bash
uv sync
uv run pytest
uv run ruff check .
uv run python -c "from guardrail_prompt_gateway.hello import main; main()"
uv run python -c "from lib.llm import demo_fake_call; demo_fake_call()"
```

Copy `.env.example` to `.env` for later live slices. Default tests must stay green with no keys.

## Next
Slice 1 (v0.2.0): gateway schemas, input gate, `complete_llm` / `complete_request`. Locked tests T1.1–T1.4 in [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md).
