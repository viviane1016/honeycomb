---
depends-on: []
output-files: [bin/honeycomb-mcp, lib/honeycomb/recall.py, lib/honeycomb/semantic.py, tests/test_recall_overlay.py, tests/test_mcp_overlay_e2e.py, tests/test_log_writer_cache.py]
scribe-model: claude-opus-4-7
---

# Spec 001 — MCP overlay_root plumbing, `source` field on recall results, log-writer module-level cache

## Builder model

claude-sonnet-4-6

## Goal

Thread `overlay_root` through the recall and semantic dispatches in `bin/honeycomb-mcp`, tag every recall result with a `source` field (`"canon"` or `"consumer-overlay"`), and cache the log-writer import at module level so `sys.path` no longer accumulates per call.

## Scope

**Touched files**

- `bin/honeycomb-mcp` — rename `_overlay_root_for_petitions()` to `_overlay_root()` and call it from all four tool paths (`palace_recall`, `palace_recall_semantic`, `palace_petition_submit`, `palace_petition_list`); pass `overlay_root=` into the recall + semantic dispatches; replace per-call `_load_log_writer()` with a module-level cache (single `sys.path.insert` guarded by `if path not in sys.path:`, single `honeycomb.log` import); extend the module docstring to document overlay resolution and the cached writer.
- `lib/honeycomb/recall.py` — define module-level constants `SOURCE_CANON = "canon"` and `SOURCE_OVERLAY = "consumer-overlay"`; tag every overlay-merged closet dict with an internal marker (e.g. `_source = SOURCE_OVERLAY`) inside the overlay merge block in `palace_recall`; in the result-building loop set `entry["source"] = c.get("_source", SOURCE_CANON)`.
- `lib/honeycomb/semantic.py` — import `SOURCE_CANON` / `SOURCE_OVERLAY` from `honeycomb.recall`; set `"source": SOURCE_CANON` on every entry built from the chroma query result; in the overlay-merge branch set `"source": SOURCE_OVERLAY` on every replacement and overlay-only entry.
- `tests/test_recall_overlay.py` — add assertions: canon-only result carries `source == SOURCE_CANON`; overlay-replaced result carries `source == SOURCE_OVERLAY`; overlay-only result carries `source == SOURCE_OVERLAY`; queenfile-suffix-stripped overlay carries `source == SOURCE_OVERLAY`. Existing tests must continue to pass unchanged.
- `tests/test_mcp_overlay_e2e.py` — NEW. Spawn the MCP server via `subprocess.Popen` (reuse the `_spawn`/`_send` shape from `tests/test_mcp_petitions.py`); submit a petition through the wire using the real `lib/honeycomb/petitions.py` (not a stub); recall the same target through the wire; assert the recall result carries `source == "consumer-overlay"` and the overlay body content. See **Builder prompt** for the gh-shim + git-init recipe needed to make `petitions.submit` run unattended.
- `tests/test_log_writer_cache.py` — NEW. Load `bin/honeycomb-mcp` as a module via `importlib.util`, call `_load_log_writer()` five times, assert all returns are identity-equal and that `sys.path.count(<lib-path>)` does not grow by more than one across the calls.

**Non-goals**

- Do not modify `palace_petition_submit` / `palace_petition_list` / `palace_petition_withdraw` semantics beyond renaming the overlay-root helper. The `petition_id` field stays in this spec — spec 003 removes it.
- Do not change install.sh — spec 002 owns that.
- Do not edit any drawer markdown or ADR — spec 004 owns that.
- Do not introduce a new public parameter to `palace_recall` / `palace_recall_semantic`; `overlay_root=` already exists.
- Do not change the trace-writing or observability-log record shape; only the import path is being cached.

## Failing test

`tests/test_mcp_overlay_e2e.py::TestMCPOverlayE2E::test_petition_submitted_through_mcp_recallable_with_overlay_source`

Spawns the MCP server, dispatches `palace_petition_submit` for a known target against a tmpdir canon with a gh-shim on PATH, then dispatches `palace_recall` for the same target. Asserts the top-1 result carries `source == "consumer-overlay"` and that the overlay body text appears in the entry. With the bug present (no `overlay_root` plumbed in `_handle_tools_call`), the recall returns canon-only content and the assertion fails. After the fix, both assertions pass.

(Secondary fail-then-pass: `tests/test_log_writer_cache.py::TestLogWriterCache::test_load_log_writer_caches_writer_and_does_not_accumulate_sys_path` fails before the cache is added because the writer object is freshly imported each call and `sys.path` grows by one entry per call.)

## Builder prompt

You are implementing the MCP-side overlay-precedence fix for honeycomb v1.1. Three coupled changes ship together in this cell.

### Change 1 — Generalise `_overlay_root_for_petitions()` to `_overlay_root()` and use it everywhere

In `bin/honeycomb-mcp`:

1. Rename the existing helper `_overlay_root_for_petitions()` to `_overlay_root()`. Keep the same body (read `BEES_REPO_ROOT`, return `Path(raw) / ".bees" / "honeycomb-overlay"` or `None`). Add an `if not result.is_dir(): return None` check so callers receive `None` when the directory does not exist — this matches the resolution rule documented in the briefing and avoids passing a non-existent path down into recall.
2. Replace the two existing call sites that referenced `_overlay_root_for_petitions()` (inside the `palace_petition_submit` and `palace_petition_list` handlers) with the new name.
3. Inside `_handle_tools_call`, compute `overlay_root = _overlay_root()` once at the top of the function (alongside `root`, `slug`, `repo_root`).
4. In the `palace_recall` handler, add `overlay_root=overlay_root` to the kwargs passed into `palace_recall(...)`.
5. In the `palace_recall_semantic` handler, add `overlay_root=overlay_root` to the kwargs passed into `fn(...)`.

### Change 2 — `source` field on every recall result

In `lib/honeycomb/recall.py`:

1. Add at module top, near the existing `_FRONTMATTER_RE`:
   ```python
   SOURCE_CANON = "canon"
   SOURCE_OVERLAY = "consumer-overlay"
   ```
2. Inside `palace_recall`, in the overlay merge block (the `if overlay_root is not None and Path(overlay_root).is_dir():` branch), after the `oc = dict(oc, closet=closet_key)` line, set `oc["_source"] = SOURCE_OVERLAY`. For the append-when-not-in-canon-index branch, also set `oc["_source"] = SOURCE_OVERLAY` before appending. (Closets coming from `_discover_closets(search_root)` carry no `_source` key and default to canon.)
3. In the result-building loop, add `"source": c.get("_source", SOURCE_CANON)` as a new key on `entry`. Place it after `"closet"` for stable diff readability.

In `lib/honeycomb/semantic.py`:

1. At the top of the file, add the constants to the existing `from honeycomb.recall import ...` line: `from honeycomb.recall import _discover_closets, _default_root, _read_drawer_text, score_match, SOURCE_CANON, SOURCE_OVERLAY`.
2. In the canon-result-build loop (where `out.append({...})` happens after the chroma query), add `"source": SOURCE_CANON` to each appended dict.
3. In the overlay-merge branch, the `overlay_entry = {...}` dict already includes `wing`, `room`, `hall`, `path`, `closet`. Add `"source": SOURCE_OVERLAY` to it.

### Change 3 — Cache `_load_log_writer` at module level

In `bin/honeycomb-mcp`:

1. Replace the body of `_load_log_writer` with a cached version. Use a module-level sentinel pattern, for example:
   ```python
   _LOG_WRITER_CACHED = False
   _LOG_WRITER = None

   def _load_log_writer():
       """Lazy + cached import — returns write_call_record or None."""
       global _LOG_WRITER_CACHED, _LOG_WRITER
       if _LOG_WRITER_CACHED:
           return _LOG_WRITER
       lib_path = str(_repo_root() / "lib")
       if lib_path not in sys.path:
           sys.path.insert(0, lib_path)
       try:
           from honeycomb.log import write_call_record  # type: ignore  # noqa: WPS433
           _LOG_WRITER = write_call_record
       except Exception:  # noqa: BLE001
           _LOG_WRITER = None
       _LOG_WRITER_CACHED = True
       return _LOG_WRITER
   ```
2. Do **not** apply the same caching pattern to `_load_palace_recall`, `_load_palace_recall_semantic`, or `_load_petitions` in this spec — keep their bodies as-is. The briefing scopes the cache to the log writer (the only helper called once per tool dispatch in the hot path).
3. Apply the same `if lib_path not in sys.path:` guard pattern to the three other loaders (one-line additions). This is a hygiene fix that prevents test runs from accumulating duplicate `sys.path` entries across many MCP-spawn calls in the same Python process; do not introduce caches for them.

### Change 4 — Docstring refresh

Extend the `bin/honeycomb-mcp` module-level docstring with two short paragraphs:

- Under the existing "Configuration:" block, append a line describing overlay resolution: `BEES_REPO_ROOT/.bees/honeycomb-overlay/` is treated as a consumer overlay tree when the directory exists; overlay drawer files win over canon at matching `(wing, room, closet)` keys. Used identically by `palace_recall`, `palace_recall_semantic`, `palace_petition_submit`, and `palace_petition_list`.
- Add a one-line note that the `honeycomb.log` writer is loaded once per process via a module-level cache; subsequent MCP tool calls reuse the cached writer.

### Tests

#### Update `tests/test_recall_overlay.py`

Add a `source` assertion to each of the existing canon/overlay test methods. Concretely:

- `TestNoOverlay::test_no_overlay_returns_canon_text` — also assert every returned entry has `source == "canon"`.
- `TestOverlayWins::test_overlay_drawer_wins_over_canon` — also assert the first entry has `source == "consumer-overlay"`.
- `TestOverlayOnlyCloset::test_overlay_only_closet_surfaces` — also assert the overlay-only entry has `source == "consumer-overlay"`.
- `TestQueenfileSuffixStrip::test_queenfile_suffix_strips_for_merge_key` — also assert the merged entry has `source == "consumer-overlay"`.
- `TestSemanticOverlayMerge::test_semantic_overlay_merge` (chroma-skip-conditional) — also assert the overlay-derived entry has `source == "consumer-overlay"`.

Import the constants from `honeycomb.recall` at the top of the test file and use the named constants in the assertions (not raw strings), so a future rename keeps the tests honest:

```python
from honeycomb.recall import SOURCE_CANON, SOURCE_OVERLAY
```

#### New `tests/test_log_writer_cache.py`

```python
"""Tests for _load_log_writer module-level cache in bin/honeycomb-mcp."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent


def _load_mcp_module():
    spec = importlib.util.spec_from_file_location(
        "honeycomb_mcp_under_test", _REPO / "bin" / "honeycomb-mcp"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestLogWriterCache(unittest.TestCase):

    def test_load_log_writer_caches_writer_and_does_not_accumulate_sys_path(self):
        mod = _load_mcp_module()
        lib_path = str(mod._repo_root() / "lib")
        baseline = sys.path.count(lib_path)
        writers = [mod._load_log_writer() for _ in range(5)]
        after = sys.path.count(lib_path)
        # Identity-equal — proves the writer is cached, not re-imported each call.
        self.assertTrue(all(w is writers[0] for w in writers),
                        "expected identity-equal writer across calls")
        # sys.path grew by at most one (the first call's insertion if it was absent).
        self.assertLessEqual(after - baseline, 1,
                             f"sys.path accumulated: baseline={baseline} after={after}")


if __name__ == "__main__":
    unittest.main()
```

#### New `tests/test_mcp_overlay_e2e.py`

This test spawns the MCP server, submits a petition (real `petitions.py`, not a stub), and then recalls the same target through the wire. To make `petitions.submit` run without a live GitHub, install a `gh` shim on PATH and seed the canon as a git repo with a canonical drawer.

Reuse the `_spawn`/`_send` shape from `tests/test_mcp_petitions.py`. Key recipe steps:

1. Create a tmpdir hierarchy:
   - `hc/` — canon repo. Inside: `git init`, write a wing/room/closet drawer at `hc/wing_test/sample-room/sample-closet/overlay-target.md` (body: "canon body for overlay-target"), also write `hc/wing_test/sample-room/sample-closet/closet.md` with a minimal frontmatter (Hall: hall_pattern) and a short summary. Add `git add .` + `git commit -m "init"`.
   - `bees/` — bees repo root. `.bees/honeycomb-overlay/` need not pre-exist; petitions.submit creates the per-file overlay dir.
   - `shims/` — directory holding the `gh` executable shim. Contents:
     ```sh
     #!/bin/sh
     echo "https://example.test/pulls/1"
     exit 0
     ```
     `chmod +x shims/gh`.

2. Build the spawn env: start from `os.environ`, then override `HONEYCOMB_ROOT=hc`, `BEES_REPO_ROOT=bees`, `BEES_FEATURE_SLUG=test-overlay-e2e`, `BEES_ACTOR=scribe`, `BEES_STAGE=spec`, `BEES_MODEL=claude-sonnet-4-6`, `PATH=str(shims) + os.pathsep + os.environ["PATH"]`, and set `GIT_AUTHOR_NAME=test`, `GIT_AUTHOR_EMAIL=test@example.invalid`, `GIT_COMMITTER_NAME=test`, `GIT_COMMITTER_EMAIL=test@example.invalid` so the petition commit succeeds without a global git config.

3. Spawn the MCP server. Send `initialize`, then `tools/call palace_petition_submit` with arguments:
   ```json
   {
     "target": "overlay-target",
     "content": "overlay body content from petition",
     "rationale": "test rationale",
     "context": {"tool": "claude-code", "tool_version": "1.0", "consumer": "scribe"}
   }
   ```
   Assert no error in the response.

4. **Re-spawn** the MCP server for the recall call (the existing `_send` helper closes stdin after one batch, terminating the process — that is fine; the overlay file is on disk by now, written by the prior submit). Send `initialize`, then `tools/call palace_recall` with `{"query": "overlay-target", "top_k": 3}`. Parse the result text as JSON; find the entry whose `path` ends in `overlay-target.queenfile_claude-code-1.0_scribe.md` (or, more robustly: find any entry whose `wing == "wing_test"` and `room` ends in `sample-closet`). Assert that entry's `source == "consumer-overlay"`. Assert the joined drawer text (set `drawer=True` in the recall call to surface drawer bodies, then check the `drawer` field) contains `"overlay body content from petition"`.

5. Tear down the tmpdirs in `tearDown`.

Skip the test gracefully if `git` is not available (`shutil.which("git") is None`) — but `git` is a test-environment baseline; do not skip on `gh` (the shim provides it).

### Output expectations

Run `python3 -m pytest tests/test_recall_overlay.py tests/test_mcp_overlay_e2e.py tests/test_log_writer_cache.py tests/test_mcp_petitions.py tests/test_petitions.py` — all pass. Run the full suite `python3 -m pytest tests/` — no regressions.

Constraints:
- Repo-relative paths only in any commit / test fixture content.
- Do not introduce new dependencies beyond what is already imported elsewhere in `lib/honeycomb/`.
- Do not change function signatures of `palace_recall` or `palace_recall_semantic`; `overlay_root=` already exists.
- Do not modify trace-writing behaviour or the JSONL observability record shape.
- The `_overlay_root()` helper must return `None` (not a non-existent `Path`) when `BEES_REPO_ROOT` is unset or the `.bees/honeycomb-overlay/` directory does not exist; this contract is what `palace_recall`'s existing `if overlay_root is not None and Path(overlay_root).is_dir():` already handles.

## Success check

- `python3 -m pytest tests/test_recall_overlay.py tests/test_mcp_overlay_e2e.py tests/test_log_writer_cache.py` all pass.
- `python3 -m pytest tests/` overall — no regressions.
- `grep -n "_overlay_root_for_petitions" bin/honeycomb-mcp` returns nothing (helper renamed).
- `grep -n "overlay_root=" bin/honeycomb-mcp` shows the kwarg appearing in both the recall and semantic dispatches as well as the two petition dispatches (four matches total).
- `grep -n "source.*canon\|SOURCE_CANON" lib/honeycomb/recall.py lib/honeycomb/semantic.py` confirms both files use the constants.
- Diff review: `_load_log_writer` body uses module-level globals and a `if lib_path not in sys.path:` guard.

## Commit message

```
fix(mcp): plumb overlay_root through recall + semantic dispatches; tag results with source; cache log writer (#001)

Three coupled MCP-side tightening fixes:

* Generalise _overlay_root_for_petitions() → _overlay_root() and use
  it from all four tool paths (palace_recall, palace_recall_semantic,
  palace_petition_submit, palace_petition_list). The recall dispatches
  now actually pass overlay_root= down so end-to-end overlay
  precedence works through the MCP wire — the load-bearing motivation
  of ADR-0002 was silently broken when accessed via MCP.
* Add a `source` field ("canon" | "consumer-overlay") to every recall
  result entry in lib/honeycomb/recall.py and lib/honeycomb/semantic.py
  so callers can distinguish canon-sourced closets from overlay-merged
  ones. Constants SOURCE_CANON / SOURCE_OVERLAY are defined in recall
  and re-imported by semantic so the spelling is single-sourced.
* Cache the honeycomb.log writer at module level — single sys.path
  insertion (guarded), single import, cached writer returned on
  subsequent calls. Apply the same path-insert guard to the other
  three loaders so test processes that spawn the MCP repeatedly do
  not accumulate duplicate sys.path entries.

New tests: tests/test_mcp_overlay_e2e.py exercises submit-then-recall
through the MCP wire and asserts source="consumer-overlay";
tests/test_log_writer_cache.py asserts identity-equal writer across N
calls and bounded sys.path growth.

Refs: .bees/honeycomb-v1-1-fixups/specs/001-mcp-overlay-source-and-log-cache.md
```
