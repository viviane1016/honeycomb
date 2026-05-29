## Behaviour

Bees acquires a per-feature lock to prevent concurrent dispatches racing. For each selected spec, it creates an isolated git worktree at `.bees/<slug>/cells/NNN/` on branch `bees/<slug>/<NNN-task>`, launches a builder bee (the default model, tuned per spec), and waits for commits. When the builder completes, bees verifies the feature branch is an ancestor (ensuring fast-forward merge is safe), then folds the commits via direct ref update. The cell is gitignored and transient; on builder failure, it's preserved for post-mortem if worth inspecting, otherwise scrubbed.

Between the builder's commit and the FF-merge attempt, a scribe-verify step runs automatically, evaluating the spec text and the builder's diff through a scribe in verify mode. The scribe emits `APPROVE` or `REJECT` with a reason. `APPROVE` proceeds to the FF-merge; first `REJECT` triggers spec-revision and a second builder attempt; only a second `REJECT` (or revision failure) preserves the cell with feedback and skips the merge for that spec. Infrastructure errors proceed with FF-merge (advisory, not blocking).

Builders cannot touch anything outside their cell: Edit and Write are scoped to the cell cwd, Bash is narrowed to git operations and pytest.

**Builder model resolution.** Each builder's model is resolved per-spec with precedence: `--builder-model` flag (`cli_override`) > spec's `## Builder model` section (`spec`) > `DEFAULT_BUILDER_MODEL` (`default`). The resolution reason is recorded in `log.md` and `events.log`.

**Prior-commit detection and `--restart`.** Before launching any builder, `cmd_dispatch` checks whether `feat/<slug>` already contains commits referencing the target spec (by matching `.bees/<slug>/specs/NNN-` in commit bodies). Without `--restart`: emits a stderr message naming the prior-commit SHAs and pointing at `--restart`; the spec is skipped. This replaces the former silent-skip behaviour. With `--restart`: strips `feat/<slug>` back to its merge-base with `main` before launching, preserving commits whose subject matches `bees(plan|spec):` (operator-authored plan and spec commits). Operators should verify the strip list before using `--restart` as it permanently rewrites the feature branch history.

**Pre-flight worktree check.** Before launching wave 1, `cmd_dispatch` parses `git worktree list --porcelain` and exits with a clear error (naming the extra path and the `git worktree remove <path>` remediation) if `feat/<slug>` is checked out in any worktree other than the primary. No builders launch until the conflict is resolved.
