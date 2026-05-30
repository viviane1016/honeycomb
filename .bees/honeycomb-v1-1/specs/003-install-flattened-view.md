---
depends-on: [002]
output-files: [lib/honeycomb/overrides.py, tools/install.sh, tests/test_install_resolve.py]
scribe-model: claude-opus-4-7
---

# Spec 003 — Flattened-view materializer + scope-aware install.sh

## Builder model

claude-sonnet-4-6

## Goal

Add `materialize_flattened_view` to `lib/honeycomb/overrides.py` that walks the canon tree, picks the winning drawer per `resolve_overrides`, and writes a flattened view to `target_root`; extend `tools/install.sh` with `--tool/--tool-version/--consumer` flags that drive materialization before reindexing, while leaving the no-flags path byte-identical to v1.0.

## Scope

**Edit `lib/honeycomb/overrides.py`** (additions only; existing `OverrideSpec`, `parse_override_file`, `rank_by_specificity`, `resolve_overrides` from specs 001/002 stay untouched):

- Add a `ResolutionReport` dataclass with fields:
  - `materialized: list[str]` — drawer paths (relative to `target_root`) written this run.
  - `overrides_used: dict[str, str]` — `{materialized_path: source_override_filename}` for drawers where a `queenfile_*` override won.
  - `canonical_kept: list[str]` — drawer paths where the canonical file won (no override or canonical beat all candidates).
  - `ambiguous: list[str]` — drawer paths whose resolver flagged overlapping ties; the materializer still picks the resolver's nominated winner but records the ambiguity for the install summary.
  - `removed_overrides: list[str]` — paths of `queenfile_*` files removed from `target_root` after materialization.
- Add `materialize_flattened_view(canon_root: Path, target_root: Path, context: dict) -> ResolutionReport`:
  - Walks `canon_root/wing_*/**/` recursively, collecting `.md` files at each directory level.
  - For every directory, groups files by canonical drawer name: a file named `<base>.queenfile_<scope>.md` belongs to the group keyed `<base>.md`; a plain `<base>.md` is its own canonical group anchor.
  - Builds the candidate list per group: the canonical file (if present) plus all `queenfile_*` siblings parsed via `parse_override_file`.
  - Calls `resolve_overrides(candidates, context)` (from spec 002) to pick a winner.
  - When `canon_root == target_root` and the canonical file already holds the chosen content, leaves it untouched (idempotency: no write churn).
  - When the override wins, writes the override file's body to `target_root/<rel_dir>/<base>.md` (replacing the canonical file's content if any), preserving the canonical filename. The override's frontmatter header line is stripped from the body before writing.
  - After all groups in a directory are resolved, removes every `queenfile_*.md` file from `target_root/<rel_dir>/` so the materialized view contains only canonical-named drawer files.
  - When `target_root != canon_root`, creates parent directories as needed and copies non-drawer files (`closet.md`, `index.md`, `_manifest.yaml`) verbatim from canon so the target is a self-contained view.
  - When `context` is the empty dict, `resolve_overrides` returns the canonical file unchanged and the target ends up byte-identical to canon (minus `queenfile_*` files, of which there are none in a v1.0 install).
  - Returns a populated `ResolutionReport`.

**Edit `tools/install.sh`**:

- Parse three new long flags before the existing logic: `--tool <T>`, `--tool-version <V>`, `--consumer <C>`. Each is optional. Use a portable `case` loop over `"$@"`; no `getopt`.
- When *all three* flags are absent, behaviour is identical to v1.0: clone/update, then `build_index.py`.
- When *any* of the three flags is supplied, after the git checkout and before `build_index.py`, invoke materialization:

  ```
  python3 -c "
  import sys, json
  sys.path.insert(0, '$TARGET/lib')
  from pathlib import Path
  from honeycomb.overrides import materialize_flattened_view
  ctx = {'tool': '$TOOL', 'tool_version': '$TOOL_VERSION', 'consumer': '$CONSUMER'}
  ctx = {k: v for k, v in ctx.items() if v}
  report = materialize_flattened_view(Path('$TARGET'), Path('$TARGET'), ctx)
  print(json.dumps({
      'materialized': len(report.materialized),
      'overrides_used': len(report.overrides_used),
      'ambiguous': report.ambiguous,
      'removed_overrides': len(report.removed_overrides),
  }))
  "
  ```

  Print a one-line summary (`step "materialized: N drawers, M overrides applied"`); when `ambiguous` is non-empty, print a `warn` line listing each ambiguous path.
- The materializer call exits non-zero on failure; surface that with `die "materialization failed"`.
- Document the three new flags in the usage block at the top of the script.

**New tests** `tests/test_install_resolve.py` (stdlib `unittest`, no third-party deps):

- `test_default_flags_preserves_canon`: build a tmp canon with `wing_foo/room_a/closet_x/{closet.md,drawer1.md}`, no override files; call `materialize_flattened_view(canon, target, {})` with `target` being a *separate* tmp dir; assert every byte of every file matches canon and `report.overrides_used == {}`.
- `test_override_wins_when_axes_match`: canon contains `drawer1.md` plus `drawer1.queenfile_bees-v1.18.md` whose frontmatter targets `tool=bees, tool_version=v1.18`; call with `context={'tool': 'bees', 'tool_version': 'v1.18'}`; assert the materialized `target/.../drawer1.md` byte-equals the override file's body (header stripped), the override filename is absent from target, and `report.overrides_used` records the substitution.
- `test_idempotent_in_place_materialization`: copy canon (with one override sibling) into a tmp dir, call materializer twice with `canon_root == target_root == tmp` and identical scope; capture a recursive checksum of the tree after each call (e.g., sorted SHA-256 over `(relpath, sha256(contents))` tuples) and assert byte-identical.
- `test_default_context_keeps_canonical_drawer_when_overrides_present`: canon has `drawer1.md` plus `drawer1.queenfile_other-v1.0.md`; call materializer with `context={}`; assert `target/.../drawer1.md` matches the canonical body and `report.canonical_kept` includes the drawer.
- `test_non_drawer_files_copied_verbatim`: canon contains `wing_foo/room_a/closet_x/{closet.md,index.md,drawer1.md}`; assert all three appear in target with identical bytes (the closet/index files are not "drawers" but must be carried over so the install tree stays whole).

## Failing test

File: `tests/test_install_resolve.py`
Function: `TestInstallResolve.test_override_wins_when_axes_match` — fails because `materialize_flattened_view` does not yet exist in `lib/honeycomb/overrides.py`; the test imports the symbol at module top and any test in the file will error out with `ImportError`.

## Builder prompt

You are building spec 003 of the honeycomb v1.1 rollout. Specs 001 and 002 have already shipped: `lib/honeycomb/overrides.py` already defines an `OverrideSpec` dataclass, a `parse_override_file(path) -> OverrideSpec` parser, a `rank_by_specificity(matches, context)` ranker, and a `resolve_overrides(candidates, context) -> dict` resolver. Read that module first before writing new code, then *add* (do not modify) the symbols described below.

Repo layout you will touch (paths relative to the repo root):

- `lib/honeycomb/overrides.py` — append `ResolutionReport` and `materialize_flattened_view`.
- `tools/install.sh` — add `--tool/--tool-version/--consumer` flags and the materialization step.
- `tests/test_install_resolve.py` — new file.

**`materialize_flattened_view(canon_root: Path, target_root: Path, context: dict) -> ResolutionReport`** behaviour:

1. Walk `canon_root/wing_*/**/` recursively. At each directory, list `.md` files.
2. Group files by canonical drawer name. A file `<base>.queenfile_<scope>.md` belongs to group `<base>.md`. A plain `<base>.md` is the canonical anchor of its own group. `closet.md` and `index.md` are not treated as overrideable drawers — copy them verbatim only.
3. For each drawer group, build a candidate list: the canonical file (if it exists) plus the `OverrideSpec` returned by `parse_override_file` for every `queenfile_*` sibling.
4. Call `resolve_overrides(candidates, context)` (from spec 002) to pick a winner. The resolver's return shape is `dict[drawer_path, chosen_file]`; use the chosen file for that drawer.
5. Write the winner's content to `target_root/<rel_dir>/<base>.md`:
   - When the winner is an override, strip its frontmatter header (the `<!-- ... -->` block at top) and write only the body.
   - When the winner is the canonical file, copy it verbatim.
   - When `canon_root == target_root` and the file on disk already matches the chosen content byte-for-byte, skip the write (for idempotency and to avoid touching mtimes).
6. After processing a directory, delete every `queenfile_*.md` file from `target_root/<rel_dir>/` and record their paths in `report.removed_overrides`.
7. When `canon_root != target_root`, ensure parent dirs exist via `Path.mkdir(parents=True, exist_ok=True)` and copy `closet.md`, `index.md`, and any `_manifest.yaml` files verbatim.
8. When `context == {}`, `resolve_overrides` should pick the canonical file every time (because the no-axes context cannot match any override). The resulting target tree equals canon minus the `queenfile_*` files (a no-op when canon has none — the v1.0 path).

The `ResolutionReport` dataclass:

```python
@dataclass
class ResolutionReport:
    materialized: list[str] = field(default_factory=list)
    overrides_used: dict[str, str] = field(default_factory=dict)
    canonical_kept: list[str] = field(default_factory=list)
    ambiguous: list[str] = field(default_factory=list)
    removed_overrides: list[str] = field(default_factory=list)
```

Paths in the report are `target_root`-relative POSIX strings (`wing_foo/room_a/closet_x/drawer1.md`).

**`tools/install.sh` changes**:

- Parse `--tool <T>`, `--tool-version <V>`, `--consumer <C>` into shell vars (`TOOL`, `TOOL_VERSION`, `CONSUMER`); default each to the empty string.
- The new arg-parse must run before the existing tag-resolution block. Use a `while`/`case` loop; no GNU `getopt`.
- Update the usage comment at the top to document the new flags.
- After the existing `git checkout` block and before `build_index.py`, gate materialization on `[ -n "$TOOL" ] || [ -n "$TOOL_VERSION" ] || [ -n "$CONSUMER" ]`. When the gate fires, exec the inline python snippet (see Scope above) and surface the printed JSON via `step "materialized: …"`. When the JSON contains a non-empty `ambiguous` list, emit one `warn` line per path.
- Failure of the python invocation must `die "materialization failed"`.
- The build_index call stays as-is; it now reads the materialized tree.

**Tests** in `tests/test_install_resolve.py`:

- Use stdlib `unittest` only; runnable via `python3 -m unittest discover -s tests`.
- Each test should build a tmp canon under `tempfile.TemporaryDirectory()`; reach into `wing_foo/room_a/closet_x/` paths to keep the wing-layout convention.
- Write fixture override files with a minimal frontmatter header matching the parser spec 001 established (the format documented in the existing `overrides.py`); follow whatever the parser actually accepts — read its tests in `tests/test_overrides_parse.py` first to match the convention exactly.
- The five tests are enumerated in Scope; implement them all. The "byte-identical" tests should compute `hashlib.sha256` over sorted `(relpath, contents)` tuples to make the equality check explicit and debuggable.
- Do not import `pytest`. Do not require `chromadb` or other third-party packages.

**Constraints**:

- No new dependencies. `pathlib`, `shutil`, `hashlib`, `dataclasses`, `subprocess` (in install.sh only via shell), `tempfile`, `unittest`.
- Do not modify the `OverrideSpec`/`parse_override_file`/`resolve_overrides` symbols from specs 001/002 — additions only.
- Do not touch `lib/honeycomb/recall.py`, `lib/honeycomb/semantic.py`, or `lib/honeycomb/__init__.py`; later specs handle those.
- Do not import `honeycomb.recall` or `honeycomb.semantic` from `overrides.py` — keep the dependency arrow one-way.
- Materialization writes plain UTF-8 with LF newlines, regardless of the source platform.
- Avoid `os.walk` if `Path.rglob` reads cleaner — either is fine, pick the simpler one.
- When `canon_root == target_root`, **do not** delete the canonical drawer file mid-traversal — overwrite its content in place after the winner is computed.

**Success check**: after your changes, run `python3 -m unittest discover -s tests` from the repo root; all tests in `tests/test_install_resolve.py` pass alongside the spec 001/002 suites. The no-flags `bash tools/install.sh --help`-style usage line documents the three new flags. `git diff` on `tools/install.sh` is contained to the two regions (arg parsing + materialization step + usage comment); the rest of the script is untouched.

## Success check

`python3 -m unittest discover -s tests` passes from the repo root, including all five tests in `tests/test_install_resolve.py`. Manual diff review confirms: `tools/install.sh` no-flags path is unchanged below the new arg-parse block (the existing clone/checkout/build_index lines still execute verbatim), `materialize_flattened_view` is purely additive in `overrides.py`, and `ResolutionReport` is a frozen-shape dataclass with the five fields named in Scope.

## Commit message

```
feat(overrides): flattened-view materializer + scope-aware install (#003)

Add materialize_flattened_view + ResolutionReport in lib/honeycomb/overrides.py
that walks canon, resolves each drawer through resolve_overrides, and writes a
flattened tree to target_root with queenfile_* siblings stripped. Extend
tools/install.sh with --tool / --tool-version / --consumer flags; absent flags
preserve v1.0 behaviour, any flag triggers in-place materialization before
the existing build_index step.

Refs: .bees/honeycomb-v1-1/specs/003-install-flattened-view.md
```
