<!-- retry-incremental-repair.md: migrated from retry-incremental-repair.md.

Hall: hall_procedure
-->

When a scribe fails parse or validation (`lib/spec.py:1144`), bees fires one retry (`max_attempts=2`, `lib/spec.py:1079`). The retry prompt contains the prior raw output verbatim plus the specific error plus a "fix only what the error flagged" directive. On second failure, `.raw.NNN.txt` is written to the specs dir and the process exits non-zero. See ADR-0022.
