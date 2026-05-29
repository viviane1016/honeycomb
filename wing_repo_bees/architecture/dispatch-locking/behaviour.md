## Behaviour

When `bees dispatch <slug>` runs, it attempts to acquire an exclusive lock on `.bees/<slug>/dispatch.lock` using `fcntl.flock()` with the `LOCK_EX | LOCK_NB` flags (exclusive, non-blocking). If the lock is held, the call fails immediately; the dispatcher does not queue or retry. If the lock is acquired, the dispatch proceeds. When the dispatch exits (success or failure), the lock is released.

The lock is per-feature, not global, so two dispatches on different features can run concurrently without contention. Within a single feature, the lock serializes the dispatch run end-to-end (plan parsing, wave construction, cell creation, builder launches, FF-merge) while permitting wave-internal parallelism: within each wave, builders run in parallel via `ThreadPoolExecutor(max_workers=parallelism)`, with a barrier between waves ensuring all builders commit and merge before the next wave starts.

What the lock prevents: two `bees dispatch` commands on the same feature racing to create cells, update the feature branch, or trigger merges. Wave-internal builders in different cells do not contend on the lock — they hold it collectively, release it together after all waves complete.
