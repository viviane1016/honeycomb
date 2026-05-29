## Behaviour

**PIPE_BUF guarantee.** On most POSIX systems, a single `write()` call of ≤4096 bytes to a file opened in append mode is atomic — no interleaving of data from concurrent writers. Use this for small events (e.g. a single line to `events.log`). If your write exceeds 4096 bytes, use a lock instead of relying on PIPE_BUF.

**File locking with fcntl.** `events.log`, `log.md`, and `honeycomb-trace.md` are appended by both the dispatcher and builders within a wave. Lock these files with `fcntl.flock(fd, fcntl.LOCK_EX)` before appending to ensure no interleaving:

```python
import fcntl
with open("events.log", "a") as f:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    try:
        f.write(json_line)
    finally:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

The lock is per-file and advisory (honoured by cooperating processes). It blocks until the lock is available, serializing writes across concurrent builders.

**Atomic file write.** Spec files (`.bees/<slug>/specs/NNN-<task>.md`) are written via a tempfile-and-rename pattern:

```python
import os
with open(tmp_path, "w") as f:
    f.write(spec_body)
os.replace(tmp_path, final_path)  # atomic on POSIX
```

`os.replace()` is atomic: either the temp file is renamed to the final path, or it isn't. No partial writes visible to concurrent readers. The tempfile lives in the same directory as the final file to ensure `os.replace()` is a same-filesystem operation (atomic; cross-filesystem renames are not atomic).

**CWD isolation.** Each builder runs in its own cell at `.bees/<slug>/cells/NNN/`. The cell's git worktree is separate from other cells and the user's primary worktree. Builders' file edits are confined to their cwd; they cannot interfere with sibling builders or the user's tree. This is the primary safeguard against wave-internal merge conflicts: if two builders both edit the same file, bees detects it at FF-merge time (non-ancestor state), not during a concurrent write.

**Concurrency testing.** The parallel-scribes audit (PR #65) validated these patterns by dispatching 32 specs concurrently with `--parallel 32` and checking for data corruption, lost writes, or interleaved JSONL records. Results: PIPE_BUF-sized appends and fcntl-protected longer writes passed. Tests: use `ThreadPoolExecutor` with a concurrent workload and assert that each thread wrote its expected data with no corruption or loss.
