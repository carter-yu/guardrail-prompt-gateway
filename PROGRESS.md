# Progress Log – guardrail-prompt-gateway

## How to use
Add a new entry at the top after every session.

---

## 2026-09-11 (Slice 1 router)

- **Phase**: Slice 1 – model gateway + input gate
- **Version**: 0.2.0
- **Completed**:
  - `GatewayRequest` / `GatewayResponse` / `ErrorType`
  - Input gate: 2000 chars, HKID, Luhn PAN, injection denylist
  - `complete_llm` (timeout retries 0..2) + `complete_request` (gate then llm)
  - `get_client` wraps Fake or live stub; ADR [0002](docs/decisions/0002-multi-model-provider-abstraction.md)
- **Tests**: 19 passed (H1–H3, T0.1–T0.4, T1.1–T1.4); ruff clean
- **Issues / Friction**: live ChatXAI/Gemini bodies still stubs
- **Resilience notes**: PII blocked not forwarded; Fake in pytest; no FastAPI yet
- **Next session plan**: Slice 2 uvicorn UI T2.1–T2.3
- **Session status**: Slice 1 offline acceptance met

---

## 2026-09-11 (Slice 0 telemetry)

- **Phase**: Slice 0 – telemetry spine, prices, Fake LLM
- **Version**: 0.1.0 (complete when T0.1–T0.4 green)
- **Completed**:
  - Design in [docs/architecture.md](docs/architecture.md) (review consensus)
  - `src/lib/logger.py` `telemetry_from_provider` + `emit_llm_call`
  - `eval/prices.yaml` + `PriceTable` (unknown model → $0.0)
  - `FakeLLMClient` + `TelemetryLLMClient` (sole `llm_call` emitter); `NoOpTracer`
  - Tests T0.1–T0.4; H1–H3 kept
- **Tests**: 7 passed (H1–H3 + T0.1–T0.4); ruff clean
- **Issues / Friction**: none
- **Resilience notes**: Fake only; no network; class A stdout JSON; no store
- **Next session plan**: Slice 1 router + input gate (T1.1–T1.4). ADR 0002 multi-model. Live adapters stay stubs
- **Session status**: Slice 0 offline acceptance met

---

## 2026-09-11 (Phase 0 environment)

- **Phase**: 0 – Environment & foundations
- **Version**: 0.1.0
- **Completed**:
  - Copied AI/LLM constitution to [docs/ground-rules.md](docs/ground-rules.md)
  - Python 3.12, `uv`, hatchling package `src/guardrail_prompt_gateway`
  - `pytest` + `ruff` + `structlog`; `hello` proof-of-life
  - ADR 0001 (tooling); philosophy + architecture stub; `.env.example`
- **Tests**: 3 passed (H1–H3); ruff clean
- **Issues / Friction**: none
- **Resilience notes**: stdout logs only; no store; no live LLM; Fake-LLM telemetry waits for Phase 1
- **Next session plan**: Lock Phase 1 — input schema + Fake LLM + output schema + §3.1 fake telemetry. Do not add LangGraph/RAG yet
- **Session status**: Phase 0 offline acceptance met

---

## Template
### YYYY-MM-DD
- **Phase**:
- **Version**:
- **Completed**:
- **Tests**:
- **Issues / Friction**:
- **Resilience notes**:
- **Next session plan**:
