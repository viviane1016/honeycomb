## Debug inline-fix policy

Debug produces two classes of code changes:

1. **Inline fixes** — single-line, single-file, with a clear test. Default gating: `confirm-each`. The operator approves each fix individually before bees applies it. Operators may set their queen-file to `fix-then-notify` for repos where small fixes land without per-fix confirmation.

2. **Larger fixes** — debug **escalates to plan**: bees invokes a fresh plan stage with the debug report as briefing. The plan-approval gate then applies, so substantial code changes go through the full pipeline.

The per-repo inline-fix policy is governed by the queen-file `debug_policy` field.
