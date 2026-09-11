# Slice 2 – Family web UI & Langfuse no-op (v0.3.0)

**Status:** Done

**Inherits** [ground-rules.md](../docs/ground-rules.md) · locked table in [PROJECT_PLAN.md](../docs/PROJECT_PLAN.md) §3 Slice 2 · [architecture.md](../docs/architecture.md) KD-6, KD-13, §4.6

**Do not implement until Slice 1 is green.** Lock nothing extra here — T2.1–T2.3 in the plan are the table.

## Goal

Local FastAPI + Jinja2 UI (HK Cantonese + English). `POST /api/v1/generate`. Langfuse no-op when `LANGFUSE_ENABLED=false`. Bind `127.0.0.1:8787`.

## Locked tests

Authoritative table: PROJECT_PLAN T2.1–T2.3.

| ID | Expect |
|----|--------|
| T2.1 | `/api/v1/generate` → 200 + `GatewayResponse` |
| T2.2 | App runs with Langfuse env missing / disabled |
| T2.3 | UI strings: no Simplified Chinese (catalog + `templates/`) |

## Out of scope

Streamlit. LangGraph. Flight tool. Binding `0.0.0.0` by default.
