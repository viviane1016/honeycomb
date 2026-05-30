## Goal

Address the three accept-stage concerns and three observations from the `honeycomb-v1-1` review before merging PR #4.

## Motivation

`bees accept` on `feat/honeycomb-v1-1` flagged three real concerns and three lower-priority observations. The load-bearing one is concern #1: overlay precedence is implemented at the library level (`recall.py` / `semantic.py`) and unit-tested there, but `bin/honeycomb-mcp` never passes the `overlay_root` argument when dispatching `palace_recall` or `palace_recall_semantic`. The user-visible consequence is that the entire "submit a petition, immediately recall it back" behaviour — the load-bearing motivation for ADR-0002's overlay design — is broken when accessed through the MCP server (the only path bees uses).

Concern #2 is an acceptance-bullet violation: `bash tools/install.sh` with no flags no longer produces a byte-identical install root to v1.0, because spec 009 unconditionally writes `$TARGET/.petition-manifest.json` and emits a `Petitions:` stdout line. Either the bullet was overly strict or the manifest needs a gate.

Concern #3 is cosmetic but visible: two adjacent sections in `tools/install.sh` are both labelled `# ── 4. …`.

Observation #2 (operator-flagged in retro) — the petition_id scheme `YYYYMMDD-NNN-<scope>` was over-engineering. The override file's path IS the petition identity (ADR-0002). If a numeric reference is needed, the honeycomb PR number is the natural one. Drop the date/sequence scheme entirely.

Observation #1 (`_load_log_writer` runs per-call, `sys.path.insert` accumulates) and observation #3 (drawer TOC ordering mismatch in `wing_bees/plan/palace-petitions/`) are small enough to fold into the same fixup PR.

The fixup ships as a small targeted feature merged on top of `feat/honeycomb-v1-1` (or directly to main if PR #4 has already merged by the time this dispatches).

## Expected outcome

- **End-to-end overlay precedence works through the MCP server.** Submitting a petition via `palace_petition_submit` writes a queenfile drawer at `$BEES_REPO_ROOT/.bees/honeycomb-overlay/<wing>/<room>/<closet>/<drawer>.queenfile_<scope>.md`. Calling `palace_recall` immediately after via the MCP server returns the overlay content with `source` correctly labelled (`consumer-overlay` rather than `canon`). An integration test in `tests/test_mcp_overlay_e2e.py` exercises the full submit-then-recall path through the MCP wire.
- **`bash tools/install.sh` with no flags reverts to producing a byte-identical install root to v1.0** for a no-change canon. The `Petitions:` summary line and `.petition-manifest.json` write are gated behind detection of an actual canon update (CURRENT_SHA != PREVIOUS_SHA in the manifest's prior state). Fresh installs (no prior manifest) emit the manifest but do not print the summary line for the no-op case. Plan's acceptance bullet stands.
- **`tools/install.sh` section numbering is monotonically increasing** — the duplicate `# ── 4.` is renumbered.
- **Petition identity is the override file's path.** The `YYYYMMDD-NNN-<scope>` `petition_id` field is gone from `palace_petition_submit`'s return value, `palace_petition_list`'s entries, and the queenfile drawer's frontmatter HTML comment. Where a numeric handle is genuinely useful (e.g. operator-facing diff messages), the honeycomb PR number (when `auto_pr=True` opened one) is used. The submit logic no longer counts files or formats dates.
- **`_load_log_writer` is a module-level cache.** First call imports `honeycomb.log` and stashes the writer; subsequent calls return the cached handle. No repeated `sys.path.insert`.
- **`wing_bees/plan/palace-petitions/index.md` drawer ordering matches the prompt-described order** in spec 010, with `migration` in the position the spec called for.
- All existing tests pass. New tests cover: MCP-wire overlay precedence, no-flags install byte-identical view, log writer single-load, petition-id-removed assertions.

## In scope

- Wire `overlay_root` plumbing through `bin/honeycomb-mcp`:
  - Resolve `overlay_root = $BEES_REPO_ROOT/.bees/honeycomb-overlay/` when `$BEES_REPO_ROOT` is set and the directory exists, else `None`
  - Pass `overlay_root=` into both `palace_recall(...)` and `palace_recall_semantic(...)` dispatches inside the MCP tool handlers
  - Same resolution used by `palace_petition_submit` and `palace_petition_list` for consistency
- Gate the install-time petition-manifest summary on actual canon change:
  - Read prior `.petition-manifest.json` if present
  - Only emit the `Petitions:` stdout line and update the manifest when `CURRENT_SHA` differs from prior `previous_sha`
  - Fresh installs (no prior manifest) write the manifest with `previous_sha=null` but emit no summary line
- Renumber `tools/install.sh` sections so each step has a unique number (`# ── 5. Always reindex` if "petition manifest" stays at 4)
- Drop petition numbering:
  - Remove the `YYYYMMDD-NNN-<scope>` `petition_id` field from `palace_petition_submit` return shape
  - Remove from `palace_petition_list` entry shape
  - Remove from the queenfile drawer's frontmatter HTML comment (`petition_id:` line)
  - The petition's identity is `(wing, room, closet, drawer, consumer)` — the file path
  - When `auto_pr=True` and a PR was opened, the PR number is available in the file's frontmatter `pr_url:` line and surfaces as the natural numeric handle in CLI output
- Cache `_load_log_writer` at module level:
  - Single sys.path insertion at first call (idempotent if already present)
  - Single `import honeycomb.log` 
  - Cached writer returned on subsequent calls
- Fix the `wing_bees/plan/palace-petitions/index.md` drawer order to put `migration` in the position spec 010 prescribed
- Tests:
  - New `tests/test_mcp_overlay_e2e.py` — spawns the MCP server, calls `palace_petition_submit`, immediately calls `palace_recall`, asserts overlay content returned with `source=consumer-overlay`
  - Existing `tests/test_recall_overlay.py` keeps passing
  - New test for no-flags install byte-identical behaviour (snapshot test or directory-diff)
  - New test for `_load_log_writer` single-load semantics (mock import, assert imported once across N calls)
  - Update existing tests that asserted `petition_id` field — drop those assertions
- Update inline docs:
  - `bin/honeycomb-mcp` docstring on the overlay_root resolution
  - `ADR-0002` supersession note appended: petition identity is path, not id
  - `wing_bees/plan/palace-petitions/closet.md` — drop any mention of the petition_id format
  - `wing_bees/plan/palace-petitions/migration.md` — drop the YYYYMMDD-NNN format

## Out of scope

- Any architectural change to overlay semantics — the overlay precedence rules from ADR-0002 stand; this fix is purely wiring the existing rules through the MCP layer
- The bees-side observability consumer (correlation, retro-petition emission) — separate BACKLOG'd feature
- Re-running `bees accept` after this fixup lands — operator runs that when ready
- Honey-pack support (ADR-0003, honeycomb v1.2)
- Bees-side excise — separate briefed feature, blocked on PR #4 merge
- Renaming/restructuring petition file naming convention — `<drawer>.queenfile_<consumer>.md` stays as ADR-0002 specified
- Modifying queen prompts to call `palace_petition_submit` directly instead of emitting `<<<PALACE PROPOSAL>>>` blocks (queen-prompt rewrite is its own concern, lives in bees)

## Issue references

Refs `viviane1016/honeycomb` PR #4 accept review.

## Operator amendments

<!-- Timestamped entries appended as the operator amends intent after plan approval. -->
