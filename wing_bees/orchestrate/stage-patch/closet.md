<!-- stage-patch.md: migrated from stage-patch.md.

Hall: hall_procedure
-->

Plan-less single-issue workflow: skips the plan stage and treats the issue body as the spec. The scribe produces `001-<task>.md` in one call; the queen-orchestrator drives dispatch → accept → ship unchanged. The PR opens with `Closes #N` for GitHub auto-close. Scope detection refuses "Part 1 of N", 3+ numbered tasks, or "scope: multiple files across subsystems". One human gate: PR review.
