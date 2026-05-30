---
type: scribe-only
depends-on: [003, 005, 007, 008, 009, 010, 011, 012]
output-files:
  - README.md
  - CHANGELOG.md
  - VERSION
  - wing_bees/_manifest.yaml
  - decisions/INDEX.md
  - BACKLOG.md
---

# Spec 013 — Docs + version bump + decisions index + backlog

## Builder model

claude-sonnet-4-6

## Goal

Update `README.md`, `CHANGELOG.md`, `VERSION`, and `wing_bees/_manifest.yaml` to reflect the v1.1.0 release; create `decisions/INDEX.md` listing all four ADRs; create `BACKLOG.md` capturing shipped v1.1 items and deferred work.

## Scope

**Files written/edited:**

- `README.md` — add v1.1 install scope flags, new env vars (`BEES_ACTOR`, `BEES_STAGE`, `BEES_MODEL`), override mechanism overview, consumer overlay location, log destination, petition MCP tools
- `CHANGELOG.md` — prepend `v1.1.0` entry (added: overrides, scope-aware install, petition MCP tools, observability log, consumer overlay)
- `VERSION` — bump from `1.0.1` to `1.1.0`
- `wing_bees/_manifest.yaml` — bump `version` from `1.0.0` to `1.1.0`; add new canonical rooms introduced in v1.1
- `decisions/INDEX.md` — new file; short-form index of all four ADRs with one-line summaries and statuses
- `BACKLOG.md` — new file; shipped v1.1 items + deferred items

**Non-goals:**

- No changes to library modules or binary files.
- No changes to wing content files.
- No changes to test files.

## Failing test

No automated test gates this spec. Verification is by inspection:
`grep -q "1.1.0" VERSION && grep -q "v1.1.0" CHANGELOG.md && test -f decisions/INDEX.md && test -f BACKLOG.md`.

## Builder prompt

You are acting as both scribe and builder for spec 013. Apply these exact file changes:

**1. VERSION** — replace `1.0.1` with `1.1.0` (single line, no trailing content).

**2. wing_bees/_manifest.yaml** — change `version: 1.0.0` to `version: 1.1.0`. Add new canonical room entries for rooms added in v1.1 that are not yet listed: none needed beyond the existing set for v1.1.

**3. CHANGELOG.md** — prepend a `## v1.1.0 — 2026-05-30` section immediately after the preamble (before the `## v1.0.0` entry). Content:

```
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

### Actor identity env vars (new in v1.1)

| Var | Purpose |
|---|---|
| `BEES_ACTOR` | Role name propagated into MCP log records (e.g. `queen`, `scribe`) |
| `BEES_STAGE` | Bees pipeline stage (e.g. `plan`, `spec`, `ship`) |
| `BEES_MODEL` | Model ID driving the calling actor |

Missing → logged as `"unknown"`.

### Backwards compatibility

No v1.0 API removed. `palace_recall` keeps its v1.0 signature; overlay and scope
behaviour are keyed by env / flag presence. A bees v1.17 install without override
flags returns byte-identical results to v1.0.
```

**4. README.md** — append a new `## v1.1 features` section after `## Versioning`, and update the `### Install`, `### Environment`, and `### MCP config` sub-sections as follows:

- Under `### Install`, add a note about scope flags (v1.1):
  ```
  ### Install
  
  ```bash
  git clone --depth 1 --branch v1.1.0 https://github.com/viviane1016/honeycomb ~/.honeycomb
  ```
  
  **Scope-aware install (v1.1):** pass `--tool`, `--tool-version`, and/or `--consumer`
  to resolve drawer overrides for your context. Absent flags = canonical-only (v1.0 behaviour):
  
  ```bash
  # canonical-only (v1.0-compatible):
  bash ~/.honeycomb/tools/install.sh
  
  # scope-resolved for bees v1.18:
  bash ~/.honeycomb/tools/install.sh --tool bees --tool-version v1.18 --consumer scarab
  ```
  
  After each install, a one-line petition manifest summary is printed:
  `Petitions: N accepted, M declined, K pending since v<prev>`.
  ```

- Under `### Environment`, add the three new v1.1 env vars.

- Add `### Petition tools (v1.1)` sub-section.

- Add `### Consumer overlay (v1.1)` sub-section.

- Add `### Observability log (v1.1)` sub-section.

The README additions preserve all existing content unchanged.

**5. decisions/INDEX.md** — create new file:

```markdown
# Decisions index

| ADR | Title | Status | Summary |
|---|---|---|---|
| [ADR-0001](0001-mcp-mediated-queenfile-and-petitions.md) | MCP-mediated queenfile, petition flow, and single-API access | Partially superseded (see ADR-0002) | Establishes MCP as the single recall API surface; consumer-side queenfile as overlay; petitions as the consumer→canon PR bridge. Mechanism refined by ADR-0002; architectural intent unchanged. |
| [ADR-0002](0002-drawer-overrides-scoped-indexes.md) | Drawer overrides with scope-keyed semantic indexes | Proposed | Collapses queenfile + petition into one mechanism: `<drawer>.queenfile_<scope>.md` override files. Install-time specificity ranking; single ChromaDB collection over the flattened view. Shipped in v1.1. |
| [ADR-0003](0003-honey-packs.md) | Honey packs — à la carte content modules | Deferred (v1.2) | Distributable content modules letting third-party maintainers publish honeycomb wings as standalone packages. Deferred post-v1.1 to avoid scope creep. |
| [ADR-0004](0004-mcp-observability-actor-identity.md) | MCP-side observability + actor-identity logging | Proposed | Per-call JSONL log with actor identity, duration, bytes, and content SHA. Env vars `BEES_ACTOR`, `BEES_STAGE`, `BEES_MODEL`. Shipped in v1.1. |
```

**6. BACKLOG.md** — create new file with shipped v1.1 items and deferred items.

## Success check

- `VERSION` contains exactly `1.1.0`.
- `CHANGELOG.md` contains a `## v1.1.0` section.
- `wing_bees/_manifest.yaml` `version` field reads `1.1.0`.
- `decisions/INDEX.md` exists and references all four ADRs.
- `BACKLOG.md` exists and contains the deferred items list.
- `README.md` contains references to `--tool`, `BEES_ACTOR`, `palace_petition_submit`, and consumer overlay.

## Commit message

```
bees scribe-only: honeycomb-v1-1 013 — Docs + version bump + decisions index + backlog.

Bumps VERSION → 1.1.0, wing_bees/_manifest.yaml → 1.1.0. Prepends v1.1.0
CHANGELOG entry. Updates README with scope-aware install, env vars, petition
tools, consumer overlay, and observability log. Adds decisions/INDEX.md (all
four ADRs) and BACKLOG.md (shipped + deferred items).

Refs: .bees/honeycomb-v1-1/specs/013-docs-version-bump-decisions-index-backlog.md
```
