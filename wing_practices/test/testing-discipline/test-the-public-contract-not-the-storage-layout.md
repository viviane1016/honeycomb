## Test the public contract, not the storage layout

Tests that read specific files by path to assert on their content are testing the storage layout, not the system's behaviour. When the storage layout changes — a room splits, a file moves, a function moves to a different module, content is refactored across files — the test breaks even though nothing the system actually promises has broken. The test was coupled to implementation, not to behaviour.

The fix: test the public contract. For content corpora (like honeycomb), the public contract is the **query → result mapping** — when a caller asks for a topic, do they get back content that satisfies their need? For code, the public contract is the function signature and behaviour, not the file path the symbol is defined at. Write the test to call the public interface and assert on what it returns; the storage layout is then free to refactor without breaking tests.

Concrete example from honeycomb. **Brittle (storage-coupled):**

```python
body = (REPO_ROOT / "honeycomb" / "wing_bees" / "scout-headers.md").read_text()
assert "/**" in body, "scout-headers.md missing TypeScript example"
```

**Robust (retrieval-coupled):**

```python
results = palace_recall("file header convention", top_k=5)
bodies = [open(REPO_ROOT / r["path"]).read() for r in results]
assert any("/**" in b for b in bodies), \
    "no recalled room contains the TypeScript header example"
```

The brittle test breaks when you factor the format spec out of `wing_bees/scout-headers` into `wing_practices/agentic-file-headers` (real refactor, hc 0.10.3). The robust test passes — the query still surfaces the right content from its new home.

Path-coupled tests are legitimate when the storage layout *is* the contract — workflow YAML structure, config file location, generated artifact name, a specific file's existence as an invariant. The disease only sets in when path-coupling sneaks into **content** tests, where the file is incidental and the content is the point.
