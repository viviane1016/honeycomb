## Goal

Implement honeycomb v1.1: drawer-override mechanism, install-time scope resolution, petition flow, and MCP-side observability.

## Motivation

Honeycomb v1.0 shipped the four-level structure and a working MCP recall surface. Four open architectural concerns block bees-excise and the broader palace-tuning loop:

1. **Petitions have no working home post-cutover.** Today bees writes accepted petitions into `bees/honeycomb/`, the in-tree legacy corpus. After excise, that corpus is gone — petitions need a new endpoint.
2. **No mechanism to evolve content without lock-stepping bees and honeycomb releases.** Bees v1.18 prompt/contract changes today require coordinated bees + honeycomb releases. With queries growing, the coupling is becoming a bottleneck.
3. **Consumer customization has no shape.** Operators who want to tweak honeycomb content for their project have nowhere to put it that recall will pick up. The queenfile concept exists in name but has no schema or recall integration.
4. **No feedback loop for tuning the palace.** We can't tell which closets are bloated, which queries miss, or which procedures fail in practice. Curators are flying blind.

Four ADRs cover the design: ADR-0001 (MCP-mediated petitions, single API), ADR-0002 (drawer overrides + scoped install-time resolution), ADR-0004 (per-call observability + actor identity). ADR-0003 (honey packs) is deferred to v1.2. ADR-0001 is partially superseded by ADR-0002 — the architectural intent stands; the mechanism reference is ADR-0002.

## Expected outcome

- A consumer running bees v1.17 against honeycomb v1.1 calls `palace_recall` and gets results indistinguishable from v1.0 behaviour. Backwards-compatible default.
- A consumer running bees v1.18-dev with `behaviour.queenfile_bees-v1.18.md` override files in canon transparently gets the v1.18 variants. No bees source-code change required for prompt-only features.
- A consumer's queen calls `palace_petition_submit(target, content, rationale)`; honeycomb writes a `<drawer>.queenfile_<consumer>.md` file to a feature branch in `~/.honeycomb`, opens a PR against `viviane1016/honeycomb`, and (optionally) writes the same file to a consumer-side overlay for immediate self-visibility.
- `bash ~/.honeycomb/tools/install.sh` resolves canon for the consumer's tool version + consumer identity at install time, writes a flattened view to `~/.honeycomb/wing_*/`, builds one ChromaDB collection over it, and emits a petition report manifest naming which petitions were accepted/declined/still-pending since the previous install.
- Every `palace_recall` call writes a JSONL record to `$BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl` with actor identity (`BEES_ACTOR`, `BEES_STAGE`, `BEES_MODEL`), request/response details, returned bytes, and content shas — enabling bees-side correlation with actor outcomes for the retro-petition feedback loop (bees-side work; honeycomb commits to the log contract).
- bees-excise unblocks: bees v1.17.x can be cut over to consume v1.1 with `_compose_appended_prompt` routed through the recall library, petition parser routed through `palace_petition_submit`, and the legacy `bees/honeycomb/` + in-tree MCP infra deleted.

## In scope

- `palace_petition_submit` MCP tool (writes override file to canon feature branch, opens PR, writes overlay copy)
- `palace_petition_list` MCP tool (walks override files matching consumer scope)
- `palace_petition_withdraw` MCP tool (removes override file, closes PR)
- Drawer-override file format: filename pattern (`<drawer>.queenfile_<scope>.md`) + frontmatter schema (target, tool, tool_version, consumer, rationale, etc.)
- Override-resolution algorithm in `lib/honeycomb/recall.py` — runs at install time, produces flattened view
- Specificity ranking: axes-matched > version-specificity > consumer-specificity > mtime tiebreaker
- Scope-aware install workflow in `tools/install.sh`: takes `(tool, tool_version, consumer)`, resolves canon, writes flattened view, reindexes
- Consumer-side overlay at `$BEES_REPO_ROOT/.bees/honeycomb-overlay/` for in-flight petitions (consumer's own submissions before PR merge)
- Petition manifest schema and generation algorithm (commit-message convention walker)
- Operator-facing upgrade output (summary of accepted/declined/pending petitions)
- MCP server env contract: `BEES_ACTOR`, `BEES_STAGE`, `BEES_MODEL` propagated to log
- Per-call JSONL log writer: schema v1, synchronous flush, destination `$BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl`
- New + updated honeycomb content for v1.1 concepts (~9 closets per ADR-0001 §H7 — petition flow, queenfile contract, MCP-mediated access, overrides, role-queen + role-scribe updates, palace_recall update)
- Backwards-compat behaviour: when overlay is absent, recall walks canon only; default install (no overrides anywhere) returns identical results to v1.0
- Tests covering: override resolution edge cases, scope key composition, recall + overlay merge, MCP log schema, petition submit/withdraw, install-time resolution determinism
- Documentation: README updates pointing at the new install flow, install.sh `--help` covers the new args, ADRs referenced from `decisions/INDEX.md` (new — short index of all four ADRs)

## Out of scope

- Honey pack architecture (ADR-0003; deferred to honeycomb v1.2)
- Central pack registry, pack signing, smart-suggestion install heuristics
- Bees-side consumer of the observability log (correlation, signal heuristics, retro-petition emission) — depends on v1.1 contract being live; tracked as bees BACKLOG
- Bees-excise itself (depends on v1.1 shipping; separate bees feature)
- Multi-tool concurrent consumer (only bees consumes honeycomb in v1.1)
- Override depth (overrides of overrides) — single-layer only
- Cross-feature recall trace rollup
- Redaction hook for sensitive content in logs
- Auto-PR machinery for consumers without `gh` CLI; v1.1 assumes `gh` is installed and authenticated
- Curated v1.0 closet hand-curation (the broader content polish across all 77 v1.0 closets) — separate effort

## Issue references

Refs ADR-0001, ADR-0002, ADR-0004 (`decisions/0001-...`, `0002-...`, `0004-...`).

## Operator amendments

<!-- Timestamped entries appended as the operator amends intent after plan approval. -->
