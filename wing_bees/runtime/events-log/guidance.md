## Guidance

The log is your audit trail. It's also expensive to parse if it grows large; operators should occasionally prune old entries. The log format is stable, so custom parsing (e.g., cost tracking across teams) is feasible. If you need to associate human context with a feature (who started it, why, approval status), the feature branch's commits and PRs are the source of truth — the events log records what bees did, not why.
