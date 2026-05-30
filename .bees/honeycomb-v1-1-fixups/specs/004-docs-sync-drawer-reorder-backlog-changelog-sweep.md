---
type: scribe-only
depends-on: [001, 002, 003]
output-files:
  - decisions/0002-drawer-overrides-scoped-indexes.md
  - wing_bees/plan/palace-petitions/index.md
  - wing_bees/plan/palace-petitions/parser-and-emitter.md
  - wing_bees/plan/petitions-flow/mcp-tool-emission.md
  - wing_bees/plan/petitions-flow/lifecycle.md
  - README.md
  - BACKLOG.md
  - CHANGELOG.md
  - VERSION
scribe-model: claude-sonnet-4-6
---

# Spec 004 — Docs sync, drawer reorder, BACKLOG/CHANGELOG sweep

## Builder model

claude-sonnet-4-6

## Goal

Sync all documentation with the v1.1.0 fixups shipped in units 001–003: append a supersession note to ADR-0002 recording that petition identity is the override file path (not a date-sequenced id), remove `petition_id` from wing_bees plan files, reorder `palace-petitions/index.md` so `migration` is last, qualify the README install-summary claim, and record the fixup in BACKLOG, CHANGELOG (v1.1.1), and VERSION.

## Scope

**Files edited:**

- `decisions/0002-drawer-overrides-scoped-indexes.md` — append supersession note at end of file
- `wing_bees/plan/palace-petitions/index.md` — reorder drawers: petition-shapes → parser-and-emitter → statuses → related-decisions → migration
- `wing_bees/plan/palace-petitions/parser-and-emitter.md` — remove `petition_id` from submit return shape
- `wing_bees/plan/petitions-flow/mcp-tool-emission.md` — remove `petition_id` from submit and list return shapes; change withdraw signature from `petition_id` to `path`
- `wing_bees/plan/petitions-flow/lifecycle.md` — change withdraw reference from `petition_id` to `path`
- `README.md` — qualify the post-install summary claim to apply only when canon was updated
- `BACKLOG.md` — add "Shipped in v1.1.0 fixups" subsection listing the five resolved concerns
- `CHANGELOG.md` — add v1.1.1 entry (v1.1.0 is already tagged)
- `VERSION` — bump to 1.1.1

**Files grep-verified (no edit needed):**

- `wing_bees/plan/palace-petitions/closet.md` — no `petition_id` mention
- `wing_bees/plan/palace-petitions/migration.md` — no `petition_id` mention

**Explicit non-goals:**

- `decisions/0001-mcp-mediated-queenfile-and-petitions.md` — ADR-0001 retains its original `petition_id` references as historical record; only ADR-0002 receives the supersession note
- Any code file (`bin/`, `lib/`, `tests/`) — covered by specs 001–003
- `tools/install.sh` — covered by spec 002
- Renaming any file or directory

## Failing test

No executable test for a pure-doc scribe-only unit. The acceptance checks are:

1. `grep -n "petition_id" wing_bees/plan/palace-petitions/parser-and-emitter.md` returns no matches.
2. `grep -n "petition_id" wing_bees/plan/petitions-flow/mcp-tool-emission.md` returns no matches.
3. `grep -n "petition_id" wing_bees/plan/petitions-flow/lifecycle.md` returns no matches.
4. `tail -20 decisions/0002-drawer-overrides-scoped-indexes.md` contains "superseded" or "Post-v1.1.0" text.
5. `tail -1 wing_bees/plan/palace-petitions/index.md` references `migration`.
6. `cat VERSION` outputs `1.1.1`.
7. `grep "v1.1.1" CHANGELOG.md` returns a match.
8. `grep "Shipped in v1.1.0 fixups" BACKLOG.md` returns a match.

## Builder prompt

You are the scribe-only builder for spec 004 of the `honeycomb-v1-1-fixups` plan.
Your job is to apply the documentation edits described below. Touch ONLY the files
listed. Do not edit code files, test files, or `decisions/0001-*.md`.

---

### 1. `decisions/0002-drawer-overrides-scoped-indexes.md`

Append the following block at the very end of the file (after all existing content):

```
---

## Post-v1.1.0 supersession note

**Petition identity is the override file path, not a date-sequenced id.**

The v1.1.0 implementation shipped `petition_id` (a `YYYYMMDD-NNN-<scope>` string)
in `PetitionResult` and `PendingPetition`, generated via `git log` date and a
`rglob`-based counter. The retro identified this as unnecessary complexity: the
override file's path within canon (e.g. `wing_bees/build/manual-amend/behaviour.queenfile_scarab.md`)
is already a unique, stable, human-readable identity.

**Changes in the v1.1.0 fixup (shipped on the `honeycomb-v1-1-fixups` branch):**

- `petition_id` field removed from `PetitionResult` and `PendingPetition` dataclasses
  in `lib/honeycomb/petitions.py`.
- `palace_petition_withdraw` now takes `path: str` (the override file's relative path
  within canon) instead of `petition_id`.
- Branch names are derived deterministically from the override file path
  (e.g. `feat/petition-<sha1(rel_path)[:12]>`); no date or counter logic.
- `palace_petition_submit` returns `{branch, pr_url, overlay_path}` — no `petition_id`.
- `palace_petition_list` entries carry `{target, consumer, tool, tool_version, path,
  source, rationale}` — no `petition_id`.
- The HTML-comment frontmatter written into override files no longer contains a
  `petition_id:` line.

**Backwards compatibility:** The frontmatter parser ignores unknown fields, so any
`petition_id:` lines in override files written by v1.1.0 are silently ignored by
v1.1.1+. No migration script is needed.
```

---

### 2. `wing_bees/plan/palace-petitions/index.md`

Replace the entire file content with the reordered drawer list (migration moved to last):

```
## Drawers

- **petition-shapes** — Legacy petition shapes (deprecated; for operator reference during the compat window)
- **parser-and-emitter** — v1.1 MCP tool path and legacy block translation layer
- **statuses** — Petition statuses and petition manifest summary
- **related-decisions** — Related decisions
- **migration** — Block→tool migration table and one-release backwards-compat window
```

---

### 3. `wing_bees/plan/palace-petitions/parser-and-emitter.md`

In the v1.1 path paragraph, change:

```
and returns `{petition_id, branch, pr_url}`.
```

to:

```
and returns `{branch, pr_url, overlay_path}`.
```

---

### 4. `wing_bees/plan/petitions-flow/mcp-tool-emission.md`

Three changes in this file:

**a.** In the `palace_petition_submit` paragraph, change:

```
and returns `{petition_id, branch, pr_url, overlay_path}`.
```

to:

```
and returns `{branch, pr_url, overlay_path}`.
```

**b.** In the `palace_petition_list` paragraph, change:

```
Returns a list of `{petition_id, target, branch, pr_url, status}`.
```

to:

```
Returns a list of `{target, consumer, tool, tool_version, path, source, rationale}`.
```

**c.** Change the section heading:

```
### `palace_petition_withdraw(petition_id)`
```

to:

```
### `palace_petition_withdraw(path)`
```

And update the description sentence for withdraw to replace any reference to `petition_id` with `path` (the override file's relative path within canon).

---

### 5. `wing_bees/plan/petitions-flow/lifecycle.md`

In step 5 (Withdrawn), change:

```
`palace_petition_withdraw(petition_id)` removes the override from the canon branch, closes the PR, and removes the local overlay copy.
```

to:

```
`palace_petition_withdraw(path=<override-file-path>)` removes the override from the canon branch, closes the PR, and removes the local overlay copy.
```

---

### 6. `README.md`

Find the line:

```
After each install, a one-line petition manifest summary is printed:
```

Replace it with:

```
After an install that updates canon, a one-line petition manifest summary is printed:
```

---

### 7. `BACKLOG.md`

Insert a new `## Shipped in v1.1.0 fixups` section immediately after the `## Shipped in v1.1.0` section (before the `## Deferred` heading). Content:

```
## Shipped in v1.1.0 fixups

- [x] `bin/honeycomb-mcp` wires `overlay_root` through `palace_recall` and `palace_recall_semantic` dispatches (spec 001)
- [x] `_load_log_writer` cached at module level — `sys.path` insert and `honeycomb.log` import happen exactly once (spec 001)
- [x] `source` field (`"canon"` / `"consumer-overlay"`) added to result entries in `lib/honeycomb/recall.py` and `lib/honeycomb/semantic.py` (spec 001)
- [x] `tools/install.sh` petition-manifest block gated: no-op install skips write and print; fresh install writes manifest but does not print summary; duplicate `# ── 4.` section renumbered to `# ── 5.` (spec 002)
- [x] `petition_id` removed from `PetitionResult`, `PendingPetition`, override-file frontmatter, and all MCP tool descriptors; `palace_petition_withdraw` now takes `path` (spec 003)
- [x] Docs synced: ADR-0002 supersession note, `wing_bees/plan` petition docs updated, `palace-petitions/index.md` reordered, `README.md` install-summary qualified, CHANGELOG v1.1.1 entry, VERSION 1.1.1 (spec 004)
```

---

### 8. `CHANGELOG.md`

Insert a new `## v1.1.1` entry immediately after the opening header block (before the `## v1.1.0` entry). Content:

```
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
  the `Petitions:` summary print when the canon SHA has not changed. Fixes
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
```

---

### 9. `VERSION`

Replace the file content with:

```
1.1.1
```

---

After making all edits, run the acceptance grep checks listed in the spec's "Failing test" section to confirm they all pass.

## Success check

1. All eight acceptance greps listed in "Failing test" pass.
2. `grep -n "petition_id" wing_bees/plan/petitions-flow/mcp-tool-emission.md` returns no matches.
3. `tail -5 wing_bees/plan/palace-petitions/index.md` contains `migration`.
4. `cat VERSION` outputs `1.1.1`.
5. No files outside the `output-files` list have been modified (verify with `git diff --name-only`).

## Commit message

```
docs(honeycomb-v1-1-fixups): sync docs for v1.1.1 fixup ship (#004)

- decisions/0002: append supersession note — petition identity is path, not id
- wing_bees/plan/palace-petitions/index.md: move migration drawer to last
- wing_bees/plan/palace-petitions/parser-and-emitter.md: drop petition_id from return shape
- wing_bees/plan/petitions-flow/mcp-tool-emission.md: drop petition_id from submit/list shapes; withdraw takes path
- wing_bees/plan/petitions-flow/lifecycle.md: withdraw reference uses path parameter
- README.md: qualify install-summary claim to canon-update installs only
- BACKLOG.md: add "Shipped in v1.1.0 fixups" subsection
- CHANGELOG.md: add v1.1.1 entry
- VERSION: 1.1.0 → 1.1.1

Refs: .bees/honeycomb-v1-1-fixups/specs/004-docs-sync-drawer-reorder-backlog-changelog-sweep.md
```
