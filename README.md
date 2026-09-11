# guardrail-prompt-gateway

A weekend learning demo: **deterministic prompt gates** (schema, allowlist, validators) around a pinned LLM.

This is **not** production prompt-injection defence, **not** a hosted API gateway, **not** a multi-agent platform, and **not** cec-vivisystem or visa-games. The LLM is a component, never source of truth.

Constitution: [docs/ground-rules.md](docs/ground-rules.md).

**Version:** 0.1.0 (Phase 0 — environment only).

## Language
- Demo UI (later): Hong Kong Cantonese + English
- Code, docs, commits, ADRs: English only. Never Simplified Chinese.

## Current status
See [PROGRESS.md](PROGRESS.md). Phase 0: `uv` + pytest + ruff + structlog + `hello`. No live LLM.

## Quick start

```bash
uv sync
uv run pytest
uv run ruff check .
uv run python -c "from guardrail_prompt_gateway.hello import main; main()"
```

Copy `.env.example` to `.env` for later live slices. Default tests must stay green with no keys.

## Next
Lock `phases/phase-1-*.md` (input gate + Fake LLM + output gate + telemetry) before coding.
