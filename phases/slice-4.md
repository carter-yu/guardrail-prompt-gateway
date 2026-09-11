# Slice 4 – Flight search tool gate & HITL (v0.5.0)

**Status:** Not started

**Inherits** [ground-rules.md](../docs/ground-rules.md) · locked table in [PROJECT_PLAN.md](../docs/PROJECT_PLAN.md) §3 Slice 4 · [architecture.md](../docs/architecture.md) KD-15, KD-16, §4.9

**Do not implement until Slice 3 is green.**

## Goal

Allowlist `flight_search` on `execute_prompt` only. Mock fixtures, not GDS. Propose → confirm; `confirmed=false` is dry-run (no fixture read). Confirm POST skips the graph.

## Locked tests

Authoritative table: PROJECT_PLAN T4.1–T4.4.

| ID | Expect |
|----|--------|
| T4.1 | Confirm after propose → fixture quotes; one execute per `confirmation_id` |
| T4.2 | Unlisted `tool_calls` blocked |
| T4.3 | Empty search → refuse, no invented flight numbers |
| T4.4 | `confirmed=false` → `dry_run=true`, no quotes |

## Out of scope

Live travel API. `ALLOW_SIDE_EFFECTS` for real side effects. Calendar/Slack ports from cec-vivisystem.
