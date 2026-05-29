## Guidance

**Inline fixes vs escalate-to-plan.** Debug can propose three classes of fixes:
- **Inline fixes** (single-line, single-file, with a clear test): typos in config, a missing import, a simple logic bug. Governed by per-repo `inline_fix_policy` in the queen-file. Default is `confirm-each` — operator reviews before bees applies.
- **Larger fixes** (multi-line, multi-file, or high-risk): debug escalates to plan. This invokes a fresh plan stage with the debug report as briefing, so the fixes go through the full plan → spec → dispatch ceremony, preserving the plan-approval gate for substantial work.
- **Backlog items / queen-file updates / petitions**: categorized and reviewed with other reflection-stage actions.

**Escalate-to-plan.** When debug diagnoses a problem too big for inline fixes, it proposes `escalate-to-plan` with the debug report as briefing. This kicks off a fresh plan stage. The resulting plan's PR cites the original failure context for traceability.

**Escalate-to-scout.** When diagnosis itself needs codebase reconnaissance (not just log/test reading), debug can emit `escalate-to-scout`, per ADR-0016. Scout bees then walk specific subtrees, report findings, and feed into a refreshed analysis.
