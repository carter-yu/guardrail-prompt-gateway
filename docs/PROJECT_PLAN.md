# Project Plan: Guardrail Prompt Gateway (`guardrail-prompt-gateway`)

**Repo Slug:** `guardrail-prompt-gateway`  
**Constitution:** `docs/ground-rules.md` (inherited from AI/LLM Learning & Demonstrate Ground Rules)  
**Engineering Language:** English only (code, comments, commits, tests, ADRs, logs)  
**User Interface Language:** Hong Kong Cantonese + English (never Simplified Chinese)  
**Host Target:** Local Mac Mini  

---

## 1. Executive Summary & Honest Demo Limits

### 1.1 Objective
Build a local, enterprise-grade LLM Gateway and Prompt Optimization service that:
1. Enables seamless routing between Google Gemini and xAI (Grok) using unified interfaces.
2. Optimizes rough user prompts into structured, high-context prompts via an explicit LangGraph pipeline.
3. Implements strict deterministic guardrails (input validation, tool allowlists, output schemas, HITL gates).
4. Employs comprehensive AIOps observability (per-call token/latency/cost telemetry and Langfuse tracing).

### 1.2 Honest Demo Limits (Rule 21)
- **Not a Production Cloud Gateway:** Hosted locally on a Mac Mini for local/family network use; no public multi-tenant auth or DDoS shield.
- **Flight Data Seam:** Initial flight tool connects to a sandboxed/mocked travel API adapter or rate-limited free API, not an enterprise GDS terminal (Amadeus/Sabre).
- **Evaluation Scope:** Model benchmarking uses local offline fixtures and synthetic golden sets; cost metrics are calculated via pinned static price tables (`eval/prices.yaml`), not live billing webhooks.

---

## 2. Target Architecture & Tech Stack

- **Runtime & Language:** Python 3.11+, managed via `uv`.
- **Frameworks:** LangChain / LangGraph, Pydantic v2 (schema validation).
- **Backend API:** FastAPI (async endpoints, dependency injection for fake/live models).
- **Frontend UI:** Lightweight Web UI (Streamlit or FastAPI + vanilla HTML/Tailwind) with bilingual HK Cantonese + English labels.
- **Observability:** Custom structured JSON logger (§3.1 telemetry) + Langfuse (optional tracer with no-op fallback).
- **Testing:** `pytest`, `pytest-mock` (100% offline default suite using Scripted/Fake LLMs).

---

## 3. Phased Implementation Roadmap (1–2 Hour Slices)

**ADR numbering erratum:** ADR 0001 is tooling (`docs/decisions/0001-dependency-and-tooling.md`). Slice 1 writes `docs/decisions/0002-multi-model-provider-abstraction.md` (do not create `0001-multi-model-…`). Slice 3 writes `docs/decisions/0003-langgraph-state-machine-topology.md` (not `0002-langgraph-…`). Do not overwrite ADR 0001. Locked test tables below are unchanged.

### Slice 0: Foundation, Scaffolding & Telemetry Spine (v0.1.0)
**Goal:** Establish repository structure, offline test harness, and deterministic telemetry logging schema.
- [x] Initialize repo structure according to §5 of ground rules.
- [x] Implement `src/lib/logger.py` supporting Section 3.1 telemetry fields (`provider`, `model_id`, `prompt_version`, `node`, `latency_ms`, `token_in`, `token_out`, `token_total`, `finish_reason`, `estimated_cost_usd`).
- [x] Implement price catalog `src/lib/prices.py` (`eval/prices.yaml`) for Gemini and xAI models.
- [x] Implement `FakeLLMClient` returning deterministic schema-valid responses without external API calls.
- [x] **Locked Test Table (Slice 0):**
  - `T0.1 (Happy)`: Logger emits valid JSON with all mandatory §3.1 fields on successful fake call.
  - `T0.2 (Failure)`: Logger records `finish_reason="error"` and retains latency/token metrics when call fails.
  - `T0.3 (Contract)`: Ensure cost calculation handles unknown models gracefully (`estimated_cost_usd=0.0`).
  - `T0.4 (Garbage)`: Logger survives malformed provider payloads without crashing.
- [x] Deliverable: Green offline `pytest`, `PROGRESS.md`, SemVer bump to `v0.1.0`.

---

### Slice 1: Model Gateway & Deterministic Router (v0.2.0)
**Goal:** Implement model-switching service between Gemini and xAI with strict input validation.
- [x] Define input/output schemas in `src/schemas/gateway.py` (`GatewayRequest`, `GatewayResponse`, `ProviderEnum`).
- [x] Implement `src/services/router.py`:
  - Enforce max prompt length (e.g., 2000 chars) and reject suspicious injection tokens.
  - Route execution to `ChatGoogleGenerativeAI` or `ChatXAI` based on request parameter.
  - Injectable provider factory (allows injecting `FakeLLM` during tests).
- [x] Write ADR `docs/decisions/0002-multi-model-provider-abstraction.md` (plan filename 0001 is tooling).
- [x] **Locked Test Table (Slice 1):**
  - `T1.1 (Happy)`: Routing to `google` or `xai` returns expected structured response schema.
  - `T1.2 (Gate)`: Input exceeding character ceiling is rejected with `outcome="skipped"`.
  - `T1.3 (Gate)`: PII detection regex blocks HKID / credit card patterns at boundary.
  - `T1.4 (Contract)`: Provider timeout triggers structured retry (max 2) and logs `outcome="failure"`.
- [x] Deliverable: Working offline router test suite, `PROGRESS.md`, SemVer bump to `v0.2.0`.

---

### Slice 2: Family Web Interface & Langfuse Integration (v0.3.0)
**Goal:** Deliver a runnable local web interface with bilingual UI and trace instrumentation.
- [x] Implement lightweight UI (FastAPI static templates or Streamlit):
  - Model Switcher: Gemini / xAI toggle.
  - Bilingual interface text (Cantonese + English):
    - Input: "輸入提示詞 (Enter Prompt)"
    - Model: "選擇模型 (Select Model)"
    - Submit: "送出 (Submit)"
    - Telemetry Badge: "耗時 (Latency) | 消耗 Token (Tokens) | 預估成本 (Cost)"
- [x] Integrate Langfuse wrapper in `src/lib/tracer.py`:
  - Must check `LANGFUSE_ENABLED=false` and run as a no-op when unset.
  - Redact user raw inputs exceeding 200 characters from span attributes.
- [x] **Locked Test Table (Slice 2):**
  - `T2.1 (Happy)`: Web API endpoint `/api/v1/generate` returns 200 with schema payload.
  - `T2.2 (Resilience)`: App starts and runs cleanly when Langfuse environment variables are missing.
  - `T2.3 (UI Contract)`: Ensure UI strings contain no Simplified Chinese glyphs.
- [x] Deliverable: Local demo runnable on Mac Mini (`uvicorn`), `PROGRESS.md`, SemVer bump to `v0.3.0`.

---

### Slice 3: Explicit LangGraph Prompt Optimization Engine (v0.4.0)
**Goal:** Implement a 2-node graph to refine, structure, and optimize raw prompts before execution.
- [ ] Define graph state in `src/graph/state.py` using typed `Pydantic` schema (`raw_prompt`, `optimized_prompt`, `model_target`, `step_count`, `confirmed`).
- [ ] Implement explicit LangGraph nodes in `src/graph/optimizer.py`:
  - Node 1: `refine_prompt` (Transforms rough family query into structured objective + constraints).
  - Node 2: `execute_prompt` (Dispatches optimized prompt to target LLM).
- [ ] Enforce deterministic guardrail: `recursion_limit=5`, no unbounded loops.
- [ ] Pinned prompt template: `prompts/prompt_refiner.v1.md`.
- [ ] Write ADR `docs/decisions/0002-langgraph-state-machine-topology.md`.
- [ ] **Locked Test Table (Slice 3):**
  - `T3.1 (Happy)`: Raw query "find me tickets to Osaka" expands into structured query with origin, destination, and dates.
  - `T3.2 (Guardrail)`: Graph terminates safely at `max_steps` without hanging.
  - `T3.3 (Contract)`: Node output strictly conforms to `RefinedPromptSchema`.
- [ ] Deliverable: Graph test suite green with Fake LLM, mermaid diagram in README, SemVer bump to `v0.4.0`.

---

### Slice 4: Flight Search Tool Gate & Human Confirmation (v0.5.0)
**Goal:** Integrate a grounded flight lookup tool with strict allowlist and HITL confirmation.
- [ ] Implement tool schema in `src/tools/flight_search.py` (`origin`, `destination`, `departure_date`).
- [ ] Implement Tool Gate:
  - Tool allowlist: only `flight_search` permitted on the execution node.
  - Mock API adapter returning deterministic flight fixtures for offline tests.
- [ ] Human Confirmation Gate (Rule 6):
  - Model proposes search parameters; user must confirm before tool execution.
  - Non-confirmed actions default to `dry_run=True`.
- [ ] **Locked Test Table (Slice 4):**
  - `T4.1 (Happy)`: Valid query triggers flight tool and parses returned pricing schema.
  - `T4.2 (Gate)`: Model attempting to call an unlisted tool is blocked by the tool allowlist.
  - `T4.3 (Refusal)`: Empty search result causes model to refuse politely without hallucinating flight numbers.
  - `T4.4 (HITL)`: Tool execution with `confirmed=False` performs dry-run only.
- [ ] Deliverable: Grounded tool pipeline, `PROGRESS.md`, SemVer bump to `v0.5.0`.

---

## 4. Grok Build Execution Protocol

When initiating a build session in Grok Build, strictly paste the following prompt:

```text
Build the next weekend slice of guardrail-prompt-gateway. Do not start from a blank scaffold once the repo exists.
Read docs/ground-rules.md (AI-LLM-LEARNING-GROUND-RULES) and PROJECT_PLAN.md as the constitution.

Heritage: cec-vivisystem + visa-games spine. This is an LLM learning/demo project, not a calendar swarm and not a kiosk.

Lock the test/eval table for THIS slice before coding. Default tests: Fake LLM, offline, no secrets.
LLM is a component, not source of truth. Guardrails in code (schema, tool allowlist, output validate).
LangGraph = explicit graph, no hidden supervisor blob.
Live calls: log section 3.1 (model, tokens, latency, cost estimate) + Langfuse optional, redacted; app runs with LANGFUSE_ENABLED=false.
Human confirm + dry-run for any side effect. English engineering. UI Cantonese+English. Never Simplified Chinese.
End with PROGRESS.md + SemVer bump. Time-box 1-2 hours. Leave a working demo.