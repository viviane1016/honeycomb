<!-- retro-workflow.md: migrated from stage-retro.md.

Hall: hall_procedure
tools: [github-actions]
-->

Operator-invoked `bees retro <slug>` plus a workflow-triggered `retro-drone`. Both produce structured markdown findings: the subcommand writes to `.bees/retros/YYYY-MM-DD-<label>.md` and optionally `--md` to stdout; the drone files PRs labelled `retro-drone` with `wing_models/` petitions. Acceptance criteria 1-8 each ship as an explicit work-breakdown unit with regression test.
