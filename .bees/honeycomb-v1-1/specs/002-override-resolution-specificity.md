---
depends-on: [001]
output-files: [lib/honeycomb/overrides.py, tests/test_overrides_resolve.py]
scribe-model: claude-opus-4-7
---

# Spec 002 — Override resolution + specificity ranking

## Builder model

claude-sonnet-4-6

## Goal

Extend `lib/honeycomb/overrides.py` with `rank_by_specificity` and `resolve_overrides` so callers can pick a single winning override per drawer path from a candidate set, applying the deterministic specificity ladder (axes-matched > version-specificity > consumer-specificity > file mtime).

## Scope

**Edit** `lib/honeycomb/overrides.py` — add (alongside spec 001's `OverrideSpec` and `parse_override_file`):

- `@dataclass class ResolutionContext`: fields `tool: str | None`, `tool_version: str | None`, `consumer: str | None`. Each defaults to `None` (= "no scope flag supplied at install").
- `@dataclass class RankedMatch`: fields `spec: OverrideSpec`, `path: pathlib.Path`, `score: tuple[int, int, int, float]` (sort key). Higher tuple wins.
- `def rank_by_specificity(matches: list[tuple[OverrideSpec, pathlib.Path]], context: ResolutionContext) -> list[RankedMatch]`:
  - Drops any match whose `OverrideSpec` does not match `context` on every populated axis (`tool`, `tool_version`, `consumer`). An axis is "matched" if (a) the spec's value is `None` (= wildcard) or (b) the spec's value equals (for `==` ops / scalars) or contains (for `>=` ranges) the context's value. Use a simple string-prefix comparison for `>=` ranges in v1.1 (e.g. spec `tool_version: ">=v1.18"` matches context `v1.18`, `v1.18.1`, `v1.19`; does NOT match `v1.17`); document the limitation.
  - Builds a four-tuple score per surviving match: `(axes_matched_count, version_exactness, consumer_exactness, mtime_epoch)` where
    - `axes_matched_count` = number of populated context axes the spec matched explicitly (wildcard `None` in spec does NOT count as a match).
    - `version_exactness` = 2 if spec uses `==` (or a bare scalar), 1 if uses `>=`, 0 if wildcard.
    - `consumer_exactness` = 1 if spec's `consumer` is a named string, 0 if `None`.
    - `mtime_epoch` = `path.stat().st_mtime` (float).
  - Returns the surviving matches sorted by `score` descending.
- `def resolve_overrides(candidates: dict[str, list[tuple[OverrideSpec, pathlib.Path]]], context: ResolutionContext) -> tuple[dict[str, pathlib.Path], list[str]]`:
  - `candidates` keys are drawer paths (e.g. `wing_bees/plan/petitions-flow/behaviour`); values are lists of (spec, override-file-path) tuples gathered by the caller.
  - For each drawer key, run `rank_by_specificity`. If the ranked list is empty after axis filtering, omit the drawer from the result dict.
  - Pick the top-ranked match as the winner; record its `path` in the result dict.
  - If two or more matches tie on the FIRST THREE score components (axes/version/consumer) and differ only in mtime, append the drawer key to the second return value (`ambiguous: list[str]`). Do NOT raise — the mtime tiebreaker still selects a winner; the list is a lint signal for the caller.
  - Return `(winners, ambiguous)`.
- Module-level public surface: append `ResolutionContext`, `RankedMatch`, `rank_by_specificity`, `resolve_overrides` to `__all__` (create `__all__` if spec 001 did not).

**New file** `tests/test_overrides_resolve.py` — stdlib `unittest`; runnable via `python3 -m unittest discover -s tests`. Cover, with separate test methods:

1. Axis filtering: spec with `tool="bees"` is dropped when context `tool="scarab"`.
2. Wildcard match: spec with `tool=None` survives every context but scores 0 axes-matched.
3. Version-exactness tiebreaker: spec `tool_version="==v1.18"` beats spec `tool_version=">=v1.17"` when context `tool_version="v1.18"`, both otherwise equal.
4. Consumer-exactness tiebreaker: spec `consumer="scarab"` beats spec `consumer=None` when context `consumer="scarab"`, both otherwise equal.
5. Mtime tiebreaker: two identically-scored override files; use `os.utime(path, (mtime, mtime))` on the loser with an older epoch to make ranking deterministic. Assert the newer file wins.
6. Ambiguous-overlap flag: two override files tied on axes/version/consumer; assert the drawer key appears in the `ambiguous` list AND a winner is still chosen (do NOT assert which one — only that exactly one path is returned).
7. Multi-drawer resolution: build a `candidates` dict with two drawer keys; assert each gets its own winner independently.
8. Empty input: `resolve_overrides({}, ctx) == ({}, [])`.
9. All-filtered-out drawer: a drawer whose every candidate fails axis filtering is omitted from `winners` and absent from `ambiguous`.

Test fixtures should construct `OverrideSpec` instances directly (no parsing) and write zero-byte placeholder files via `tempfile.TemporaryDirectory()` so `.stat().st_mtime` is available. Use `os.utime` for every mtime assertion to avoid timing flakiness.

**Non-goals**: filesystem walking / drawer-path derivation (spec 003), semver-aware range matching beyond prefix comparison, regex consumers, overrides-of-overrides.

## Failing test

`tests/test_overrides_resolve.py::TestResolveOverrides::test_version_exactness_beats_range` — constructs two `OverrideSpec` instances, one with `tool_version="==v1.18"` and one with `tool_version=">=v1.17"`, both matching context `tool_version="v1.18"`, asserts the `==` spec wins. Fails before the builder runs because `rank_by_specificity`/`resolve_overrides` do not yet exist (`ImportError`).

## Builder prompt

You are extending `lib/honeycomb/overrides.py` (created in spec 001, which already defines `OverrideSpec` and `parse_override_file`). Add override resolution: a deterministic specificity ladder that picks one winning override file per drawer path.

**Read first**: `lib/honeycomb/overrides.py` (the existing module), `lib/honeycomb/__init__.py` (re-export pattern), the plan section "Approach" and work-breakdown item 2 in `.bees/honeycomb-v1-1/plan.md`, and ADR-0002 in `decisions/` (if present) for the override-file design rationale.

**Add to `lib/honeycomb/overrides.py`**:

1. `@dataclass class ResolutionContext` with fields `tool: str | None = None`, `tool_version: str | None = None`, `consumer: str | None = None`.
2. `@dataclass class RankedMatch` with fields `spec: OverrideSpec`, `path: pathlib.Path`, `score: tuple[int, int, int, float]`.
3. `def rank_by_specificity(matches, context) -> list[RankedMatch]`:
   - Filter: drop any (spec, path) whose populated axes conflict with `context`. An axis matches if the spec value is `None` (wildcard) OR equals the context value (scalar / `==`) OR is a `>=vX` range whose `vX` is a string prefix of the context value (treat `vX` as a string and require `context_value >= vX` lexicographically — explicitly document this is a simplification).
   - Score each survivor as `(axes_matched, version_exactness, consumer_exactness, mtime)`:
     - `axes_matched` counts populated context axes the spec matched explicitly (wildcards in spec don't count).
     - `version_exactness`: 2 if spec uses `==` or a bare scalar, 1 if `>=`, 0 if wildcard / None.
     - `consumer_exactness`: 1 if spec's `consumer` is a named string, 0 if `None`.
     - `mtime`: `path.stat().st_mtime`.
   - Return survivors sorted by score descending.
4. `def resolve_overrides(candidates, context) -> tuple[dict[str, pathlib.Path], list[str]]`:
   - Per drawer key, rank candidates; if empty after filtering, skip the drawer.
   - Winner = top-ranked match's `path`.
   - If top 2+ matches tie on the first three score components (axes/version/consumer) but differ only in mtime, append the drawer key to `ambiguous`. Still return one winner (the newest by mtime).
   - Return `(winners, ambiguous)`.
5. Append the new public names to `__all__`.

**Add `tests/test_overrides_resolve.py`** with the nine test methods listed in the Scope. Use stdlib `unittest`, `tempfile.TemporaryDirectory()` for placeholder files, and explicit `os.utime(path, (mtime, mtime))` for every mtime-sensitive assertion. The test file MUST be runnable via `python3 -m unittest discover -s tests` from the repo root.

**Constraints**:
- Use only the Python stdlib (`dataclasses`, `pathlib`, `os`, `tempfile`, `unittest`). No new third-party deps.
- Do NOT modify `lib/honeycomb/__init__.py` re-exports in this spec — spec 003 / a later doc spec handles public-surface promotion.
- Do NOT walk the filesystem in this module — `resolve_overrides` operates on a pre-built `candidates` dict. Filesystem discovery is spec 003's job.
- Document the `>=` version-matching simplification (string-prefix comparison only) in the `rank_by_specificity` docstring.
- Do NOT raise on ambiguous overlap; return the flag list instead.

**Success check**: `python3 -m unittest discover -s tests` runs to completion with all nine new test methods passing, plus all spec 001 tests still passing.

## Success check

Run from the repo root:

```
python3 -m unittest discover -s tests -v
```

Expected: every `TestResolveOverrides` method passes; spec 001's `tests/test_overrides_parse.py` still passes; no test errors or skips. Diff review confirms `lib/honeycomb/overrides.py` adds only the four new public names plus their implementations, and `tests/test_overrides_resolve.py` exercises every tiebreaker rung with explicit `os.utime` calls for mtime determinism.

## Commit message

```
feat(honeycomb): override resolution + specificity ranking (#002)

Add ResolutionContext, RankedMatch, rank_by_specificity, and
resolve_overrides to lib/honeycomb/overrides.py. Implements the
four-rung specificity ladder (axes-matched > version-exactness >
consumer-exactness > mtime) and emits an `ambiguous` flag list when
two candidates tie on the first three rungs. tests/test_overrides_resolve.py
covers each tiebreaker independently with os.utime-driven determinism.

Refs: .bees/honeycomb-v1-1/specs/002-override-resolution-specificity.md
```
