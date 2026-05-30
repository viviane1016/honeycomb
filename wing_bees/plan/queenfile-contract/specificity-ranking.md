## Specificity ranking

When multiple override files match a calling context `{tool, tool_version, consumer}`, the recall library (`lib/honeycomb/overrides.py`) selects the **most-specific** matching variant.

### Algorithm

```python
candidates = [behaviour.md,
              behaviour.queenfile_bees-v1.18.md,
              behaviour.queenfile_scarab.md]

# Step 1: filter to candidates whose frontmatter rules match the context.
matching = [c for c in candidates if context_matches(c.frontmatter)]

# Step 2: rank by specificity; pick the winner.
chosen = rank_by_specificity(matching)[0]
```

### Ranking order (highest to lowest priority)

1. **Axes matched.** An override targeting both `tool` and `consumer` beats one targeting only `tool`. Count of non-null targeting fields determines the score.

2. **Version specificity.** An exact pin (`==v1.18`) beats a range (`>=v1.18`). When both match, the exact pin wins.

3. **Consumer specificity.** A named consumer (e.g. `scarab`) beats `null` (any consumer).

4. **File mtime (last resort).** When two equally specific overrides exist — a curation error — the most recently modified wins. The lint tool (`tools/install.sh --lint`) flags ambiguous overlapping overrides; operators should resolve before shipping.

### Fallback

If no override matches the calling context, the canonical drawer (`behaviour.md`) is returned. Canonical with no overrides present behaves identically to honeycomb v1.0 — a bees v1.17 install with no scope flags produces byte-identical recall results.
