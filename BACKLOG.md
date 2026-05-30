# Backlog

## Shipped in v1.1.0

- [x] Drawer override file format and frontmatter parser (`lib/honeycomb/overrides.py`)
- [x] Override resolution + specificity ranking (`rank_by_specificity`, `resolve_overrides`)
- [x] Flattened-view materializer + scope-aware `tools/install.sh` (`--tool`, `--tool-version`, `--consumer`)
- [x] MCP log writer (`lib/honeycomb/log.py`) with synchronous JSONL append and `fcntl.flock`
- [x] Log writer wired into `bin/honeycomb-mcp` for `palace_recall` and `palace_recall_semantic`
- [x] Petition helpers (`lib/honeycomb/petitions.py`): `submit`, `list_pending`, `withdraw`
- [x] Petition MCP tools registered in `bin/honeycomb-mcp`: `palace_petition_submit`, `palace_petition_list`, `palace_petition_withdraw`
- [x] Consumer overlay support in `lib/honeycomb/recall.py` and `lib/honeycomb/semantic.py`
- [x] Petition manifest generator (`lib/honeycomb/manifest.py`) + operator output in `tools/install.sh`
- [x] New plan-room closets: `wing_bees/plan/petitions-flow/`, `wing_bees/plan/queenfile-contract/`, updated `wing_bees/plan/palace-petitions/`
- [x] New architecture closets: `wing_repo_bees/architecture/honeycomb-access/`, `wing_repo_bees/architecture/palace-recall/`
- [x] New + updated actor closets: `wing_repo_bees/actor/surveyor/`, `wing_repo_bees/actor/honeycomb-stewards/`, updated `role-queen`, updated `scribe-model-tiers`
- [x] `decisions/INDEX.md` — short index of all four ADRs
- [x] `BACKLOG.md` — this file
- [x] `README.md` updated for v1.1 (scope flags, env vars, petition tools, overlay, log)
- [x] `CHANGELOG.md` v1.1.0 entry
- [x] `VERSION` → 1.1.0
- [x] `wing_bees/_manifest.yaml` version → 1.1.0

## Shipped in v1.1.0 fixups

- [x] `bin/honeycomb-mcp` wires `overlay_root` through `palace_recall` and `palace_recall_semantic` dispatches (spec 001)
- [x] `_load_log_writer` cached at module level — `sys.path` insert and `honeycomb.log` import happen exactly once (spec 001)
- [x] `source` field (`"canon"` / `"consumer-overlay"`) added to result entries in `lib/honeycomb/recall.py` and `lib/honeycomb/semantic.py` (spec 001)
- [x] `tools/install.sh` petition-manifest block gated: no-op install skips write and print; fresh install writes manifest but does not print summary; duplicate `# ── 4.` section renumbered to `# ── 5.` (spec 002)
- [x] `petition_id` removed from `PetitionResult`, `PendingPetition`, override-file frontmatter, and all MCP tool descriptors; `palace_petition_withdraw` now takes `path` (spec 003)
- [x] Docs synced: ADR-0002 supersession note, `wing_bees/plan` petition docs updated, `palace-petitions/index.md` reordered, `README.md` install-summary qualified, CHANGELOG v1.1.1 entry, VERSION 1.1.1 (spec 004)

## Deferred

### v1.2 — Honey packs (ADR-0003)

Distributable content modules: third-party honeycomb wings as standalone
`pip`-installable packages. Lets model-family maintainers, tool maintainers,
and consumer teams publish wings independently of canon.

- Design: ADR-0003 (`decisions/0003-honey-packs.md`)
- Blocked on: stabilising the override mechanism across one real release cycle

### Bees-side observability consumer

MCP call log correlation + signal heuristics on the bees side:

- Correlate log records with bees stage outcomes (did the recall help?)
- Heuristic: closet bytes >> actual tokens used → candidate for splitting
- Retro-petition emission: if a miss pattern is detected in logs, propose a petition automatically
- Tracked in bees BACKLOG (not this repo)

### Log redaction hook

`lib/honeycomb/log.py` currently writes `request` and `response` verbatim.
For consumers with sensitive content in palace queries, a redaction hook
(`HONEYCOMB_LOG_REDACT_FN`) should let operators strip or hash content fields
before the record is written. Deferred: no known need in v1.1 consumers.

### Per-scope ChromaDB collections

ADR-0002 §3 considered maintaining a separate vector index per override scope.
Collapsed in v1.1 to a single ChromaDB collection over the install-time
flattened view. Per-scope collections would allow scope-switching without
reinstall but add index-management complexity. Revisit in v1.2 if scope
switching becomes a common operator workflow.

### Multi-tool concurrent consumer

A single `honeycomb-mcp` process serving multiple concurrent bees subprocesses
(e.g. parallel scribes) relies on `fcntl.flock` for log append safety. If
contention proves significant under heavy parallelism, replace with a write-side
queue or a dedicated log-collector subprocess. Monitor via log record timestamps
and gap analysis.

### Bees-excise

Removing the legacy `bees/honeycomb/` directory from the bees repo is gated on
v1.1 shipping and bees v1.17 being retired. Tracked as a bees feature, not here.

### Override depth (overrides of overrides)

v1.1 supports single-layer overrides only. If a honey pack ships an override
that a consumer wants to further customise, there is no mechanism for it in v1.1.
Punted: the use case hasn't materialised; single-layer is easier to reason about.
