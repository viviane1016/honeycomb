## Behaviour

Cells are created by `bees dispatch` before launching each builder and are managed by the dispatch lifecycle, not the builder itself. The filesystem layout isolates builders from each other: two builders on different specs of the same feature run concurrently in separate cells without contention. A cell's branch is a dedicated worktree branch that never touches the user's primary checkout — if the user is mid-edit on an unrelated feature, bees dispatch refuses to start (preventing cell creation on the feature branch until the user switches away).

When the builder exits successfully, `bees dispatch` fast-forward-merges the cell branch into `feat/<slug>` by direct ref update (see `arch-ff-merge`). The cell directory is then removed. If the builder fails but commits something worth preserving, the cell stays on disk for the operator to inspect — the worktree branch remains intact, and its commits are available via `git log` for reviewing what went wrong.

See ADR-0003 for the design rationale and discussion of alternatives (single shared workspace, branch-switching, containers).
