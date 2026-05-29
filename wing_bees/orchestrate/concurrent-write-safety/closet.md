<!-- concurrent-write-safety.md: migrated from parallelism-safety.md.

Hall: hall_pattern
tools: [git, fcntl]
languages: [python]
-->

Parallel builders share logs and the feature branch. Atomic writes under PIPE_BUF (≤4096 bytes) guarantee safety; longer data uses `fcntl.flock()`. Spec files use `os.replace()` (atomic rename). Builders run in isolated cells (separate worktrees). Parallel-scribes audit (PR #65) validated these patterns under concurrent load.
