<!-- queen-file.md: migrated from arch-queen-file.md.

Hall: hall_architecture
-->

Per-project notebook at `.bees/queen.md`. Bootstrapped from `templates/queen.md` on first plan in a repo. Injected at plan and spec under `## Project context (queen file)` (16 KiB cap; secret-scan-and-skip on hit). The queen may emit a `<<<QUEEN FILE UPDATE>>>` block; bees writes it to `.bees/<slug>/queen-file-proposal.md` for operator review — no auto-apply. Builder cells do not receive the queen file.
