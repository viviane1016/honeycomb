## Behaviour

Bootstrap on first `bees plan` in a repo: bees copies `templates/queen.md` into `.bees/queen.md` and commits it to `feat/<slug>` alongside `plan.md`. The operator's working tree and current branch are never disturbed.

At plan and spec stages, the queen file is always injected into the queen's and scribe's context under the heading `## Project context (queen file)`. Content is capped at 16 KiB; anything beyond is replaced with `[...truncated...]`. If the file contains a secret-pattern hit, injection is skipped with a warning. If the file is absent, injection is silently skipped.

The queen may optionally emit a `<<<QUEEN FILE UPDATE>>>...<<<END>>>` block in her plan output. Bees extracts this block and writes it to `.bees/<slug>/queen-file-proposal.md`. No auto-apply occurs; the operator reviews and manually merges the proposal into `.bees/queen.md` at PR time.

Builder cells do **not** receive the queen file. It is planner- and scribe-only context.

Retro/debug write-back (the queen amending `.bees/queen.md` directly) and honeycomb-version pre-flight petition review are deferred to the **retro-v1** milestone.
