# ADR 0002: Multi-model provider abstraction

## Status
Accepted

## Context
Slice 1 needs Gemini and xAI behind one seam. PROJECT_PLAN named this file `0001-multi-model-provider-abstraction.md`; ADR 0001 is already tooling, so this is **0002**. See `docs/architecture.md` KD-5.

## Decision
- Core code depends on `lib.llm.LLMClient`. Tests inject `FakeLLMClient`.
- `get_client` always returns `TelemetryLLMClient(inner)`.
- Split router: `complete_llm` (timeout, max 2 retries, no input gate) vs `complete_request` (input gate then `complete_llm`).
- Live adapters are **stubs** in Slice 1 (`MISSING_CREDENTIALS` / `NOT_IMPLEMENTED`). Vendor SDKs are not default pytest deps.
- Later live path: try `langchain_xai.ChatXAI` first; fallback `ChatOpenAI(base_url=https://api.x.ai/v1)`. Lazy-import inside `get_client` / `_live_or_stub` only.
- Default live provider xAI (`grok-4.3`). Gemini route `gemini-2.5-flash`.
- HTTP/library `GatewayResponse.provider` is the **requested** enum; telemetry records the actual inner client (`fake` in pytest).

## Consequences
Default `uv run pytest` stays offline. Graph nodes (Slice 3) call `complete_llm`, never `complete_request`.
