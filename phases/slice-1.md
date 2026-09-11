# Slice 1 – Model gateway & input gate (v0.2.0)

**Status:** Done (`71b42c2`)

**Inherits** [ground-rules.md](../docs/ground-rules.md) · locked table in [PROJECT_PLAN.md](../docs/PROJECT_PLAN.md) §3 Slice 1 · [architecture.md](../docs/architecture.md) KD-10, §4.3–4.5 · ADR [0002](../docs/decisions/0002-multi-model-provider-abstraction.md)

## Goal

Route xAI / Gemini behind `LLMClient`. Gate length, HKID/PAN, injection tokens **in code**. Fake LLM in pytest. Live adapters are stubs.

## Locked tests

Authoritative table: PROJECT_PLAN T1.1–T1.4.

| ID | Expect |
|----|--------|
| T1.1 | `google` / `xai` → `GatewayResponse`; `provider` is the requested enum |
| T1.2 | Prompt > 2000 chars → `outcome=skipped` |
| T1.3 | HKID / Luhn PAN → `pii_blocked` |
| T1.4 | `TimeoutError` retried twice (3 `llm_call`s) then `outcome=failure` |

## Shipped

- `src/schemas/gateway.py`
- `src/services/input_gate.py`, `router.py` (`complete_llm` / `complete_request`), `providers.py` (stubs)
- `tests/test_input_gate.py`, `tests/test_router.py`

## Out of scope

HTTP `/api/v1/generate` (Slice 2). Real `ChatXAI` / `ChatGoogleGenerativeAI` bodies (later live-smoke).
