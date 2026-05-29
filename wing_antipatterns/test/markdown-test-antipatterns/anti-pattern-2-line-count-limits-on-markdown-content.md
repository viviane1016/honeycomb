## Anti-pattern 2 — line count limits on Markdown content

### What it looks like

```python
lines = (tmp_path / "BACKLOG.md").read_text().splitlines()
assert len(lines) < 500, "BACKLOG.md is too long"
```

```python
section_lines = extract_section(plan_md, "## Context")
assert len(section_lines) <= 30
```

### Why it misfires

The world grows. A BACKLOG accumulates. A plan section becomes more detailed as a feature
gets complex. A line-count limit that was a reasonable heuristic at authoring time becomes
a hard ceiling that the system can no longer grow past without breaking CI.

Agents encountering a line-count failure have no good options: truncate real content,
split sections arbitrarily, or delete older entries to make room. All three degrade the
document rather than improve it. The test is enforcing a proxy metric (file size) rather
than the underlying concern (content quality or readability).

### What to test instead

If the concern is content bloat, test for the structural symptom, not the byte count:

- Does the section contain the required subsections?
- Are required fields non-empty?
- Is the document parseable and navigable?

### If you must bound a length

Add a comment explaining what failure mode the limit guards against, what the threshold
represents, and when it should be revised:

```python
# CLAUDE.md starter must stay under 40 lines so it fits within the Claude Code
# context injection limit without truncation. If the limit fires, trim boilerplate
# rather than raising the threshold — the 40-line ceiling is a hard system constraint.
assert len(starter_lines) <= 40
```

Without this, a future agent treats the limit as arbitrary and is likely to either
raise it without investigation or contort the content to stay under it.
