## Behaviour

**Trigger semantics.**
- **Push to main (incremental):** Enumerates only files changed in that push via `git diff HEAD~1..HEAD --name-only --diff-filter=AM`, applies the shared shell filter, Haiku-batches survivors, and commits the updated headers directly to main.
- **workflow_dispatch (full-scan):** Enumerates all eligible files via `find`, applies the same shell filter, Haiku-batches all survivors, and opens a single PR labeled `scout`.

**Execution pipeline (both modes):** enumerate → filter → batch → write → finalize. The finalize step differs by mode: incremental commits directly to main; full-scan opens a PR.

**Bot-loop guard.** The workflow's first step checks whether the triggering actor is `github-actions[bot]`. If so it writes a notice and exits 0. Rationale: incremental mode commits directly to main, which would re-fire the push trigger, creating a recursive loop. The guard breaks it at the source.

**Mode-keyed authority.**
- Incremental: direct commit to main is appropriate because each changed file's header update is small, targeted, and independently verifiable.
- Full-scan: PR required because the diff spans the entire repo and needs operator review before landing.

**Multi-run race handling (full-scan only).** Before opening a new PR, scout lists open PRs labeled `scout` via `gh pr list --label scout --state open`. For each prior open scout PR found, it posts a supersede comment. Prior PRs are not auto-closed; operator agency is preserved.

**No-findings case.** If all eligible files already have current headers, scout writes a summary to `$GITHUB_STEP_SUMMARY` and exits 0 without committing or opening a PR.

**Soft-fail on PR creation.** If `gh pr create` fails (rate limit, transient error), any staged diff is captured to `$GITHUB_STEP_SUMMARY` and the workflow exits 0. The operator re-triggers via `workflow_dispatch`. The bot-loop guard ensures this re-trigger is safe.

**Timeout note.** Full-scan time scales with eligible-file count (roughly 50 batches per 500 files at ~5–15 s each). The 15-minute job timeout is the soft cap for large repos.
