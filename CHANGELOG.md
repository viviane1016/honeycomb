# Changelog

Honeycomb releases use semver at two levels:

- **Top-level** (`VERSION`) — overall release across all wings.
- **Per-wing** (`wing_*/_manifest.yaml: version:`) — wings move
  independently; top-level aggregates the highest bump kind across
  wings.

Semver semantics:

- **PATCH** — closet text edit, drawer text edit, frontmatter tweak.
- **MINOR** — new closet, new drawer, new tag namespace, new canonical
  room added to manifest. Additive only.
- **MAJOR** — closet removed or renamed, mandatory-drawer change,
  scope change, manifest restructure, breaking API contract change.

## v1.0.0 — 2026-05-29

First stable release of honeycomb as an independent repository.

### Added

- Four-level structure: wing / room / closet / drawer (ADR-0024).
- Canonical-content migration via `tools/migrate_v2.py` — drawers
  carry verbatim source sections, no LLM paraphrase (vs v0.x which
  had Haiku-synthesised paraphrase causing 7.2× content bloat).
- 77 closets across 6 wings:
  - `wing_bees` (runtime, v1.0.0) — 30 closets
  - `wing_repo_bees` (project:bees, v1.0.0) — 22 closets
  - `wing_practices` (universal, v1.0.0) — 17 closets
  - `wing_antipatterns` (universal, v1.0.0) — 3 closets
  - `wing_tools` (universal, v1.0.0) — 2 closets
  - `wing_models` (universal, v1.0.0) — 3 closets
- Standalone MCP server (`bin/honeycomb-mcp`) speaking JSON-RPC 2.0
  over stdio, server name `honeycomb` (distinct from legacy
  `bees-honeycomb` so both can run side-by-side during cutover).
- Two recall engines preserved from legacy bees-honeycomb:
  - `palace_recall` — keyword scoring (`lib/honeycomb/recall.py`)
  - `palace_recall_semantic` — ChromaDB vector recall
    (`lib/honeycomb/semantic.py`); cache at
    `~/.mempalace/honeycomb_v1/` (distinct from legacy cache so
    side-by-side install doesn't collide).
- API contract preserved 1:1 with legacy `bees-honeycomb` for day-1
  cutover compatibility. The `room` field in result dicts is now a
  composite `"<room>/<closet>"` string, giving structural
  disambiguation for closets that share names across rooms (e.g.
  `wing_bees/build/manual-amend` vs `wing_bees/orchestrate/manual-amend`).
- Forward-compat extension points declared in the recall signatures:
  `scope`, `tools`, `models`, `project`. Accepted-and-ignored in
  v1.0.0; will be wired in v1.1 for targeted recall.

### Migration

Migrated from legacy `bees/honeycomb/` (77 source `.md` files in
flat wing/<room>.md layout) to four-level structure.

- Expansion ratio: 0.87× (vs v1's deprecated 7.2× bloat) — drawers
  are byte-faithful verbatim section extractions.
- Single Haiku call per source for classification only; all drawer
  writes are mechanical Python section-splitting.
- One multi-source consolidation: `role-queen-orchestrator.md` +
  `stage-orchestrate.md` → `wing_bees/orchestrate/queen-orchestrator/`
  with `.multi-source` marker for operator review.

### Side-by-side validation

10 representative queries against both legacy `bees-honeycomb` and
new `honeycomb` MCPs returned semantically-equivalent context. The
new server's composite `room` field provides better closet-level
resolution where the legacy server's flat name was opaque.

### Known limitations

- `wing_models` ships as a singleton catalog. Future model-identity
  refactor (`wing_gemma_4`, `wing_claude_sonnet_4_6`, etc.) is
  tracked for v1.1+.
- Recall trace doesn't currently store content hashes or scoring
  metadata — tracked in BACKLOG.
- Day-2 honeycomb ADR work (consumer-local `wing_repo_<X>`, queen-file
  dissolution, cut bees over) is the next workstream.
