## Wave-internal conflicts

When specs in the same wave both touch the same file, merge conflicts emerge. Here's what happens:

1. **Parallel builders in wave N.** Two builders start on specs NNN and MMM, both in the same wave. Both edit `src/core.py`.
2. **First builder succeeds.** Builder NNN commits its changes to `bees/<slug>/NNN-task`. Dispatcher attempts FF-merge: the cell branch is an ancestor of `feat/<slug>` (currently at some earlier commit), so the merge succeeds. `feat/<slug>` now points to `bees/<slug>/NNN-task`.
3. **Second builder fails to merge.** Builder MMM commits its changes to `bees/<slug>/MMM-task`. Dispatcher attempts FF-merge: but `feat/<slug>` has advanced to `bees/<slug>/NNN-task` (via the first merge), and `bees/<slug>/MMM-task` is not an ancestor of that tip. The merge check fails. `ff_merge()` returns `False`.
4. **Cell preservation and diagnosis.** The dispatcher invokes `_fail_dispatch` (the same codepath as timeout/non-zero-exit failures), which preserves the cell and branch. Then it invokes `_queen_diagnose_conflict` with the failed builder's diff, the commits that landed on `feat/<slug>` since the builder started, and the spec body.
5. **Queen diagnosis.** The queen analyzes the overlap and produces a plain-text diagnosis: likely cause, expected conflict files, and suggested resolution. Example: "Both specs NNN and MMM edit `src/core.py`. Expected conflict: the two sets of changes overlap. Options: (a) tighten spec MMM's `depends-on:` to include NNN, so they dispatch in sequence; (b) rebase the cell branch on top of NNN's commits and manually merge the conflict in the cell; (c) modify one spec's `## Scope` so the two specs no longer touch the same file." The diagnosis is written to `.bees/<slug>/cells/NNN/.queen-diagnosis.md`, appended to `.bees/<slug>/log.md`, and printed to stderr for the operator to see.
6. **Manual resolution.** The operator chooses one of the three options above and re-dispatches or modifies the spec. Bees does not auto-rebase or auto-merge conflicts in v1.

### Failure-mode taxonomy

Not every FF-merge failure is a content conflict. Bees classifies `ff_merge` failures by inspecting captured stderr before deciding whether to invoke `_queen_diagnose_conflict`:

| `outcome` | `fail_reason` | Root cause | Queen diagnoses? |
|---|---|---|---|
| `"conflict"` | `"non-ancestor"` | Content conflict: two specs edited the same file; the second builder's branch is not an ancestor of the merged tip | Yes |
| `"blocked"` | `"feat-branch-checked-out-elsewhere"` | `feat/<slug>` is checked out in another worktree; `git branch -f` refuses to update it | **No** |
| `"failure"` | `"<exception type>"` | Infrastructure error (lock contention, permission denied, I/O error) | No |

For `"blocked"` outcomes, bees emits a clear stderr message naming the extra worktree path and the `git worktree remove <path>` remediation. `_queen_diagnose_conflict` is skipped entirely — there is no content conflict to diagnose, and invoking Opus would produce misleading output. Resolve by removing the extra worktree and re-dispatching.

### Detached-HEAD plan amendment

`bees plan-amend <slug>` provides a safe way to edit `plan.md` mid-flight without blocking dispatch. It creates a temp worktree via `git worktree add --detach <path> feat/<slug>` (detached HEAD — the feature branch is never checked out as a tracking branch), opens `$EDITOR` or accepts `--file <path>` for non-interactive input, commits the amended `plan.md` to `feat/<slug>` by ref update, and tears down the worktree in try/finally. Because the worktree is detached, no worktree holds `feat/<slug>` as a checked-out branch, so subsequent FF-merges proceed unblocked.
