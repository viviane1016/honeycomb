## Usage

Bees uses git as its primary artifact store and coordination mechanism. Each feature lives on `feat/<slug>`, built by builder bees running in isolated worktrees (cells). When a builder finishes, bees merges its commits to the feature branch via direct ref update — never via `git merge` or interactive rebase — so your working tree stays untouched. A PR per feature then gates the merge back to `main`. Commits reference their spec file by path, making the trail from feature to plan to code explicit.
