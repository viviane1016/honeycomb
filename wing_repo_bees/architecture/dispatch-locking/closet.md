<!-- dispatch-locking.md: migrated from arch-locking.md.

Hall: hall_architecture
-->

A per-feature, non-blocking fcntl lock guards the entire dispatch run, from start to finish. The lock file lives in `.bees/<slug>/` and is acquired at dispatch start. If another dispatch on the same feature is running, the lock is held and the new dispatch fails immediately with a clear error. Inside the lock, wave-internal builders run in parallel under `--parallel N` / `BEES_DISPATCH_PARALLEL` (default 4).
