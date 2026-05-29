## Behaviour

Scout detects header staleness by comparing the `Scout:` timestamp in an existing header to the file's last commit time. Behaviour is:

- **Write when absent**: If a file has no scout header, scout writes one with the current UTC timestamp.
- **Skip when current**: If the header's timestamp ≥ the file's last commit time, the file is considered up-to-date; scout skips regeneration to avoid unnecessary churn.
- **Regenerate when stale**: If the header's timestamp < the file's last commit time, the file was modified after the header was written; scout regenerates the header with a fresh timestamp.
- **Force flag**: The `force` flag bypasses staleness checks and regenerates all headers regardless of timestamp.

Scout runs in batches of Haiku invocations — one model call per file that needs writing or regenerating — so the cost scales with the number of stale files, not the size of the codebase. Files that have not changed since their last scout run cost nothing.
