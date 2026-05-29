<!-- structured-events.md: migrated from observability.md.

Hall: hall_pattern
-->

Emit structured JSONL events at every boundary. Never lose them to exceptions—wrap event-emission in a try-except that swallows exceptions. Bees' `emit_event` writes to `~/.bees/events.log` with schema `{ts, feature, stage, outcome, model, duration_ms, repo, ...}`; if emission fails, the pipeline continues (observability cannot break the pipeline). Query the log with `jq` or feed it to Grafana—it's the contract.
