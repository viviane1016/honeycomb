## Debug code changes
- [ ] Inline fix: `file.py:42` single-line correction (test: `test_foo`)
      Escalate to plan: larger auth refactor needed
```

### Action categories and gating

**Git-tracked file changes** — BACKLOG.md, queen-file edits, petitions written to `.bees/<slug>/petitions.md`. Operator approval: automatically applied to working tree on operator confirmation; flow through normal PR review.

**Non-git actions** — GitHub issue filing, external notifications, anything hitting shared systems with side-effects. Operator approval: **per-action** operator approval. Bees executes only the approved subset.

**Debug code changes** — two sub-classes:
- **Inline fixes** — single-line, single-file, with a clear test. Governed by `debug_policy` in the queen-file. Default: `confirm-each` (operator approves each fix before bees applies). Operators may set `fix-then-notify` for repos where small fixes land without per-fix confirmation.
- **Larger fixes** — debug **escalates to plan**: bees invokes a fresh plan stage with the debug report as briefing. The plan-approval gate then applies.
