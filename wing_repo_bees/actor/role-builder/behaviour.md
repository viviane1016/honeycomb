## Behaviour

Each builder runs in its own cell — an isolated git worktree at `.bees/<slug>/cells/NNN/` checked out on `bees/<slug>/<NNN-task>`. The cell is transient: scrubbed on success or empty failure, preserved with commits on failure so the operator can inspect what went wrong. The builder's only job is to read the spec, implement it, and commit. Bees handles the merge onto the feature branch via fast-forward ref update; the builder never touches the user's working tree.

If the spec is unclear or impossible to implement with the allowed tools, the builder writes `.bees-builder-note.md` (the escape hatch) explaining the blocker, commits nothing, and exits. Bees reads this note and surfaces it for operator review.

Builders may run with sibling builders (other specs in the same wave) in parallel. The primary safeguard against wave-internal merge conflicts is scope discipline: edit only files declared in your spec's `## Scope` section. If two sibling builders touch overlapping files, bees detects the conflict at FF-merge time (non-ancestor state), preserves the cell, and invokes the queen to diagnose the conflict. The operator then manually resolves the conflict by tightening dependencies, rebasing, or modifying scope.
