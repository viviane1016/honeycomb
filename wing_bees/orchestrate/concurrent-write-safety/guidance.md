## Guidance

**When to use PIPE_BUF vs fcntl.** If you're appending a single small event (e.g. one JSON object ≤4096 chars), write it directly — PIPE_BUF guarantees it won't interleave. If you're appending multiple items or the item is larger, acquire `LOCK_EX` first. For critical files like `events.log`, use the lock even for small appends (defensive, no performance cost).

**Atomic rename pattern.** Always write to a temporary file and then rename:
```python
tmp = final_path + ".tmp"
write_to(tmp)
os.replace(tmp, final_path)
```
This ensures readers see either the old file or the new file, never a partially-written one. Don't write directly to the final path.

**Testing parallel dispatch locally.** Use `--parallel N` with N > 1 to exercise the concurrent-write paths. Run your test suite multiple times (concurrency bugs are often non-deterministic). If you suspect a race condition, add a `time.sleep(random.random())` call inside critical sections to increase the chance of hitting the race.
