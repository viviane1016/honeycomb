## Queen consultation at plan time

If `RELEASE_MAP.md` exists at the repo root, the queen reads it during planning to understand how the requested feature fits the upcoming release sequence — what is queued for the next release, what has been deferred, and what dependencies are in flight.

The queen may note in `## Context` that the feature naturally fits a specific milestone (e.g., "fits v1.2 Drone milestone alongside drone-sentinel"), but the operator's briefing remains authoritative. The release map informs context; it does not override the briefing.

If `RELEASE_MAP.md` is absent (older repo or pre-cartographer state), this step is skipped silently.
