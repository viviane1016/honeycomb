## Testing the recall surface

Tests of honeycomb content should query `palace_recall` and assert on the recalled rooms' content — they should not read specific `.md` files by path. The query is the public contract; the file layout is implementation. When rooms split, merge, or move (real refactors happen — `wing_bees/scout-headers` was factored into a generic format-spec room in `wing_practices` and a mechanism room in `wing_bees` at hc 0.10.3), query-driven tests continue to pass as long as the recall contract still holds; path-coupled tests break needlessly.

**Pattern:**

```python
results = palace_recall("file header convention", top_k=5)
bodies = [open(REPO_ROOT / r["path"]).read() for r in results]
assert any("/**" in b for b in bodies), \
    "no recalled room contains the TS/JS header example"
```

This decouples the test from the room layout. The same test passes whether the content lives in one room or three, in `wing_bees` or `wing_practices`, or moves between releases — as long as `palace_recall("file header convention")` still returns content that contains the required examples.

Path-coupled tests remain legitimate when the path *is* the contract — a specific room's existence as a structural invariant, a workflow YAML's location, a generated artifact's name. The disease only sets in when path-coupling sneaks into content tests, where the file is incidental and the content is the point. See `wing_practices/testing-discipline` § "Test the public contract, not the storage layout" for the generic doctrine.
