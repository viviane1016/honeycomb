# Plan — Honeycomb v1.1: drawer overrides, petitions, observability

## Context

Honeycomb v1.0 shipped a four-level content structure (wing/room/closet/drawer) plus an MCP recall surface. Four open architectural concerns block bees-excise and the broader palace-tuning loop:

1. Petitions have no working home post-cutover (bees writes to `bees/honeycomb/`, which is about to be deleted).
2. Bees and honeycomb ship in lock-step for prompt/contract changes; that coupling is becoming a bottleneck as v1.18 design work fans out.
3. Consumer customization has no recall-aware shape.
4. There's no feedback loop for tuning palace content — curators can't see what works or fails.

Four ADRs cover the design. ADR-0001 (MCP-mediated petitions, single API) and ADR-0002 (drawer overrides + scoped install-time resolution) collapse into one mechanism: petitions ARE drawer overrides. ADR-0004 adds per-call observability with actor-identity propagation. ADR-0003 (honey packs) is deferred to v1.2.

v1.1 must remain a drop-in for v1.0 consumers: a bees v1.17 install without override flags returns identical results.

## Approach

**Drawer overrides as files alongside canonical drawers.** A drawer file's filename encodes scope via a `queenfile_<tag>` suffix (`behaviour.md` canonical → `behaviour.queenfile_bees-v1.18.md` override). Authoritative targeting rules live in the override file's frontmatter (`target`, `tool`, `tool_version`, `consumer`, `rationale`).

**Install-time resolution.** `tools/install.sh` gains `--tool/--tool-version/--consumer` flags. Install resolves overrides for the supplied context, materializes a flattened view (per-drawer winner replaces canonical), and builds one ChromaDB collection over the result. Default flags = canonical-only (v1.0 behaviour).

**Specificity ranking.** Axes-matched > version-specificity > consumer-specificity > mtime tiebreaker. Lint flags ambiguous overlapping overrides.

**Petitions as MCP tools.** `palace_petition_submit/list/withdraw` operate over override files. Submit writes the override file to a feature branch in canon (`$HONEYCOMB_ROOT`), runs `gh pr create`, and optionally writes a copy to a consumer-side overlay at `$BEES_REPO_ROOT/.bees/honeycomb-overlay/` for self-visibility before PR merge.

**Consumer overlay merge at query time.** `palace_recall` (and the semantic engine) walk both the canon flattened view and the overlay; overlay files take precedence for matching drawer paths. When the overlay is absent, recall walks canon only.

**Petition manifest at install.** A commit-message-convention walker classifies merged/declined/pending petitions since the previous install and prints an operator summary.

**Observability.** A new `lib/honeycomb/log.py` writes one JSONL record per MCP tool call (schema_version v1, synchronous flush) to `$BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl`, with actor identity propagated through three new env vars (`BEES_ACTOR`, `BEES_STAGE`, `BEES_MODEL`). Missing values log as `unknown`. The MCP server wires both `palace_recall` and `palace_recall_semantic` through the writer.

**Backwards compatibility.** No API removed. `palace_recall` keeps its v1.0 signature; new behaviour is keyed by env / overlay presence. The MCP tool descriptors gain three new petition tools; existing two are unchanged.

## Scope

**New modules** (`lib/honeycomb/`):
- `overrides.py` — frontmatter parser, specificity ranking, flattened-view materializer
- `petitions.py` — submit/list/withdraw helpers; subprocess wrappers around `git` and `gh`
- `log.py` — JSONL record writer with env-derived actor identity
- `manifest.py` — petition manifest generator + operator summary

**Edited modules**:
- `lib/honeycomb/recall.py` — overlay-aware keyword recall
- `lib/honeycomb/semantic.py` — overlay-aware vector recall
- `lib/honeycomb/__init__.py` — re-export new public surfaces

**Edited binaries / tools**:
- `bin/honeycomb-mcp` — wraps tool calls with log writer; registers three petition tools; reads new env vars
- `tools/install.sh` — `--tool/--tool-version/--consumer` flags; invokes resolver; calls manifest generator; prints summary

**New content** (per ADR-0001 §H7, ~9 closets):
- `wing_bees/plan/petitions-flow/`, `wing_bees/plan/queenfile-contract/`
- `wing_repo_bees/architecture/honeycomb-access/`, `wing_repo_bees/architecture/palace-recall/`
- `wing_repo_bees/actor/surveyor/`, `wing_repo_bees/actor/honeycomb-stewards/`

**Updated content**:
- `wing_bees/plan/palace-petitions/` (block→tool migration, deprecation window)
- `wing_repo_bees/actor/role-queen/` (petition-aware recall)
- `wing_repo_bees/actor/scribe-model-tiers/` (pending-petition awareness)

**Docs and release**:
- `README.md` — v1.1 install flow, env vars, override mechanism
- `CHANGELOG.md` — v1.1.0 entry
- `VERSION` → 1.1.0
- `wing_bees/_manifest.yaml` — version bump
- `decisions/INDEX.md` (new) — short index of all four ADRs
- `BACKLOG.md` (new) — shipped v1.1 items + deferred (honey packs / bees-side observability consumer / log redaction)

**Tests** (`tests/`): one `test_<module>.py` per public module; stdlib `unittest` invoked via `python3 -m unittest discover -s tests`. First spec to land tests establishes this convention; later specs follow.

**Non-goals**:
- Honey packs (ADR-0003 — v1.2)
- Per-scope ChromaDB collections (ADR-0002 §3 — collapsed to one collection over the install-time flattened view)
- Bees-side observability consumer (correlation, signal heuristics, retro-petition emission) — bees BACKLOG
- Bees-excise itself — separate bees feature, gated on v1.1 shipping
- Override depth (overrides of overrides) — single-layer only
- Redaction hook for sensitive log content — BACKLOG
- Auto-PR machinery for consumers without `gh` CLI — v1.1 assumes `gh` is installed and authenticated

## Work breakdown

1. **[claude-sonnet-4-6] Override file format + frontmatter parser.** New module `lib/honeycomb/overrides.py` exposing `OverrideSpec` dataclass and `parse_override_file(path) -> OverrideSpec`. Parses the `<!-- ... target: ... tool: ... tool_version: ... consumer: ... rationale: ... -->` header. Filename pattern is a hint only; frontmatter is authoritative. Establishes test-suite convention: add `tests/test_overrides_parse.py` runnable via `python3 -m unittest discover -s tests`. Output-files: `lib/honeycomb/overrides.py`, `tests/test_overrides_parse.py`.

2. **[claude-sonnet-4-6] Override resolution + specificity ranking.** Add `rank_by_specificity(matches, context)` and `resolve_overrides(candidates, context) -> dict[drawer_path, chosen_file]` to `lib/honeycomb/overrides.py`. Ranking order: axes-matched > version-specificity (exact `==` beats range `>=`) > consumer-specificity (named beats null) > file mtime. Tests cover each tiebreaker independently and ambiguous-overlap detection (returns flag, doesn't raise). Use explicit `os.utime` in tests to make mtime tiebreaker deterministic. depends-on: [1]. Output-files: `lib/honeycomb/overrides.py`, `tests/test_overrides_resolve.py`.

3. **[claude-sonnet-4-6] Flattened-view materializer + scope-aware install.sh.** Add `materialize_flattened_view(canon_root, target_root, context) -> ResolutionReport` to `lib/honeycomb/overrides.py` — walks `canon_root/wing_*/**/`, resolves each drawer through `resolve_overrides`, copies the winner to `target_root/wing_*/**/<drawer-name>.md` (stripping `queenfile_<scope>` from the materialized filename). `tools/install.sh` gains `--tool <T>`, `--tool-version <V>`, `--consumer <C>` flags; absent flags = canonical-only (v1.0 behaviour). When any flag is provided, install materializes the resolved view into the install root before reindexing. Idempotent: a re-run with the same scope produces a byte-identical view. Tests exercise both the default-flags path (preserves canon) and a scope-resolved path (override wins for matching drawers). depends-on: [2]. Output-files: `lib/honeycomb/overrides.py`, `tools/install.sh`, `tests/test_install_resolve.py`.

4. **[claude-sonnet-4-6] MCP log writer module.** New `lib/honeycomb/log.py` with `write_call_record(tool, request, response, duration_ms)` and `resolve_destination()` helper. Reads `BEES_REPO_ROOT`, `BEES_FEATURE_SLUG`, `BEES_ACTOR`, `BEES_STAGE`, `BEES_MODEL` from env; missing values write `"unknown"`. Per-record schema includes `schema_version: 1`, `ts` (ISO-8601 UTC), `tool`, `slug`, `actor`, `stage`, `model`, `request`, `response`, `duration_ms`. Destination: `$BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl` when slug+root set; else `$HONEYCOMB_ROOT/.calls.jsonl` (dev fallback). Synchronous `f.write(line); f.flush()`. `fcntl.flock` around the append for multi-process safety (ADR-0004 open Q3). Tests cover env-derivation, fallback path, and concurrent-write safety with a forked process. Output-files: `lib/honeycomb/log.py`, `tests/test_log.py`.

5. **[claude-sonnet-4-6] Wire log writer into MCP server.** `bin/honeycomb-mcp` records start time before each tool dispatch, computes per-result `bytes` (rendered length of closet + drawer content) and `content_sha` (sha256 hex of returned content), and calls `log.write_call_record(...)` after the response is built. Both `palace_recall` and `palace_recall_semantic` flow through the writer. Env-vars documented in the file docstring. Update tool descriptor docstrings to note the log side-effect. depends-on: [4]. Output-files: `bin/honeycomb-mcp`, `tests/test_mcp_log_integration.py`.

6. **[claude-sonnet-4-6] Petition helpers (submit/list/withdraw).** New `lib/honeycomb/petitions.py`. `submit(target, content, rationale, context, *, hc_root, overlay_root=None)` resolves the canonical drawer path from `target`, derives the override filename `<drawer>.queenfile_<scope>.md` from `context`, writes it to a fresh feature branch in `hc_root` (`git checkout -b feat/petition-<slug>`), commits with a deterministic message convention (`petition: <target> for <scope>`), runs `gh pr create --title ... --body ...`, returns `{petition_id, branch, pr_url, overlay_path|None}`. When `overlay_root` is set, also writes the override file there for immediate self-recall. `list_pending(consumer, *, hc_root, overlay_root=None)` walks `hc_root/wing_*/**/queenfile_*.md` filtered by `consumer` (or `null` matching all) and merges overlay files. `withdraw(petition_id, *, hc_root)` removes the override file from the feature branch + closes the PR. Tests mock `subprocess.run` for `git`/`gh` invocations and assert the argv shape. Missing `gh` → raises `PetitionError("gh CLI not found")`. depends-on: [1]. timeout: 2400. Output-files: `lib/honeycomb/petitions.py`, `tests/test_petitions.py`.

7. **[claude-sonnet-4-6] Register petition MCP tools.** `bin/honeycomb-mcp` adds three tool descriptors — `palace_petition_submit`, `palace_petition_list`, `palace_petition_withdraw` — with input schemas matching the helpers' kwargs (excluding `hc_root`/`overlay_root`, which the server resolves from `HONEYCOMB_ROOT` and `BEES_REPO_ROOT`). Dispatch routes each name to its helper; errors surface as JSON-RPC `error` responses. The log writer wraps petition calls too (same schema, different `tool` field). depends-on: [5, 6]. Output-files: `bin/honeycomb-mcp`, `tests/test_mcp_petitions.py`.

8. **[claude-sonnet-4-6] Consumer overlay support in recall.** `lib/honeycomb/recall.py` accepts an optional `overlay_root` parameter and, when set, walks `overlay_root/wing_*/**/` after canon discovery. Overlay drawer files (named per the `queenfile_<scope>` pattern OR plain canonical names placed under the overlay tree) win over canon for matching drawer paths. `lib/honeycomb/semantic.py` similarly accepts an overlay root and indexes overlay closets into the same in-memory result merge (linear-scan fallback; no separate ChromaDB collection for the overlay in v1.1). MCP server passes `overlay_root=$BEES_REPO_ROOT/.bees/honeycomb-overlay/` when that path exists; absent overlay = v1.0 behaviour. depends-on: [2]. Output-files: `lib/honeycomb/recall.py`, `lib/honeycomb/semantic.py`, `tests/test_recall_overlay.py`.

9. **[claude-sonnet-4-6] Petition manifest generator + operator output.** New `lib/honeycomb/manifest.py`: `generate_manifest(hc_root, previous_sha, current_sha) -> Manifest` walks `git log <prev>..<curr>` for the canon repo, classifies commits by message-prefix convention (`petition: adopted`, `petition: declined`, `petition: pending`), and produces a manifest dict `{accepted: [...], declined: [...], pending: [...]}`. `tools/install.sh` records the pre-pull SHA, performs the pull, calls the generator with `(prev, HEAD)`, writes the manifest JSON to `$HONEYCOMB_INSTALL_DIR/.petition-manifest.json`, and prints a one-line summary (`Petitions: N accepted, M declined, K pending since v<prev>`). Tests use a temp git repo with seeded commits. depends-on: [3]. Output-files: `lib/honeycomb/manifest.py`, `tools/install.sh`, `tests/test_manifest.py`.

10. **[scribe-only:claude-sonnet-4-6] New plan-room closets (3).** Add `wing_bees/plan/petitions-flow/` (new flow: MCP tool emission, scope-keyed override file lifecycle, adoption-by-PR-merge) and `wing_bees/plan/queenfile-contract/` (override file format, filename pattern, frontmatter schema, specificity ranking summary). Rewrite `wing_bees/plan/palace-petitions/` to describe the block→tool migration and the one-release backwards-compat window (legacy `<<<PALACE PROPOSAL>>>` blocks still parsed for one release post-cutover). Each closet ships `closet.md` (≤500 char summary) + `index.md` (TOC) + 1-2 drawer .md files with verbatim canonical content. timeout: 1500. Output-files: `wing_bees/plan/petitions-flow/closet.md`, `wing_bees/plan/petitions-flow/index.md`, `wing_bees/plan/petitions-flow/*.md`, `wing_bees/plan/queenfile-contract/closet.md`, `wing_bees/plan/queenfile-contract/index.md`, `wing_bees/plan/queenfile-contract/*.md`, `wing_bees/plan/palace-petitions/closet.md`, `wing_bees/plan/palace-petitions/*.md`.

11. **[scribe-only:claude-sonnet-4-6] New architecture closets (2).** Add `wing_repo_bees/architecture/honeycomb-access/` (single API surface: all reads through `palace_recall`; env contract for `BEES_ACTOR`/`STAGE`/`MODEL`; observability log shape) and `wing_repo_bees/architecture/palace-recall/` (`include_pending`/overlay semantics, scope-aware behaviour, log-record side-effect). Each ships `closet.md` + `index.md` + 1-2 drawers. Output-files: `wing_repo_bees/architecture/honeycomb-access/closet.md`, `wing_repo_bees/architecture/honeycomb-access/index.md`, `wing_repo_bees/architecture/honeycomb-access/*.md`, `wing_repo_bees/architecture/palace-recall/closet.md`, `wing_repo_bees/architecture/palace-recall/index.md`, `wing_repo_bees/architecture/palace-recall/*.md`.

12. **[scribe-only:claude-sonnet-4-6] New + updated actor closets (4).** Add `wing_repo_bees/actor/surveyor/` and `wing_repo_bees/actor/honeycomb-stewards/` (scout / surveyor / auditor trio overview). Update `wing_repo_bees/actor/role-queen/` to describe surveyor invocation and petition-aware recall. Update `wing_repo_bees/actor/scribe-model-tiers/` to describe pending-petition awareness during spec writing. Each new closet ships `closet.md` + `index.md` + 1-2 drawers; updates touch existing files in-place. timeout: 1800. Output-files: `wing_repo_bees/actor/surveyor/closet.md`, `wing_repo_bees/actor/surveyor/index.md`, `wing_repo_bees/actor/surveyor/*.md`, `wing_repo_bees/actor/honeycomb-stewards/closet.md`, `wing_repo_bees/actor/honeycomb-stewards/index.md`, `wing_repo_bees/actor/honeycomb-stewards/*.md`, `wing_repo_bees/actor/role-queen/closet.md`, `wing_repo_bees/actor/role-queen/*.md`, `wing_repo_bees/actor/scribe-model-tiers/closet.md`, `wing_repo_bees/actor/scribe-model-tiers/*.md`.

13. **[scribe-only:claude-sonnet-4-6] Docs + version bump + decisions index + backlog.** `README.md` updated with v1.1 install flow (scope flags), new env vars (`BEES_ACTOR`/`STAGE`/`MODEL`), override mechanism overview, consumer overlay location, log destination. `CHANGELOG.md` gets a v1.1.0 entry (added: overrides, scope-aware install, petition MCP tools, observability log, consumer overlay). `VERSION` bumped to `1.1.0`. `wing_bees/_manifest.yaml` `version` bumped to `1.1.0`. New `decisions/INDEX.md` listing the four ADRs with one-line summaries and current status. New `BACKLOG.md` with shipped v1.1 items and deferred items (honey packs / bees-side observability consumer / log redaction hook / per-scope ChromaDB collections / multi-tool concurrent consumer). depends-on: [3, 5, 7, 8, 9, 10, 11, 12]. Output-files: `README.md`, `CHANGELOG.md`, `VERSION`, `wing_bees/_manifest.yaml`, `decisions/INDEX.md`, `BACKLOG.md`.

## Acceptance

- `bash tools/install.sh` (no flags) against canon with no override files produces a byte-identical view to v1.0; `palace_recall` results match v1.0.
- `bash tools/install.sh --tool bees --tool-version v1.18 --consumer scarab` against canon containing `behaviour.queenfile_bees-v1.18.md` materializes the override as `behaviour.md` in the install tree; `palace_recall` returns the override content.
- `palace_petition_submit(target, content, rationale)` writes `<drawer>.queenfile_<consumer>.md` to a fresh feature branch in `$HONEYCOMB_ROOT`, opens a PR via `gh`, writes a copy to `$BEES_REPO_ROOT/.bees/honeycomb-overlay/` when that root is set, and returns `{petition_id, branch, pr_url, overlay_path}`.
- `palace_petition_list(consumer="scarab")` returns every override file matching that consumer scope across canon + overlay.
- `palace_petition_withdraw(petition_id)` removes the override file from the feature branch and closes the PR.
- Every MCP tool call appends one JSONL record to `$BEES_REPO_ROOT/.bees/<slug>/mcp-calls.jsonl` with `schema_version: 1`, actor identity, request/response details, returned bytes, and content shas. Missing actor env → `"unknown"`. Concurrent writes from two MCP subprocesses do not corrupt the log.
- `bash tools/install.sh` after a canon update prints a one-line manifest summary naming accepted/declined/pending petitions since the previous install.
- All new modules ship with unit tests; `python3 -m unittest discover -s tests` passes.
- `README.md`, `CHANGELOG.md`, `VERSION`, `wing_bees/_manifest.yaml` all reflect v1.1.0.
- `decisions/INDEX.md` exists and references all four ADRs.

## Risks / open questions

- **Mtime tiebreaker test flakiness.** Spec #2 must use explicit `os.utime` to make rank ordering deterministic. Scribe should call this out.
- **`gh` not installed / not authenticated.** v1.1 assumes `gh` is available; missing → `PetitionError` with a clear hint. Tests mock subprocess invocations; manual smoke-test required before tag.
- **Concurrent log writes.** ADR-0004 open Q3 — JSONL records may exceed `PIPE_BUF`, so atomic POSIX append is not guaranteed. Spec #4 uses `fcntl.flock` around the write; tests verify with a forked-process scenario.
- **Schema version policy.** ADR-0004 open Q1. v1 ships now; bumping is breaking. Document in `lib/honeycomb/log.py` module docstring.
- **Petition manifest commit convention.** The walker depends on canon maintainers using `petition: adopted|declined|pending` prefix in commit messages. If the convention is not followed, all such commits classify as `pending`. The scribe should call this out + the operator summary should warn when no recognised commits are found.
- **Overlay-overrides-canon precedence.** Decision: overlay always wins over canon for matching drawer paths in v1.1. If this turns out to surprise operators (their in-flight petition silently shadows a canonical update), revisit in v1.2.
- **Backwards-compat with palace_recall callers.** Existing callers (bees v1.17) pass no overlay root and no scope params; v1.1 must return identical results. Spec #8's tests must include a "no env, no overlay" path that mirrors v1.0 exactly.

## Delivery estimates

- Human: 22 hours (confidence: medium)
- Augmented: 2.5 hours (confidence: medium)
