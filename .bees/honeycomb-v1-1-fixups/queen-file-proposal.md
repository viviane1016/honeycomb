# Queen file — honeycomb

## Project context

This file is per-project memory for the bees workflow. Its contents are
injected into the queen (plan), queen (review), and scribe (spec)
subprocess prompts under a `## Project context (queen file)` heading,
and take precedence over generic honeycomb guidance when the two
conflict.

## Conventions

- **Pure-stdlib `lib/honeycomb/`.** Code under `lib/honeycomb/` must not
  import non-stdlib packages at module level. `chromadb` is the sole
  third-party dependency and is imported lazily inside
  `lib/honeycomb/semantic.py` with `try/except ImportError` → `[]`
  fallback so keyword recall always works without it.
- **Manual JSON-RPC MCP server.** `bin/honeycomb-mcp` is a hand-rolled
  stdio JSON-RPC 2.0 implementation (no `mcp` SDK, no FastAPI). New MCP
  tools follow the existing `*_DESCRIPTOR` + `tools/call` handler pattern.
- **`unittest`, not `pytest`.** Test files inherit from `unittest.TestCase`
  and start with a `sys.path.insert(0, …/lib)` preamble. The runner
  command is `python3 -m pytest tests/` but tests themselves use
  `unittest` idioms.
- **MCP-wire integration tests.** When writing new tests that exercise
  `bin/honeycomb-mcp` end-to-end, reuse the subprocess + JSON-RPC framing
  pattern in `tests/test_mcp_petitions.py` (`_spawn`, `_send`, env-builder
  fixtures). Stubbing `petitions.py` via a written-into-tmpdir module
  is the established pattern for hermetic petition tests.
- **`bash` install.** `tools/install.sh` is intended for `bash install.sh`
  invocation (curl-pipe friendly). New behaviour goes inside numbered
  `# ── N. <title>` sections; numbers must be unique and monotonic.

## Architectural decisions on file in `decisions/`

- **Petition identity is the override file's path** (post-fixup of v1.1.0).
  ADR-0002 carries the supersession note. No `petition_id` field anywhere
  in the API or frontmatter. Branch names are derived deterministically
  from the override file's path; the derivation function must be shared
  between `submit` and `withdraw`.
- **Overlay precedence (ADR-0002)** is the load-bearing motivation for
  the `_overlay_root()` helper in `bin/honeycomb-mcp`. All four MCP tool
  dispatches (`palace_recall`, `palace_recall_semantic`,
  `palace_petition_submit`, `palace_petition_list`) must use the same
  resolution rule: `$BEES_REPO_ROOT/.bees/honeycomb-overlay/` when
  `BEES_REPO_ROOT` is set and the directory exists, else `None`. Any
  new MCP tool added in the future must thread `overlay_root` from the
  same helper.

## Release-state-aware docs editing

- When the docs-update spec touches `VERSION` / `CHANGELOG.md`, the
  scribe checks `git tag --list 'v1.1.*'` (or similar) against
  `origin/main` to decide whether to amend an unshipped version's entry
  or add a new patch-level entry. Operator does not gate this — the
  spec body encodes the conditional and the scribe applies it.

## Model-selection notes

- Cross-file API-shape refactors (dataclass field removal touching
  library + MCP descriptors + tests) are Opus-tier under the
  "cross-file refactor" heuristic.
- Single-file install.sh changes with one new integration test are
  Sonnet-tier — bash gating logic with multiple cases has enough
  branching to warrant Sonnet over Haiku.
- Pure docs-update units covering ≥3 cross-referenced rooms benefit
  from Sonnet scribe-only (not Haiku) for cross-file consistency.
