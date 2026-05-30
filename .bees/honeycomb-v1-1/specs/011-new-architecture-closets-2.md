---
type: scribe-only
output-files:
  - wing_repo_bees/architecture/honeycomb-access/closet.md
  - wing_repo_bees/architecture/honeycomb-access/index.md
  - wing_repo_bees/architecture/honeycomb-access/api-surface.md
  - wing_repo_bees/architecture/honeycomb-access/env-contract.md
  - wing_repo_bees/architecture/palace-recall/closet.md
  - wing_repo_bees/architecture/palace-recall/index.md
  - wing_repo_bees/architecture/palace-recall/overlay-semantics.md
  - wing_repo_bees/architecture/palace-recall/log-side-effect.md
---

# Spec 011 — New architecture closets (2)

## Builder model

claude-sonnet-4-6

## Goal

Create two new `wing_repo_bees/architecture/` closets: `honeycomb-access` (single API surface, env contract, observability log shape) and `palace-recall` (include_pending/overlay semantics, scope-aware behaviour, log-record side-effect).

## Scope

**New files:**

- `wing_repo_bees/architecture/honeycomb-access/closet.md` — ≤500 char summary of the single MCP API surface
- `wing_repo_bees/architecture/honeycomb-access/index.md` — TOC
- `wing_repo_bees/architecture/honeycomb-access/api-surface.md` — single-API rule, what is allowed vs forbidden, `palace_recall` as the only entry point
- `wing_repo_bees/architecture/honeycomb-access/env-contract.md` — `BEES_ACTOR`/`BEES_STAGE`/`BEES_MODEL` env vars, defaults, and observability log destination

- `wing_repo_bees/architecture/palace-recall/closet.md` — ≤500 char summary of `palace_recall` semantics
- `wing_repo_bees/architecture/palace-recall/index.md` — TOC
- `wing_repo_bees/architecture/palace-recall/overlay-semantics.md` — `include_pending`, consumer overlay precedence, scope-aware recall behaviour
- `wing_repo_bees/architecture/palace-recall/log-side-effect.md` — JSONL record schema (schema_version v1), log destination derivation, write semantics

**Non-goals:**

- No changes to `lib/`, `bin/`, `tools/`, or `tests/` (code work is in other specs)
- No changes outside `wing_repo_bees/architecture/` and the spec file itself
- No changes to `wing_repo_bees/actor/` (covered by spec 012)
- No changes to `wing_bees/plan/` (covered by spec 010)

## Failing test

```
# Before this unit runs, these paths are absent:
test -f wing_repo_bees/architecture/honeycomb-access/closet.md && echo FAIL || echo PASS  # → PASS (absent)
test -f wing_repo_bees/architecture/palace-recall/closet.md && echo FAIL || echo PASS      # → PASS (absent)

# After this unit runs, these must exist:
test -f wing_repo_bees/architecture/honeycomb-access/closet.md
test -f wing_repo_bees/architecture/honeycomb-access/index.md
test -f wing_repo_bees/architecture/honeycomb-access/api-surface.md
test -f wing_repo_bees/architecture/honeycomb-access/env-contract.md
test -f wing_repo_bees/architecture/palace-recall/closet.md
test -f wing_repo_bees/architecture/palace-recall/index.md
test -f wing_repo_bees/architecture/palace-recall/overlay-semantics.md
test -f wing_repo_bees/architecture/palace-recall/log-side-effect.md

# closet.md files must be ≤500 chars:
wc -c < wing_repo_bees/architecture/honeycomb-access/closet.md  # → ≤500
wc -c < wing_repo_bees/architecture/palace-recall/closet.md     # → ≤500

# Content smoke-checks:
grep -q "BEES_ACTOR" wing_repo_bees/architecture/honeycomb-access/env-contract.md
grep -q "schema_version" wing_repo_bees/architecture/palace-recall/log-side-effect.md
grep -q "overlay" wing_repo_bees/architecture/palace-recall/overlay-semantics.md
```

## Builder prompt

This is a scribe-only unit; the scribe acts as builder.

Create the following closets under `wing_repo_bees/architecture/`. Each closet follows the established pattern: an HTML-comment header in `closet.md` (Hall tag), an `index.md` TOC, and 2 drawer `.md` files with verbatim canonical content. All content is derived from ADR-0001, ADR-0002, and ADR-0004.

### wing_repo_bees/architecture/honeycomb-access/ (NEW)

`closet.md` (≤500 chars): HTML-comment header with `Hall: hall_architecture`. Summary: all honeycomb reads go through `palace_recall` (or its MCP exposure); no direct-disk reads of closet files. Env vars `BEES_ACTOR`, `BEES_STAGE`, `BEES_MODEL` propagate actor identity. Every tool call appends a JSONL record to `.bees/<slug>/mcp-calls.jsonl`.

`index.md`: TOC listing `api-surface` and `env-contract` drawers.

`api-surface.md`: single-API rule — all honeycomb access goes through `lib/honeycomb/recall.py` or the MCP server; `closet.md` files must never be read directly. `palace_recall` is the entry point for queens, scribes, builders, and the bees host process. `_compose_appended_prompt` is rewritten to call `palace_recall(...)` instead of `Path.read_text`. Petition tools (`palace_petition_submit/list/withdraw`) are additive; they do not bypass the recall path. Reference ADR-0001 §Decision point 1.

`env-contract.md`: the five env vars the MCP server reads (`BEES_FEATURE_SLUG`, `BEES_REPO_ROOT`, `BEES_ACTOR`, `BEES_STAGE`, `BEES_MODEL`). First two existed in v1.0; last three are new in v1.1. Missing values are non-fatal and log as `"unknown"`. The bees harness is expected to set all five for every MCP spawn. Log destination is `$BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl`; dev fallback is `$HONEYCOMB_ROOT/.calls.jsonl` when slug/root unset. Reference ADR-0004 §1 and §3.

### wing_repo_bees/architecture/palace-recall/ (NEW)

`closet.md` (≤500 chars): HTML-comment header with `Hall: hall_architecture`. Summary: `palace_recall(query, wings, top_k, drawer, include_pending, tool, tool_version, consumer)` is the single recall entry point. Overlay files take precedence over canon for matching drawer paths. Every call appends a JSONL log record.

`index.md`: TOC listing `overlay-semantics` and `log-side-effect` drawers.

`overlay-semantics.md`: `include_pending` (default True) merges consumer overlay results alongside canon. When `$BEES_REPO_ROOT/.bees/honeycomb-overlay/` exists, overlay drawer files win for matching paths. Scope params (`tool`, `tool_version`, `consumer`) select the matching scoped index; absent params fall back to env-derived values then to canon. In v1.1, one ChromaDB collection covers the install-time flattened view; per-scope collections deferred. Reference ADR-0001 §5 and ADR-0002 §5.

`log-side-effect.md`: every `palace_recall` (and petition tool) call writes one JSONL record synchronously before returning. Schema: `schema_version: 1`, `ts` (ISO-8601 UTC), `tool`, `slug`, `actor`, `stage`, `model`, `request` (query, wings, top_k, drawer, engine), `response` (result_count, results array with wing/room/closet/bytes/score/source/content_sha), `duration_ms`. `bytes` = rendered bytes of returned content. `content_sha` = sha256 hex of returned content. `source` = `"canon"` | `"consumer-overlay"` | `"honey-<name>@<ver>"`. Synchronous `flush()` before MCP response returns. `fcntl.flock` around the append for multi-process safety. Reference ADR-0004 §2 and §4.

## Success check

1. All 8 output files exist at their declared paths within the cell.
2. Both `closet.md` files are ≤500 chars.
3. `env-contract.md` contains `BEES_ACTOR`, `BEES_STAGE`, `BEES_MODEL`.
4. `overlay-semantics.md` contains "overlay" and "include_pending".
5. `log-side-effect.md` contains "schema_version" and "content_sha".
6. All files committed in a single commit with the prescribed subject line.
7. Spec path referenced in commit body.

## Commit message

```
bees scribe-only: honeycomb-v1-1 011 — New architecture closets (2).

Add wing_repo_bees/architecture/honeycomb-access/ (single API surface,
env contract for BEES_ACTOR/STAGE/MODEL, observability log destination)
and wing_repo_bees/architecture/palace-recall/ (overlay/include_pending
semantics, scope-aware behaviour, JSONL log-record side-effect).

Refs: .bees/honeycomb-v1-1/specs/011-new-architecture-closets-2.md
```
