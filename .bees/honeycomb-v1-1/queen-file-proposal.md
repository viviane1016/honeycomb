# Queen file — honeycomb

## Project context

Honeycomb is a standalone knowledge palace + MCP server. Independent of any consumer tool (bees, beetle-tool-suite, future agentic tools).

### Layout conventions

- **Library code.** `lib/honeycomb/<module>.py` — one public API per module, re-exported via `lib/honeycomb/__init__.py`. New modules follow this pattern (`overrides.py`, `petitions.py`, `log.py`, `manifest.py` in v1.1).
- **MCP server.** Single-file stdio JSON-RPC at `bin/honeycomb-mcp`. Extend by adding tool descriptors to the module-level descriptor list and dispatching in `_handle_tools_call`.
- **Install path.** `tools/install.sh` is the operator entry point; `tools/build_index.py` builds the ChromaDB cache from on-disk content. Both must remain idempotent. `tools/migrate_*.py` are historical migrations from v0.x — do not touch.
- **Tests.** Top-level `tests/` directory; one `test_<module>.py` per public module. No pytest config — run with `python3 -m unittest discover -s tests`. (If a future spec needs pytest features, the spec lands `pytest.ini` alongside the first pytest test.)
- **Content layout.** `wing_<area>/<room>/<closet>/closet.md` (≤500 char summary) + `index.md` (TOC) + drawer `.md` files carrying verbatim canonical sections. Frontmatter is an HTML comment: `<!-- <filename>: <provenance>.\n\nHall: hall_<x>\ntools: [...]\nlanguages: [...]\n-->`.
- **Per-wing manifest.** `wing_<area>/_manifest.yaml` declares `scope`, `version`, `mandatory_drawers`, `canonical_rooms`. Bump per-wing `version` on additive change; top-level `VERSION` aggregates.
- **VERSION file.** Plain semver (`1.0.1`, `1.1.0`), no `v` prefix.

### v1.1 surface (this feature)

- **Drawer overrides.** Filename pattern `<drawer>.queenfile_<scope>.md` next to canonical `<drawer>.md`. Frontmatter authoritative for targeting (`target`, `tool`, `tool_version`, `consumer`, `rationale`). Resolved at install time by `lib/honeycomb/overrides.py`.
- **Scope-aware install.** `tools/install.sh --tool <T> --tool-version <V> --consumer <C>` materializes a flattened view; absent flags = canonical-only (v1.0 behaviour).
- **Consumer overlay.** `$BEES_REPO_ROOT/.bees/honeycomb-overlay/` for in-flight petitions; recall walks canon + overlay (overlay wins per drawer path).
- **Observability.** Every MCP tool call writes one JSONL record (schema_version v1, sync flush, `fcntl.flock`-guarded) to `$BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl`. Actor identity from `BEES_ACTOR`/`BEES_STAGE`/`BEES_MODEL` env; missing = `"unknown"`.
- **Petition MCP tools.** `palace_petition_submit/list/withdraw` operate over override files. Submit assumes `gh` CLI is installed and authenticated.

### Model-selection notes

- Single-module Python work (parser, helper, log writer, manifest generator) → `claude-sonnet-4-6` builder.
- Content closets, README/CHANGELOG/manifest bumps → `scribe-only:claude-sonnet-4-6` (Haiku struggles with cross-file doc synthesis even in mechanical bumps).
- No work in this v1.1 surface justifies Opus by the rubric heuristics. Reserve Opus for future cross-file refactors (e.g. bees-excise wave) or genuinely security-relevant code (crypto, auth, secret handling).

### Recurring patterns

- Honeycomb has zero runtime dependencies for keyword recall (stdlib only). `chromadb` is optional and gracefully absent. Preserve this: new modules MUST work without `chromadb` installed.
- Subprocess invocations (`git`, `gh`) — mock `subprocess.run` in tests; assert argv shape, not stdin/stdout details. Production code should raise typed errors (`PetitionError`) when the binary is missing.
- Side-effects (trace writing, log writing) use `fcntl.flock` for multi-process safety. Match this in new writers.
- Backwards-compat is a hard requirement for honeycomb v1.x. A v1.0 consumer must keep working unchanged against v1.1. Default-flags paths in v1.1 reproduce v1.0 behaviour byte-for-byte.
