<!-- cells.md: migrated from arch-cells.md.

Hall: hall_architecture
-->

A cell is a git worktree at `.bees/<slug>/cells/NNN/` checked out on `bees/<slug>/<NNN-task>`. Each cell is transient and gitignored. On successful build, the cell is scrubbed. On failure with commits worth inspecting, the cell is preserved for post-mortem. On empty failure (builder exited non-zero but left no commits), the cell is scrubbed so the next dispatch starts clean.
