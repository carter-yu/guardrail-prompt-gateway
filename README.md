# guardrail-prompt-gateway

A weekend learning demo: **deterministic prompt gates** (schema, allowlist, validators) around a pinned LLM.

This is **not** production prompt-injection defence, **not** a hosted API gateway, **not** a multi-agent platform, and **not** cec-vivisystem or visa-games. The LLM is a component, never source of truth.

Constitution: [docs/ground-rules.md](docs/ground-rules.md).

**Version:** 0.2.0 (Slice 1 router + input gate).

## Language
- Demo UI (later): Hong Kong Cantonese + English
- Code, docs, commits, ADRs: English only. Never Simplified Chinese.

## Current status
See [PROGRESS.md](PROGRESS.md). Slice 1: `complete_request` routes xAI/Gemini behind Fake LLM in tests; length/PII/injection gates skip; timeouts retry twice then fail. Live vendor SDKs are stubs. Not a public gateway. Injection denylist is a demo tripwire, not a jailbreak product.

## Quick start

```bash
uv sync
uv run pytest
uv run ruff check .
uv run python -c "from guardrail_prompt_gateway.hello import main; main()"
uv run python -c "from lib.llm import demo_fake_call; demo_fake_call()"
uv run python -c "from schemas.gateway import GatewayRequest, ProviderEnum; from services.router import complete_request; from lib.llm import FakeLLMClient, TelemetryLLMClient; r=complete_request(GatewayRequest(prompt='hello', provider=ProviderEnum.XAI), client=TelemetryLLMClient(FakeLLMClient())); print(r.outcome, r.provider, r.text)"
```

Copy `.env.example` to `.env` for later live slices. Default tests must stay green with no keys.

## Next
Slice 2 (v0.3.0): FastAPI bilingual UI + `/api/v1/generate` + Langfuse no-op. Locked tests T2.1–T2.3.
