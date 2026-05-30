---
depends-on: [002]
output-files: [lib/honeycomb/recall.py, lib/honeycomb/semantic.py, tests/test_recall_overlay.py]
scribe-model: claude-opus-4-7
---

# Spec 008 — Consumer overlay support in recall

## Builder model

claude-sonnet-4-6

## Goal

Teach `palace_recall` and `palace_recall_semantic` to merge an optional consumer-side overlay tree on top of the canon honeycomb at query time, so overlay drawer files win over canon for matching drawer paths while a missing overlay preserves v1.0 behaviour exactly.

## Scope

In scope:
- Edit `lib/honeycomb/recall.py` — add an optional `overlay_root: Optional[Path] = None` keyword parameter to `palace_recall`. When set and the path exists, walk `<overlay_root>/wing_*/<room>/<closet>/` after canon discovery using the same `_discover_closets` machinery. Merge results so that an overlay closet keyed on `(wing, room, closet)` *replaces* the canon closet at the same key; overlay-only closets are appended. The merge happens before scoring so overlay content is what gets ranked and returned.
- Edit `lib/honeycomb/semantic.py` — add an optional `overlay_root: Optional[Path] = None` keyword parameter to `palace_recall_semantic`. When set and the path exists, run the existing ChromaDB query against canon, then perform a linear-scan keyword pass over overlay closets (using `_discover_closets` + the same `score_match` from `recall.py`), and merge into the result list using the same `(wing, room, closet)` key — overlay wins. The merged list is truncated to `top_k`. No separate ChromaDB collection is built for the overlay in v1.1.
- Overlay drawer filenames may be either the canonical names (e.g. `behaviour.md`) OR the override pattern (`behaviour.queenfile_<scope>.md`); for v1.1, when the overlay contains the override-pattern filename, the materialized drawer name is the canonical name (the `queenfile_<scope>` suffix is stripped to derive the merge key). Reuse `lib/honeycomb/overrides.py` helpers from spec 002 if available for stripping; otherwise do a local regex strip (`r"\.queenfile_[^.]+(?=\.md$)"`).
- New `tests/test_recall_overlay.py` exercising: (a) no env / no overlay path returns byte-identical results to v1.0; (b) overlay closet wins over canon at the same `(wing, room, closet)` key; (c) overlay-only closet surfaces; (d) overlay path passed but does not exist on disk → falls through to canon-only without error; (e) semantic recall merges overlay closets via linear-scan and overlay wins.

Non-goals:
- Wiring `overlay_root` into `bin/honeycomb-mcp` — that lives in spec 007 (petition tools) and spec 005 (log writer); the env-derivation (`$BEES_REPO_ROOT/.bees/honeycomb-overlay/`) is added by those specs, not this one.
- Building a separate ChromaDB collection for the overlay.
- Changing the existing `palace_recall` return shape, the `scope`/`tools`/`models`/`project` extension points, or trace writing behaviour.
- Re-indexing or persisting any overlay content.

## Failing test

`tests/test_recall_overlay.py::test_overlay_drawer_wins_over_canon` — builds a temp canon tree with one closet (`wing_bees/plan/sample/`) containing `closet.md` with text `canon body`, then builds a temp overlay tree at `<overlay>/wing_bees/plan/sample/closet.md` with text `overlay body`, calls `palace_recall("sample", root=canon, overlay_root=overlay, drawer=True)`, and asserts the first result's `closet` field contains `overlay body` and not `canon body`. Test fails today because `palace_recall` does not accept `overlay_root`.

## Builder prompt

You are implementing spec 008 for honeycomb v1.1: consumer-overlay support in `palace_recall` and `palace_recall_semantic`. The goal is to let consumers (e.g. bees) keep a local overlay tree under `<consumer-repo>/.bees/honeycomb-overlay/` that the recall layer transparently merges on top of canonical honeycomb content at query time. When no overlay is supplied, behaviour must be byte-identical to v1.0.

Repo-relative files you will edit:
- `lib/honeycomb/recall.py`
- `lib/honeycomb/semantic.py`

Repo-relative file you will create:
- `tests/test_recall_overlay.py`

**Implementation — `lib/honeycomb/recall.py`:**

1. Add keyword parameter `overlay_root: Optional[Path] = None` to `palace_recall`, placed alongside the other extension points (after `project`, before `slug`).
2. After the existing `closets = _discover_closets(search_root)` call, when `overlay_root` is not None and `Path(overlay_root).is_dir()`, call `_discover_closets(Path(overlay_root))` to get `overlay_closets`. If the overlay path is None or does not exist, skip the overlay merge entirely (preserves v1.0 behaviour).
3. Build a merged list keyed by `(wing, room, closet)`:
   - Start from canon closets.
   - For each overlay closet, derive a merge key by stripping any `queenfile_<scope>` suffix from the `closet` field (use regex `re.sub(r"\.queenfile_[^.]+$", "", value)` on the closet name; closet directory names typically won't carry the suffix but defensively handle both). Wing/room are taken verbatim from the overlay's directory layout.
   - If the merge key matches an existing canon closet, replace that entry with the overlay closet. If it doesn't match, append the overlay closet.
4. The rest of the function (wing/hall filtering, scoring, top-K, trace writing) operates on the merged list unchanged.
5. Update the docstring to document the new `overlay_root` parameter: "Optional consumer-side overlay tree; when set and existing, overlay drawer files win over canon at matching `(wing, room, closet)` keys. Absent or non-existent path = canon-only (v1.0 behaviour)."

**Implementation — `lib/honeycomb/semantic.py`:**

1. Add the same `overlay_root: Optional[Path] = None` keyword parameter to `palace_recall_semantic`.
2. Run the existing ChromaDB query path against canon unchanged. Collect the result list (`out`).
3. If `overlay_root` is set and exists, perform a linear scan: call `_discover_closets(Path(overlay_root))`, apply the same wing/hall filters, score each overlay closet against the query using `score_match` imported from `honeycomb.recall`, keep matches with score > 0.
4. Merge: for each overlay match, compute the merge key from `(wing, room, closet)`; if any entry in `out` shares that key, replace it; otherwise append.
5. Re-rank the merged list deterministically (overlay matches without a ChromaDB distance get appended preserving overlay score order; the simplest approach is: keep canon ordering for non-overlapping entries, place overlay-replacements in the same position as the canon entry they replaced, and append overlay-only entries at the end). Truncate to `top_k`.
6. Result shape (composite `room` field) is unchanged.
7. Document the new parameter the same way as in `recall.py`.

**Tests — `tests/test_recall_overlay.py`:**

Use stdlib `unittest`. Each test builds temp canon + overlay directories with `tempfile.TemporaryDirectory`, writes minimal closet structures (`<root>/wing_bees/plan/sample/closet.md` etc.), invokes the public API, and asserts on returned dicts.

Required test cases:
- `test_no_overlay_matches_v1_behaviour` — call `palace_recall("sample", root=canon)` with overlay omitted; assert results are identical (same length, same `closet` text) whether `overlay_root=None` or the kwarg is not passed.
- `test_overlay_drawer_wins_over_canon` — the failing test described above.
- `test_overlay_only_closet_surfaces` — canon has closet A, overlay has closet B (different wing/room/closet); calling recall with a query that matches B returns B even though it is not in canon.
- `test_overlay_path_missing_falls_through` — pass `overlay_root=Path("/tmp/definitely-does-not-exist-12345")`; recall returns canon-only results without raising.
- `test_overlay_queenfile_suffix_strips_for_merge_key` — overlay file under `wing_bees/plan/sample/closet.md` where the closet directory name carries no suffix, and a second test where the directory is named with `queenfile_<scope>` and the suffix is stripped for merge.
- `test_semantic_overlay_merge` — only runs when `chromadb` is importable (skip via `unittest.skipUnless` otherwise); builds a canon tree, indexes it via `honeycomb.semantic.index_closets`, builds an overlay with a closet sharing the same `(wing, room, closet)` key but different body, calls `palace_recall_semantic(query, overlay_root=overlay)`, asserts overlay body wins.

Run tests with `python3 -m unittest discover -s tests` and ensure they pass.

**Backwards-compat checklist:**
- `palace_recall("foo")` with no kwargs must produce the same return value as v1.0.
- `palace_recall("foo", overlay_root=None)` must produce the same return value.
- Tests must verify both forms.

**Commit message:** Use the template in the spec's Commit message section.

When done, the test file passes and a diff review shows the two source files gained the `overlay_root` parameter, the merge logic, and updated docstrings — nothing else.

## Success check

- `python3 -m unittest discover -s tests` passes, including all new cases in `tests/test_recall_overlay.py`.
- `palace_recall("…")` and `palace_recall("…", overlay_root=None)` produce identical results to the pre-change behaviour (verified by the `test_no_overlay_matches_v1_behaviour` test).
- An overlay closet at the same `(wing, room, closet)` key as a canon closet replaces the canon entry in both `palace_recall` and `palace_recall_semantic` results.
- An overlay path that doesn't exist falls through silently (no exception).
- Diff review: only `lib/honeycomb/recall.py`, `lib/honeycomb/semantic.py`, and `tests/test_recall_overlay.py` are touched. Function signatures preserve all existing parameters in their existing order; `overlay_root` is added as a keyword-only argument.

## Commit message

```
feat(honeycomb): consumer overlay support in recall (#008)

palace_recall and palace_recall_semantic now accept an optional
overlay_root keyword; when set and existing, overlay drawer files
win over canon at matching (wing, room, closet) keys. Absent or
non-existent overlay preserves v1.0 behaviour byte-for-byte.

Refs: .bees/honeycomb-v1-1/specs/008-consumer-overlay-recall.md
```
