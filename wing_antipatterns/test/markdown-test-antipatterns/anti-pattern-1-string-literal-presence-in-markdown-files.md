## Anti-pattern 1 — string literal presence in Markdown files

### What it looks like

```python
content = (tmp_path / "CLAUDE.md").read_text()
assert "bees" in content
```

```python
assert "## Operator amendments" in briefing_text
```

### Why it misfires

The checked string is incidental to the contract. It tests that a specific word or heading
exists today, not that the document fulfils its purpose. When the content is legitimately
revised — a heading is renamed, a section is restructured, a term is updated — the test
breaks and the agent either reverts the improvement or introduces an ugly workaround to
preserve the checked string.

Worse: when an agent is in a tight loop (spec → dispatch → verify → reject → retry), a
failing string-presence test becomes a treadmill. The builder satisfies the test by
re-inserting the string; the quality of the content is irrelevant to the outcome.

### What to test instead

Test the structural contract, not the literal content:

- Does the file exist?
- Does it parse as valid Markdown?
- Does it contain the required sections (by checking section presence, not exact heading text)?
- Does it contain content that is non-empty / non-trivial?

### If you must check a literal string

Add a comment co-located with the assertion explaining the constraint:

```python
# "bees" must appear because CLAUDE_MD_STARTER is the install-time signal
# that bees skill is active; downstream tooling grepping for it is load-bearing.
assert "bees" in content
```

Without this comment, a future agent seeing a test failure has no way to distinguish
"this string matters for a specific downstream reason" from "this string was incidental
and the test is stale."
