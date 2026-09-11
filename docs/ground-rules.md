# Ground Rules — AI / LLM learning & demonstrate projects

**Status:** Binding template for future personal GitHub projects that learn and demonstrate LLM features (LangGraph, vector stores, RAGAS, DeepEval, Langfuse, and similar).
**Heritage:** Sibling of [cec-vivisystem](https://github.com/carter-yu/cec-vivisystem) and [visa-games](https://github.com/carter-yu/visa-games). This file **inherits their spine** and **adds deterministic guardrails + governance** that those two products did not need, because cec-vivisystem has **no LLM by default** and visa-games is a client kiosk, not a model pipeline.
**Language:** Engineering artifacts (this file, code, comments, commits, ADRs, eval reports) are **English only**. Any user-facing demo UI is **Hong Kong Cantonese + English**. Never Simplified Chinese.

**How to use with Grok Build**

1. Copy this whole file into the new repo as `docs/ground-rules.md` (keep a root copy if the first slice has no `docs/` yet).
2. New Grok Build chat: attach this file + one line: `Build the next weekend slice of <slug>. Do not start from a blank scaffold once the repo exists.`
3. A phase may **narrow scope**. It may **not** waive tests, logging, eval gates, or guardrails.

---

## Cantonese TL;DR

呢份係將來工餘 AI/LLM 小專案嘅憲法。繼承 cec-vivisystem / visa-games：週末 1–2 小時、有測試先寫碼、有 structured log、有 ADR、冇隱藏大腦。

加強：LLM **唔係** source of truth；工具要 allowlist；輸出要 schema；unit test 用 Fake LLM（默認 suite 唔打錢）；有 RAG 就要 golden set + RAGAS；有 LLM call 就要 log **邊個 model、token、latency**，再用 Langfuse（紅acted）；不可逆動作要 human confirmation。示範要寫明做唔到咩。

---

## 0. What was reviewed (and what was missing)

### [cec-vivisystem](https://github.com/carter-yu/cec-vivisystem) — keep

Binding `docs/ground-rules.md` (13 rules): weekend time-box, bottom-up, resilience, **mandatory unit tests**, **logging + retention**, human confirmation, calendar as SoT, **no hidden orchestrator**, language split, ADRs, `PROGRESS.md`, phase docs cannot waive tests/logs, secrets stay local.

Stronger satellite docs:

- `docs/unit-testing.md` — happy / failure / contract / garbage / boundary-log; offline; injectable clock `Asia/Hong_Kong`
- `docs/logging-and-retention.md` — `component`, `event`, `outcome`, `correlation_id`; classes A–G; never-log secrets
- `docs/resilience.md` — visible failures, no silent swallow, purge story
- `docs/architecture.md` — contracts at the seam (`parse → ParseResult`); LLM **not** a swarm component
- ADRs 0001–0003

**Does not transfer:** Google Calendar as SoT, Slack confirmation, “no LLM by default”. Those are product rules for that family swarm.

### [visa-games](https://github.com/carter-yu/visa-games) — keep

Same 13-rule spine, plus: **SemVer on every family-visible slice**, **honest capability limits** (a website cannot OS-lock macOS), PIN never logged, test **table locked before code** (P1–P9), session history capped.

**Does not transfer:** PIN kiosk, YouTube allow-list, pen-native UI, localStorage as settings SoT.

### Gaps for LLM demo projects (this file closes them)

Neither repo governs: model/prompt version pinning, tool allowlists, structured-output schemas, Fake-LLM unit tests vs paid eval jobs, RAG citation contracts, RAGAS/DeepEval gates, Langfuse redaction, token/latency budgets, or “the graph is not a hidden brain”.

---

## 1. Binding ground rules

These apply to **every phase and every component** unless an ADR changes them.

### Spine (from cec-vivisystem / visa-games)

1. **Time reality** — Development is 1–2 hour weekend (or weeknight) slices. Every change leaves the system in a working, demoable state.
2. **Bottom-up growth** — Add only the next small, proven capability. Do not design the full platform in advance. One graph node, one retriever, one eval metric — then stop.
3. **Resilience first** — Every component ships with tests, structured logs, and **visible** failure modes. No silent `except: pass`.
4. **Unit tests are mandatory** — No slice is done without a **locked test table** written **before** implementation. Minimum suite (cec standard):
   - Happy path
   - Failure / partial path
   - Contract / shape
   - Garbage input does not crash
   - Light boundary-log coverage
   Default suite is **offline**: no network, no live LLM, no live vector cloud, no real API keys. Clock is injectable; default TZ `Asia/Hong_Kong`.
5. **Logging, troubleshooting, retention** — Boundary logs on start/end: `timestamp`, `level`, `component`, `event`, `outcome` (`success|failure|partial|skipped`), `duration_ms` on completion, `error_type` / `error_message` on failure, `correlation_id` when a flow spans parts. **Every LLM call (live or fake) also logs §3.1 required telemetry** (model, tokens, latency). Every store has a **retention class and purge path**. Never log secrets, API keys, PIN, raw `.env`, full prompts with PII, or raw completions at INFO. See §3.
6. **Human confirmation for irreversible side effects** — Create / update / delete of real-world records (calendar, email send, payment, production deploy, deleting a vector index, posting to Slack) requires an explicit human confirm step. The LLM **proposes**; a guardian **accepts**. Demo tools that would be irreversible in production must be **dry-run by default**.
7. **Source of truth is not the model** — Grounded facts come from retrieval, fixtures, APIs, or the user. The LLM is a **component** that transforms under contracts. Never persist model prose as canonical data without a schema + validator.
8. **No hidden orchestrator** — LangGraph (or equivalent) is allowed **as an explicit graph**: named nodes, typed state, visible edges, documented reducers. Forbidden: a god-object “agent” that can call any tool, recurse forever, or hide control flow in a prompt. Intelligence emerges from contracts + guardrails, not from one supervisor blob. (Same Kelly rule as cec: *distributed control*.)
9. **Language** — Demo UI: Cantonese + English. Code, docs, commits, ADRs, eval reports: English only. Never Simplified Chinese in UI.
10. **Decision records** — Non-obvious choices (model, store, eval harness, graph shape) go in `docs/decisions/NNNN-title.md`.
11. **Progress visibility** — Every session ends with `PROGRESS.md` (what shipped, test/eval counts, version, leftover debt).
12. **Phase docs inherit standards** — A phase may narrow **scope**. It may not waive rules 4, 5, 6, 8, or §2 guardrails.
13. **Secrets stay local** — Keys for OpenAI/xAI/Google/Langfuse/Pinecone/etc. live in gitignored `.env`. Commit `.env.example` with empty placeholders only. Default tests must pass with no credentials. Never log secret values. Never embed keys in notebooks that get committed.
14. **Version every demoable slice** (from visa-games) — SemVer `MAJOR.MINOR.PATCH` in code + README/`PROGRESS.md`. PATCH = fix; MINOR = new capability; MAJOR = breaking contract or persist shape. Never ship a visible change without bumping.

### LLM-specific (new)

15. **Deterministic guardrails** — See §2. Input, tool, and output are gated **in code**, not by “please” in a prompt. Prompts are not a control plane.
16. **Pinned models and prompts** — Every LLM call records `provider`, `model_id`, `prompt_version` (hash or semver), `temperature`, `max_tokens`. Production/demo default for extraction, routing, and eval-under-test is **temperature 0** (or the provider’s deterministic setting). Prompt text lives in versioned files (`prompts/`), not scattered string literals.
17. **Fake LLM in the default suite** — Unit tests inject a fake/scripted model (recorded fixtures or a stub that returns schema-valid JSON). Live model calls are **opt-in** (`pytest -m live` / `eval` job) and never required for `pytest` / `npm test` to be green.
18. **Eval is a gate, not a blog post** — If the slice claims RAG, a **golden set** + **RAGAS** (or documented equivalent) must run on that set. If the slice claims an LLM judge or agent trajectory quality, **DeepEval** (or documented equivalent) on fixtures. Thresholds are numbers in code (`eval/thresholds.yaml`). A metric that is only printed in a notebook is not a gate.
19. **Observe every real LLM call** — Live calls emit the §3.1 fields **and** a **Langfuse** (or documented equivalent) span: same `correlation_id`, node, model, tokens, latency, tool name. Redact secrets and raw PII from traces. Local/dev must work **without** Langfuse (no-op exporter). Do not fail the demo because the dashboard is down. Fake-LLM unit tests still log `model_id=fake` + tokens=0 so the schema is exercised.
20. **Budgets** — Each live path declares `max_tokens`, `max_steps` (graph), `timeout_s`, and a **cost ceiling** for the golden eval job. Exceeding `max_steps` / timeout is a **visible failure**, not a silent retry storm. Retries are bounded (max 2) and idempotent.
21. **Honest demo limits** — README states what the project does **not** do (cec: no OS-lock analogue). Examples: “not production RAG”, “retriever is local chroma/FAISS, not a hosted cluster”, “judge is LLM-as-judge, not human labels”. Never present a stub as a live vendor.

---

## 2. Deterministic Guardrails (binding)

Guardrails are **code**. A prompt saying “do not call delete” is not a guardrail.

### 2.1 Input gate

- Schema-validate user/API input before it reaches the graph (`pydantic` / Zod / equivalent).
- Max input length; reject or truncate with `outcome=skipped` and a log.
- PII: do not send raw identifiers (HKID, full address, passwords) to a third-party model. Redact or hash at the boundary.
- Injection: treat retrieved docs and user text as **untrusted data**, never as executable instructions. System prompt + developer messages are the only control channel.

### 2.2 Tool gate

- **Allowlist** of tools per node. A node that “can use any tool” is a hidden orchestrator — forbidden.
- Each tool: JSON schema, timeout, idempotency key where it has side effects.
- Side-effecting tools default to **dry-run** unless `ALLOW_SIDE_EFFECTS=true` **and** a human confirmation id is present (rule 6).
- No shell tool, no unrestricted HTTP, no “run this Python” in learning demos unless the whole point of the slice is a **sandboxed** interpreter — and then it still has an allowlist.

### 2.3 Output gate

- Structured outputs for anything downstream consumes: JSON schema validate **before** persistence or tool fire.
- On validation failure: retry **once** with the validator error (bounded), then fail visible (`outcome=failure`, no partial write).
- RAG answers **must** attach citation ids from retrieved chunks. If retrieval is empty: **refuse** with a fixed message, do not hallucinate. That refuse path is a unit test.

### 2.4 Graph gate (LangGraph)

- State is a typed reducer, not a bag of strings.
- Every edge is explicit. Cycles must have a step counter → `max_steps`.
- Checkpoints: optional; if used, they are retention class C (purge).
- “Supervisor” nodes may **route** among a **fixed** child list. They may not invent tools or spawn unbounded sub-agents.

### 2.5 Retrieval gate (vector DB / RAG)

- Embedding model id is pinned and recorded next to the index version.
- Index rebuild is a documented command; never implicit on every request.
- Query path logs `top_k`, scores, chunk ids (not full raw docs at INFO).
- Golden questions live in `eval/golden/*.json`. Changing the index without re-running RAGAS is unfinished work.

---

## 3. Logging, traces, retention

Minimum **flow** fields (cec + visa):

`timestamp`, `level`, `component`, `event`, `outcome`, `duration_ms` (completion), `error_type` (failure), `correlation_id` (cross-node).

### 3.1 LLM call telemetry (binding)

One structured event per **model invocation** (chat, embed, judge, rerank). Fake LLM uses the same schema with `model_id=fake`.

**Required (every call)**

| Field | Meaning |
| --- | --- |
| `provider` | `xai` / `openai` / `google` / `anthropic` / `local` / `fake` |
| `model_id` | Exact id sent to the API, e.g. `grok-4`, `gpt-4.1-mini`. Not a nickname. |
| `prompt_version` | Semver or content hash of the prompt file |
| `node` | LangGraph node (or `embed` / `judge`) |
| `latency_ms` | Wall time of this call (TTFB to complete). Also copy to `duration_ms`. |
| `token_in` | Prompt / input tokens (provider usage) |
| `token_out` | Completion tokens (0 for embeddings) |
| `token_total` | `token_in + token_out` (+ cache write if the provider splits it) |
| `finish_reason` | Provider value: `stop` / `length` / `tool_calls` / `content_filter` / `error` |
| `stream` | `true` if streamed |
| `retry_count` | 0 on first attempt |

**Required when the provider returns them**

| Field | Meaning |
| --- | --- |
| `provider_request_id` | Vendor request id (debug billing / support) |
| `token_cached` | Cached prompt tokens (if billed separately) |
| `ttft_ms` | Time to first token when streaming |
| `estimated_cost_usd` | tokens times a pinned price table (`eval/prices.yaml` or `src/lib/prices.py`), rounded to 6 decimals. Log `price_table_version`. Never log the payment account. |

**Required on the graph / RAG path (when that slice exists)**

| Field | Meaning |
| --- | --- |
| `graph_run_id` | One id for the whole graph invocation (= `correlation_id` if they coincide) |
| `step` | Node index / `max_steps` |
| `tool` / `tool_call_id` | Allowlisted tool name; id of the call |
| `validation_outcome` | `pass` / `retry` / `fail` for output schema |
| `embed_model_id` | Embedding model (may differ from chat) |
| `index_version` | Vector index build id |
| `top_k` | Retrieval k |
| `chunk_ids` | Retrieved ids only, not raw text at INFO |

**Nice to have (DEBUG or Langfuse span attributes, not INFO)**

- `temperature`, `max_tokens`, `top_p`
- `tool_schema_version`
- `safety_flag` (boolean / category from the provider — **not** the blocked text)
- Truncated preview of user input / output, **max 200 chars**, PII already redacted
- `prompt_hash` if you do not want `prompt_version` to be a filename

**Roll up (end of graph / request, class B audit)**

- `token_in_sum`, `token_out_sum`, `latency_ms_sum`, `llm_calls`, `estimated_cost_usd_sum`
- `outcome` of the whole flow

Eval jobs log the same fields per call plus `eval_run_id`, `golden_id`, metric scores (class H).

### 3.2 Never log

- API keys, `.env`, Langfuse secrets, OAuth tokens
- Full system / developer prompt bodies at INFO (hash + version only)
- Full user documents, retrieved chunk **text**, or raw completions that may contain PII
- HKID, passwords, PIN, emails, child names as raw strings
- Card numbers / payment account ids
- Tool arguments that contain secrets (redact; log tool **name** only at INFO)

DEBUG truncated previews are optional and still redacted.

### 3.3 Retention

| Class | What | Retention |
| --- | --- | --- |
| A | Application logs (includes per-call telemetry) | 14 days (or session for a local demo) |
| B | Audit (tool side effects, human confirm, **per-request token/cost roll-up**) | 90 days; cap size |
| C | Operational (graph checkpoints, in-flight jobs) | Until terminal + 7 days; max 30 days |
| D | Dead letters | 30 days |
| E | Health | 14 days detail; last status overwrite |
| F | User content the operator meant to keep | Until explicit delete |
| H | Eval artifacts (RAGAS/DeepEval reports, traces export) | 90 days; golden **fixtures** are git (not purged) |
| T | Langfuse traces | Follow Langfuse project retention; still redact; no secrets |

No store without a purge story (a script is enough before automation).

Langfuse is **observability**, not source of truth. The app must run if Langfuse is unset (`LANGFUSE_ENABLED=false`). Langfuse spans reuse §3.1 field names so logs and traces can be joined on `correlation_id`.

### 3.4 Tests for telemetry

Unit tests (Fake LLM) must assert the required fields exist on a successful call and on a failed call (`finish_reason=error`, `token_*` present even if 0). Garbage provider payloads must not crash the logger.

---

## 4. Testing vs evaluation

Two different gates. Both can be “green”; they are not interchangeable.

| Gate | When | Network | LLM | Pass criterion |
| --- | --- | --- | --- | --- |
| **Unit** | Every slice | No | Fake / fixtures | Locked table; pytest/vitest offline |
| **Contract** | Every public function | No | Fake | Schema / typed state |
| **Eval (RAGAS)** | Slice that claims RAG | Optional isolated | Live **or** recorded | Thresholds in `eval/thresholds.yaml` |
| **Eval (DeepEval)** | Slice that claims judge/agent quality | Optional | Live **or** recorded | Same |
| **Live smoke** | Opt-in | Yes | Yes | Manual / `pytest -m live`; never default CI |

Eval jobs must be **reproducible**: pinned model, pinned prompt hash, pinned golden set commit, recorded `run_id`. A one-off notebook screenshot is not an eval.

Minimum eval table (lock **before** coding a RAG/agent slice):

| ID | Case | Expect |
| --- | --- | --- |
| E1 | Golden question with supporting chunk in index | answer cites that chunk; RAGAS faithfulness ≥ threshold |
| E2 | Golden question with **empty** retrieval | refuse; no fabricated citation |
| E3 | Contradictory / garbage question | no crash; `outcome=skipped` or refuse |
| E4 | Tool allowlist: model asks a forbidden tool | tool gate denies; graph does not execute it |
| E5 | `max_steps` exceeded | visible failure, no infinite loop |

---

## 5. Suggested repo shape (new LLM demo)

Do not copy cec calendar/Slack code or visa-games kiosk code. Copy **this constitution**.
Repo layout (indent = files, not a fenced block):

    README.md                 # honest limit + how to run tests/eval
    PROGRESS.md
    docs/ground-rules.md      # this file
    docs/philosophy.md        # short; Kelly + “LLM is a component”
    docs/architecture.md      # graph, stores, seams
    docs/decisions/           # ADRs
    prompts/<name>.vN.md      # pinned prompts
    src/                      # graph, tools, retriever, validators
    eval/golden/              # fixtures
    eval/thresholds.yaml
    tests/                    # offline unit + fakes
    .env.example

Python default (cec-like): `uv`, `pytest`. TypeScript default (visa-like): `vitest`. Pick one per repo; do not mix without an ADR.

Auth and hosted DB stay **off** unless the slice’s whole point is that vendor (then `.env` + fakes still required).

---

## 6. Feature-specific standards (use when the slice claims that feature)

### LangGraph

- One typed `State` + named nodes. README contains a mermaid of the graph.
- `max_steps`, timeout, and a terminal `Failed` node.
- Unit-test the **reducers and routing** with a fake model: given state X, next node is Y.

### Vector database

- Local-first for learning (Chroma / FAISS / sqlite-vec). Hosted Pinecone/etc. is opt-in + ADR.
- Index version + embedding model id in metadata.
- Delete/rebuild command documented; retention class F for corpora you meant to keep, class C for caches.

### RAGAS

- Golden set ≥ 5 questions before claiming RAG.
- Report: faithfulness, answer relevancy, context precision (or current RAGAS equivalents). Thresholds committed.
- Empty-retrieval case is mandatory (E2).

### DeepEval

- Assertions in code (`assert_test` / equivalent), not screenshots.
- LLM-as-judge is **eval-only**, never the unit-test default.
- Judge model id pinned; cost under the eval budget.

### Langfuse

- Wrap live LLM + tool spans.
- Map `correlation_id` → Langfuse `trace_id` / `session_id`.
- Redact env keys, emails, names if the demo is public.
- `.env.example`: `LANGFUSE_PUBLIC_KEY=`, `LANGFUSE_SECRET_KEY=`, `LANGFUSE_HOST=`, `LANGFUSE_ENABLED=false`.

---

## 7. Grok Build kickoff block (paste above this file)
Paste the following 13 lines as the Grok Build prompt (no nested fence in this constitution):

    Build the next weekend slice of <PROJECT_SLUG>. Do not start from a blank scaffold once the repo exists.
    Read docs/ground-rules.md (AI-LLM-LEARNING-GROUND-RULES) as the constitution.

    Heritage: cec-vivisystem + visa-games spine. This is an LLM learning/demo project, not a calendar swarm and not a kiosk.

    Lock the test/eval table for THIS slice before coding. Default tests: Fake LLM, offline, no secrets.
    LLM is a component, not source of truth. Guardrails in code (schema, tool allowlist, output validate).
    LangGraph = explicit graph, no hidden supervisor blob.
    If this slice claims RAG: golden set + RAGAS thresholds. If it claims a judge: DeepEval.
    Live calls: log section 3.1 (model, tokens, latency, cost estimate) + Langfuse optional, redacted; app runs with LANGFUSE_ENABLED=false.
    Human confirm + dry-run for any side effect. English engineering. UI Cantonese+English. Never Simplified Chinese.
    End with PROGRESS.md + SemVer bump. Time-box 1-2 hours. Leave a working demo.

---

## 8. Definition of done (every slice)

- [ ] Test/eval table locked in the phase doc **before** code
- [ ] Offline unit suite green (happy, failure, contract, garbage, log boundary)
- [ ] Guardrails: input schema, tool allowlist, output schema (as applicable) have failing tests that prove they block
- [ ] Structured logs at the new boundary; `correlation_id` if the flow spans nodes
- [ ] LLM telemetry §3.1 required fields on Fake-LLM success **and** failure (model, tokens, `latency_ms`)
- [ ] Retention/purge named for any new store
- [ ] No secrets in git, logs, or fixtures
- [ ] If RAG/agent claimed: eval job + thresholds; E1–E5 as applicable
- [ ] Langfuse no-op path works
- [ ] Honest limit line in README
- [ ] SemVer bumped; `PROGRESS.md` updated
- [ ] ADR if a vendor/model/store was chosen

---

## 9. What this file is not

- Not a licence to paste LangChain mega-templates.
- Not a production MLOps platform.
- Not a replacement for cec-vivisystem or visa-games constitutions **inside those repos**.
- Not permission to turn every weekend into “add an agent”. Most slices should stay **one node, one contract, one eval**.

*Adopted from cec-vivisystem (Kevin Kelly vivisystem spine) and visa-games (honest limits + SemVer) on 2026-09-10. For LLM learning/demonstrate projects only.*