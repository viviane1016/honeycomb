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

## v1.1.1 — 2026-05-30

### Fixed

- **Overlay plumbing** — `bin/honeycomb-mcp` now passes `overlay_root` to
  `palace_recall` and `palace_recall_semantic` dispatches. Previously the parameter
  was accepted by the library but never threaded through from the MCP server, so the
  overlay was silently ignored at recall time.
- **`source` field on recall results** — result entries now carry `source: "canon"` or
  `source: "consumer-overlay"` so callers can distinguish where each drawer came from.
- **Log-writer import cached** — `_load_log_writer` in `bin/honeycomb-mcp` now inserts
  `sys.path` and imports `honeycomb.log` exactly once (module-level cache); prior
  behaviour re-ran the import on every tool call.
- **Install no-op gate** — `tools/install.sh` skips the petition-manifest write and
  the `Petitions:` summary print when the canon SHA has not changed. Fixes the
  "byte-identical to v1.0" acceptance criterion for no-change installs.
- **Duplicate section label** — renamed second `# ── 4.` in `tools/install.sh` to
  `# ── 5.` so section numbers are monotonically increasing.
- **`petition_id` removed** — `PetitionResult` and `PendingPetition` no longer carry
  a date-sequenced `petition_id`. Identity is the override file's path within canon.
  `palace_petition_withdraw` now accepts `path` instead of `petition_id`.
  Branch names are derived deterministically from the path.
  `palace_petition_submit` returns `{branch, pr_url, overlay_path}`.
  `palace_petition_list` entries carry `{target, consumer, tool, tool_version,
  path, source, rationale}`.

### Backwards compatibility

The frontmatter parser ignores unknown fields; any `petition_id:` lines in override
files written by v1.1.0 are silently ignored by v1.1.1+. No migration needed.

---

## v1.1.0 — 2026-05-30

### Added

- **Drawer overrides** — `<drawer>.queenfile_<scope>.md` filename convention for
  per-scope canonical-drawer variants (ADR-0002). Override files carry authoritative
  frontmatter (`target`, `tool`, `tool_version`, `consumer`, `rationale`).
- **Scope-aware install** — `tools/install.sh` gains `--tool`, `--tool-version`,
  `--consumer` flags. Absent flags = canonical-only (v1.0 behaviour). When any
  flag is supplied, the installer resolves overrides for that context and materializes
  a flattened view before reindexing.
- **Specificity ranking** — axes-matched > version-specificity (exact `==` beats
  range `>=`) > consumer-specificity > mtime tiebreaker. Lint flags ambiguous
  overlapping overrides.
- **Petition MCP tools** — three new tools: `palace_petition_submit`,
  `palace_petition_list`, `palace_petition_withdraw`. Petitions are override files
  written to a feature branch in canon and opened as PRs. Optional consumer-side
  overlay for immediate self-recall before PR merge.
- **Consumer overlay** — `palace_recall` and `palace_recall_semantic` accept an
  optional overlay root. `bin/honeycomb-mcp` passes
  `$BEES_REPO_ROOT/.bees/honeycomb-overlay/` when present; overlay files win over
  canon for matching drawer paths. Absent overlay = v1.0 behaviour.
- **Observability log** — `lib/honeycomb/log.py` writes one JSONL record per MCP
  tool call to `$BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl`. Schema v1 includes
  `ts`, `tool`, `slug`, `actor`, `stage`, `model`, `request`, `response`,
  `duration_ms`, `bytes`, `content_sha`. Missing actor env vars log as `"unknown"`.
  Dev fallback: `$HONEYCOMB_ROOT/.calls.jsonl`. Concurrent-write safety via
  `fcntl.flock`.
- **Petition manifest** — `lib/honeycomb/manifest.py` classifies merged/declined/
  pending petitions since the previous install by commit-message convention
  (`petition: adopted|declined|pending`). `tools/install.sh` prints a one-line
  summary after each pull.
- **New content** — 9 new closets across `wing_bees/plan/` and `wing_repo_bees/`:
  `petitions-flow`, `queenfile-contract`, updated `palace-petitions`,
  `honeycomb-access`, `palace-recall`, `surveyor`, `honeycomb-stewards`,
  updated `role-queen`, updated `scribe-model-tiers`.
- **Decisions index** — `decisions/INDEX.md` listing all four ADRs.
- **Backlog** — `BACKLOG.md` tracking shipped v1.1 items and deferred work.
- **Actor identity env vars** — `BEES_ACTOR`, `BEES_STAGE`, `BEES_MODEL`
  propagated into MCP log records; missing values log as `"unknown"`.

### Backwards compatibility

No v1.0 API removed. `palace_recall` keeps its v1.0 signature; overlay and scope
behaviour are keyed by env / flag presence. A bees v1.17 install without override
flags returns byte-identical results to v1.0.

---

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
