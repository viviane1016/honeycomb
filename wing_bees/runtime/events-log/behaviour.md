## Behaviour

`emit_event` is called at every stage boundary: start (outcome=started), success, failure, timeout. The function swallows all exceptions so a logging failure never breaks the pipeline. JSONL format makes the log append-only and line-delimited, so partial writes (e.g., mid-power-failure) are rare and don't corrupt earlier records.

Consumers of the events log:
- `bees status <slug>` — filters to the feature, shows recent events and stage summary.
- `bees dash` — reads the whole log, groups by repo, computes aggregate costs and success rates, and serves an HTTP dashboard at `127.0.0.1:7475` with live updates via Server-Sent Events.

The log is per-user (lives in `~/.bees/`), not per-repo, so one log accumulates events across all bees work. The `repo` field lets dashboards group by project. The `cwd` field is included only when it differs from `repo`.
