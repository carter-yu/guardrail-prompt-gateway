# Progress Log – guardrail-prompt-gateway

## How to use
Add a new entry at the top after every session.

---

## 2026-09-12 (Educational AI comments)

- **Phase**: Comment-only — LangGraph / routing / gates / telemetry textbook comments
- **Version**: 0.4.0 (no bump; no runtime or HTTP change)
- **Completed**:
  - English architectural comments on `src/graph/`, `src/services/`, `src/lib/`, `src/schemas/`, `src/app/main.py`
  - Grep markers: `INPUT GATE`, `TOOL GATE`, `OUTPUT GATE`, `OBSERVABILITY HOOK`
  - Ground rules: new rule 22 + §10 in `docs/ground-rules.md` and `/Users/yucarter/my-ai-projects/-ai-projects-ground-rules.md`
  - Did **not** edit `prompts/prompt_refiner.v1.md` (loaded as system message)
- **Tests**: 27 passed; ruff clean
- **Next session plan**: Slice 4 flight tool + HITL T4.1–T4.4 (comments on new tool files per §10)
- **Session status**: comment-only; offline suite still green

---

## 2026-09-11 (Slice 3 LangGraph)

- **Phase**: Slice 3 – explicit 2-node LangGraph (`refine_prompt` → `execute_prompt`)
- **Version**: 0.4.0
- **Completed**:
  - `OptimizerState` + `RefinedPromptSchema`; pinned `prompts/prompt_refiner.v1.md`
  - `build_graph` with `recursion_limit=5` on invoke and in-graph `max_steps`
  - HTTP `POST /api/v1/generate` = input gate then `graph.invoke`; counters are sums
  - ADR [0003](docs/decisions/0003-langgraph-state-machine-topology.md) (plan filename 0002 is superseded)
- **Tests**: 27 passed (H1–H3, T0–T3); ruff clean
- **Next session plan**: Slice 4 flight tool + HITL T4.1–T4.4
- **Session status**: Slice 3 offline acceptance met

---

## 2026-09-11 (Slice 2 UI)

- **Phase**: Slice 2 – FastAPI bilingual UI + Langfuse no-op
- **Version**: 0.3.0
- **Completed**:
  - `GET /`, `GET /health`, `POST /api/v1/generate`
  - Jinja2 UI (yue-HK + English); JSON `fetch` (not form-urlencoded)
  - `get_tracer()` no-op when `LANGFUSE_ENABLED` is unset/false
  - `GATEWAY_USE_FAKE=true` for key-free demo
- **Tests**: 24 passed (H1–H3, T0–T2); ruff clean
- **Next session plan**: Slice 3 LangGraph T3.1–T3.3
- **Session status**: Slice 2 offline acceptance met

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
